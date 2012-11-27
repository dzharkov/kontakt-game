# -*- coding: utf-8 -*-
from tornado import httpserver, web, websocket, ioloop, gen
from tornadio2 import SocketConnection, TornadioRouter, SocketServer, event
import tornadio2.gen

class GameCatcher(SocketConnection):
    def __init__(self, *args, **kwargs):
        super(GameCatcher, self).__init__(*args, **kwargs)
        self.listen()

    def listen(self):
        pass

    @event('login')
    def on_login(self, session_id, room_id):
        self.emit('login_result', 1)

    @event('accept')
    def on_accept(self, contact_id, word):
        print word
        self.emit('accepting_result', contact_id, 1)

    @event('room_state_request')
    def on_room_state_request(self):
        result = dict()
        result['game'] = {'open_word_part' : u'м', 'word_length' : 11, 'state' : 'running' }
        result['users'] = [{'id' : i, 'name' : 'user ' + str(i), 'nickname' : 'user_' + str(i)} for i in range(1, 10)]


        result['contacts'] = [ { 'id' : i, 'user_id' : i+3, 'desc' : 'Description of word by user ' + str(i) } for i in range(1, 4)]

        self.emit('room_state_update', result)

    @tornadio2.gen.sync_engine
    def on_event(self, name, *args, **kwargs):
        """Wrapped ``on_event`` handler, which will queue events and will allow usage
        of the ``yield`` in the event handlers.

        If you want to use non-queued version, just wrap ``on_event`` with ``gen.engine``.
        """
        return super(GameCatcher, self).on_event(name, *args, **kwargs)

def start_server():
    router = TornadioRouter(GameCatcher)
    app = web.Application(router.urls, socket_io_port=8001)
    SocketServer(app)