from django.utils import timezone

from app import settings

class Game(object):

    def __init__(self):
        self.master = None
        self.guessed_word = None
        self.guessed_letters = None

        self.contacts = None

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

    def has_active_accepted_contacts(self):
        return self.contacts.active_accepted().count() > 0

class Contact(object):

    def __init__(self, *args, **kwargs):
        self.game = None

        self.created_at = None

        self.author = None

        self.word = None
        self.description = None

        self.connected_user = None
        self.connected_word = None
        self.connected_at = None

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

    def accept(self, user, word):
        self.connected_at = timezone.now()
        self.connected_user = user
        self.connected_word = word
