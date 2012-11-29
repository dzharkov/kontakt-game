from models import Room

class RoomManager(object):

    def __init__(self):
        self._rooms = dict()
        self.create_default_room()

    def create_default_room(self):
        room = Room()
        room.id = 1
        self.add_room(room)

    def add_room(self, room):
        self._rooms[room.id] = room

    def get_room_by_id(self, room_id):
        return self._rooms[room_id]

    def add_user_to_room(self, user, room_id):
        self._rooms[room_id].add_user(user)

room_manager = RoomManager()
