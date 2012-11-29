# -*- coding: utf-8 -*-
import tornado.database
import tornado.web
from tornadio2 import SocketConnection, TornadioRouter, SocketServer, event
import tornadio2.gen

from database import redis
from managers import user_manager, notification_manager
from games.managers import game_manager
from rooms.managers import room_manager

class GameCatcher(SocketConnection):
    def __init__(self, *args, **kwargs):
        super(GameCatcher, self).__init__(*args, **kwargs)
        self.listen()
        self.room_id = None
        self.user_id = None
        self.user = None
        self.game = None

    def listen(self):
        pass

    @event('login')
    def on_login(self, session_id, room_id):
        self.room_id = room_id
        redis.hget('room:' + str(room_id), session_id, callback=self.process_login)

    def process_login(self, user_id):
        if not user_id:
            self.emit('login_result', 0)
        else:
            self.user_id = user_id

            user = user_manager.get_user_by_id(user_id)
            user.is_online = True

            self.user = user

            self.room = room_manager.get_room_by_id(self.room_id)
            self.room.add_user(user)

            self.game = game_manager.get_game_in_room(self.room_id)

            self.emit_for_room('joined_user', user.json_representation)

            notification_manager.add_user_connection(self)

            self.emit('login_result', 1)
            self.on_room_state_request()

    @event('accept')
    def on_accept(self, contact_id, word):
        print word
        self.emit('accepting_result', contact_id, 1)

    @event('room_state_request')
    def on_room_state_request(self):
        result = dict()
        result['game'] = self.game.json_representation

        all_users = set(self.room.users)

        for contact in self.game.active_contacts:
            all_users.add(contact.author)
            if contact.connected_user:
                all_users.add(contact.connected_user)

        all_users.add(self.game.master)

        print all_users,user_manager._users

        result['users'] = [user.json_representation for user in all_users]

        self.emit('room_state_update', result)

    def emit_for_room(self, event, *args, **kwargs):
        notification_manager.emit_for_room(self.room_id, event, *args, **kwargs)

    def on_close(self):
        self.user.is_online = False
        self.room.remove_user(self.user)
        notification_manager.remove_user_connection(self)
        self.emit_for_room('user_quit', self.user_id)

    @tornadio2.gen.sync_engine
    def on_event(self, name, *args, **kwargs):
        """Wrapped ``on_event`` handler, which will queue events and will allow usage
        of the ``yield`` in the event handlers.

        If you want to use non-queued version, just wrap ``on_event`` with ``gen.engine``.
        """
        return super(GameCatcher, self).on_event(name, *args, **kwargs)

def start_server():
    game_manager.load_active_games()

    router = TornadioRouter(GameCatcher)
    app = tornado.web.Application(router.urls, socket_io_port=8001)
    SocketServer(app)