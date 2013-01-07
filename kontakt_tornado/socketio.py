# -*- coding: utf-8 -*-
import functools
import tornado.database
import tornado.web
import tornado.ioloop
from tornadio2 import SocketConnection, TornadioRouter, SocketServer, event
import tornadio2.gen

from database import redis_connection, db_modifier
from managers import user_manager, connection_manager
from chats.managers import chat_manager
from games.managers import game_manager
from games.exceptions import GameError

def emit_game_errors(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except GameError as e:
            self.emit('game_error', e.message)
    return wrapper

class GameCatcher(SocketConnection):
    def __init__(self, *args, **kwargs):
        super(GameCatcher, self).__init__(*args, **kwargs)
        self.listen()
        self.room_id = None
        self.user_id = None
        self.user = None

    def listen(self):
        connection_manager.add_connection(self)
    
    @property
    def current_room_game(self):
        return game_manager.get_game_in_room(self.room_id)

    @event('login')
    def on_login(self, session_id, room_id):
        room_id = int(room_id)
        self.room_id = room_id
        user_id = redis_connection.hget('room:' + str(room_id), session_id)
        self.process_login(user_id)

    def process_login(self, user_id):
        if not user_id:
            self.emit('login_result', { 'result' : 0 })
        else:
            db_modifier.execute("UPDATE rooms_room SET online_amount = online_amount + 1 WHERE id = %s", self.room_id)

            self.user_id = int(user_id)

            user = user_manager.get_user_by_id(user_id)

            self.user = user

            connection_manager.add_user_room_connection(self)

            self.emit('login_result', { 'result' : 1, 'user_id' : self.user_id })
            self.on_room_state_request()

            self.emit_for_room('joined_user', user.json_representation)

    @event('contact_accept')
    @emit_game_errors
    def on_contact_accept(self, contact_id, word):
        game_manager.accept_contact(self.user, self.current_room_game, int(contact_id), word)

    @event('contact_break')
    @emit_game_errors
    def on_contact_break(self, contact_id, word):
        game_manager.break_contact(self.user, self.current_room_game, int(contact_id), word)

    @event('contact_cancel')
    @emit_game_errors
    def on_contact_cancel(self, contact_id):
        game_manager.cancel_contact(self.user, self.current_room_game, int(contact_id))

    @event('contact_create')
    @emit_game_errors
    def on_contact_create(self, word, description):
        game_manager.create_contact(self.user, self.current_room_game, word, description)

    @event('game_start')
    @emit_game_errors
    def on_game_start(self):
        game_manager.start_game(self.user, self.room_id)

    @event('game_word_propose')
    @emit_game_errors
    def on_game_word_proposed(self, word):
        game_manager.add_master_contender(self.current_room_game, self.user, word)

    @event('room_state_request')
    def on_room_state_request(self):
        result = dict()
        game = self.current_room_game
        result['game'] = game.json_representation
        all_users = set(connection_manager.online_users_in_room(self.room_id))

        for contact in game.active_contacts:
            all_users.add(contact.author)
            if contact.connected_user:
                all_users.add(contact.connected_user)

        if game.master:
            all_users.add(game.master)

        result['chat_messages'] = map(lambda x: x.json_representation, chat_manager.last_messages_in_room(self.room_id))

        result['users'] = [user.json_representation for user in all_users]

        self.emit('room_state_update', result)

    @event('chat_message_send')
    def on_chat_message_send(self, text):
        chat_manager.new_message(self.room_id, self.user, text)

    def emit_for_room(self, event, *args, **kwargs):
        connection_manager.emit_for_room(self.room_id, event, *args, **kwargs)

    def on_close(self):
        if self.user:
            self.emit_for_room('user_quit', { 'user_id' : self.user_id })

        db_modifier.execute("UPDATE rooms_room SET online_amount = online_amount - 1 WHERE id = %s", self.room_id)

        connection_manager.remove_connection(self)

    @tornadio2.gen.sync_engine
    def on_event(self, name, *args, **kwargs):
        """Wrapped ``on_event`` handler, which will queue events and will allow usage
        of the ``yield`` in the event handlers.

        If you want to use non-queued version, just wrap ``on_event`` with ``gen.engine``.
        """
        return super(GameCatcher, self).on_event(name, *args, **kwargs)


import re
def web_channel_handler(msg):
    if msg.kind == 'message':
        if msg.body == 'reload_games':
            game_manager.load_active_games()
            connection_manager.emit_broadcast('reload')
            return

        m = re.match('room_deleted\:(\d+)', msg.body)
        if m:
            connection_manager.room_became_deleted(int(m.group(1)))

        m = re.match('room_private\:(\d+)', msg.body)
        if m:
            connection_manager.room_became_private(int(m.group(1)))

        m = re.match('kick_user_from_room\:(\d+)\:(\d+)', msg.body)
        if m:
            connection_manager.remove_user_from_room(int(m.group(1)), int(m.group(2)))

def start_server():
    from app import settings
    game_manager.load_valid_words_from_file(settings.VALID_WORDS_FILENAME)
    game_manager.load_active_games()

    router = TornadioRouter(GameCatcher)
    app = tornado.web.Application(router.urls, socket_io_port=8001)

    from database import redis_subscriptions

    db_modifier.execute("UPDATE rooms_room SET online_amount = 0")

    tornado.ioloop.IOLoop.instance().add_callback(
        lambda: redis_subscriptions.subscribe('web_channel', lambda x: redis_subscriptions.listen(web_channel_handler))
    )

    #tornado.ioloop.IOLoop.instance().add_callback(
    #    lambda: redis_subscriptions.subscribe('room_close', lambda x: redis_subscriptions.listen(room_close))
    #)

    SocketServer(app)