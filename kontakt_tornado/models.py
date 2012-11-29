
class User(object):
    def __init__(self):
        self.id = None
        self.nickname = None
        self.first_name = None
        self.last_name = None
        self.is_online = False

    @property
    def json_representation(self):
        return {
            'id' : self.id,
            'name' : self.first_name + ' ' + self.last_name,
            'nickname' : self.nickname,
            'is_online' : self.is_online
        }
