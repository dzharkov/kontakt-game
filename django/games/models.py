from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from app import settings

from managers import *

def create_word_field(*args, **kwargs):
    kwargs['max_length']=30
    return models.CharField(*args, **kwargs)

class Game(models.Model):

    objects = GameManager()

    master = models.ForeignKey(User)
    guessed_word = create_word_field()
    guessed_letters = models.PositiveSmallIntegerField()

    def letters_left(self):
        return len(self.guessed_word) - self.guessed_letters

    def available_word_part(self):
        return self.guessed_word[:self.guessed_letters]

    def available_word_part_with_asterisks(self):
        return self.available_word_part() + ("*" * self.letters_left())

    def can_be_contact_word(self, word):
        if len(word) < self.guessed_letters + 1:
            return False
        return self.available_word_part() == word[:self.guessed_letters]

class Contact(models.Model):

    objects = ContactManager()

    game = models.ForeignKey(Game, related_name="contacts")

    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(User, related_name="all_contacts")

    word = create_word_field()
    description = models.CharField(max_length=140)

    connected_user = models.ForeignKey(User, null=True)
    connected_word = create_word_field(null=True)
    connected_at = models.DateTimeField(null=True)

    def is_canceled(self):
        return False

    def is_accepted(self):
        return self.connected_at != None

    def is_active(self):
        return not self.is_accepted() or self.seconds_left() > 0

    def accepted_seconds_ago(self):
        return (timezone.now()-self.connected_at.replace(tzinfo=None)).seconds

    def seconds_left(self):
        return max(0, settings.CONTACT_CHECKING_TIMEOUT  - self.accepted_seconds_ago())

    def can_be_connected_word(self, word):
        return self.game.can_be_contact_word(word)
