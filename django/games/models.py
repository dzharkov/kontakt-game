from django.db import models
from django.contrib.auth.models import User
from managers import *

def create_word_field(*args, **kwargs):
    kwargs['max_length']=30
    return models.CharField(*args, **kwargs)

class Game(models.Model):

    objects = GameManager()

    master = models.ForeignKey(User)
    guessed_word = create_word_field()
    guessed_letters = models.PositiveSmallIntegerField()

class Contact(models.Model):

    objects = ContactManager()

    game = models.ForeignKey(Game)

    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(User, related_name="all_contacts")

    word = create_word_field()
    description = models.CharField(max_length=140)

    connected_user = models.ForeignKey(User, null=True)
    connected_word = create_word_field(null=True)
    connected_at = models.DateTimeField(null=True)

    def is_canceled(self):
        return False


