
class Room(object):

    def __init__(self):
        self._users = dict()

    def add_user(self, user):
        self._users[user.id] = user

    def remove_user(self, user):
        try:
            del self._users[user.id]
        except KeyError:
            pass

    @property
    def users(self):
        return self._users.values()