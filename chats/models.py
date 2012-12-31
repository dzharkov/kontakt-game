from django.utils import timezone

class ChatMessage(object):
    def __init__(self):
        self.author = None
        self.created_at = timezone.now()
        self.room_id = None
        self.text = None

    @property
    def json_representation(self):
        return {
            'author_id' : self.author.id,
            'time' : self.created_at.strftime("%I:%M"),
            'text' : self.text
        }

