from models import User
from database import db

class ConnectionManager(object):

    def __init__(self):
        self._rooms_connections = dict()
        self._users_in_rooms = dict()
        self._all_connections = dict()

    def add_user_room_connection(self, connection):
        room_id = connection.room_id
        user = connection.user
        if not room_id in self._rooms_connections:
            self._rooms_connections[room_id] = dict()
            self._users_in_rooms[room_id] = dict()

        if user.id in self._rooms_connections[room_id]:
            self._rooms_connections[room_id][user.id].close()

        user.is_online = True

        self._rooms_connections[room_id][user.id] = connection
        self._users_in_rooms[room_id][user.id] = user

    def add_connection(self, connection):
        self._all_connections[connection.__hash__()] = connection

    def remove_connection(self, connection):
        del self._all_connections[connection.__hash__()]
        if connection.user and connection == self._rooms_connections[connection.room_id][connection.user.id]:
            connection.user_id = False
            del self._rooms_connections[connection.room_id][connection.user.id]
            del self._users_in_rooms[connection.room_id][connection.user.id]

    def emit_for_user_in_room(self, _user_id, room_id, event, *args, **kwargs):
        if room_id in self._rooms_connections and _user_id in self._rooms_connections[room_id]:
            self._rooms_connections[room_id][_user_id].emit(event, *args, **kwargs)

    def emit_for_room(self, room_id, event, *args, **kwargs):
        if not room_id in self._rooms_connections:
            return
        for user_id in self._rooms_connections[room_id].keys():
            self.emit_for_user_in_room(user_id, room_id, event, *args, **kwargs)

    def emit_broadcast(self, event, *args, **kwargs):
        for conn in self._all_connections.values():
            conn.emit(event, *args, **kwargs)

    def online_users_in_room(self, room_id):
        return self._users_in_rooms[room_id].values()


connection_manager = ConnectionManager()

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