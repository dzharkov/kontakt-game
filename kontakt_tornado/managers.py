from models import User
from database import db

class NotificationManager(object):

    def __init__(self):
        self._rooms_connections = dict()

    def add_user_connection(self, connection):
        room_id = connection.room_id

        if not room_id in self._rooms_connections:
            self._rooms_connections[room_id] = dict()
        self._rooms_connections[room_id][connection.user_id] = connection

    def remove_user_connection(self, connection):
        del self._rooms_connections[connection.room_id][connection.user_id]

    def emit_for_user_in_room(self, user_id, room_id, event, *args, **kwargs):
        if room_id in self._rooms_connections and user_id in self._rooms_connections[room_id]:
            self._rooms_connections[room_id][user_id].emit(event, *args, **kwargs)

    def emit_for_room(self, room_id, event, *args, **kwargs):
        if not room_id in self._rooms_connections:
            return
        for user_id in self._rooms_connections[room_id].keys():
            self.emit_for_user_in_room(user_id, room_id, event, *args, **kwargs)


notification_manager = NotificationManager()

class UserManager(object):

    def __init__(self):
        self._users = dict()

    def get_user_by_id(self, id):
        id = int(id)
        if id in self._users:
            return  self._users[id]

        user = User()

        row = list(db.query("SELECT id, username as nickname, first_name, last_name FROM auth_user WHERE id = %s", id))[0]

        for k,v in row.iteritems():
            user.__setattr__(k, v)

        self._users[id] = user

        return user

user_manager = UserManager()