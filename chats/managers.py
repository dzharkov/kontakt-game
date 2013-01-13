from collections import deque
from models import ChatMessage
from kontakt_tornado.managers import connection_manager

RECENT_MESSAGES_AMOUNT = 50

class ChatManager(object):
    def __init__(self):
        self._recent_messages_in_room = dict()

    def clear(self):
        self._recent_messages_in_room = dict()

    def new_message(self, room_id, author, text):
        msg = ChatMessage()
        msg.author = author
        msg.room_id = room_id
        msg.text = text

        if not room_id in self._recent_messages_in_room:
            self._recent_messages_in_room[room_id] = deque()

        if len(self._recent_messages_in_room[room_id]) >= RECENT_MESSAGES_AMOUNT:
            self._recent_messages_in_room[room_id].popleft()

        self._recent_messages_in_room[room_id].append(msg)

        connection_manager.emit_for_room(room_id, 'chat_message', msg=msg.json_representation)

    def last_messages_in_room(self, room_id):
        try:
            return self._recent_messages_in_room[room_id]
        except KeyError:
            return []

chat_manager = ChatManager()