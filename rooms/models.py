
class Room(object):

    def __init__(self):
        self._users = dict()

    def add_user(self, user):
        self._users[user.id] = user

    def remove_user(self, user):
        del self._users[user.id]

    @property
    def users(self):
        return self._users.values()