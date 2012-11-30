from django.utils import timezone
from datetime import timedelta

from app import settings

class Game(object):

    def __init__(self):
        self.room = None
        self.master = None
        self.guessed_word = None
        self.guessed_letters = None

        self.state = None

        self._active_contacts = dict()

        self.valid_until = None
        self.last_successful_contact = None
        self.last_accepted_contact = None
        self.is_active = True

    def add_active_contact(self, contact):
        self._active_contacts[contact.id] = contact

    @property
    def active_contacts(self):
        return self._active_contacts.values()

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
        return self._active_contacts.active_accepted().count() > 0

    @property
    def is_valid(self):
        return not self.valid_until or self.valid_until > timezone.now()

    @property
    def has_active_accepted_contact(self):
        return self.last_accepted_contact and self.last_accepted_contact.is_active

    @property
    def json_representation(self):
        return {
            'id' : self.id,
            'master_id' : self.master.id,
            'available_word_part' : self.available_word_part(),
            'word_length' : len(self.guessed_word),
            'state' : self.state,
            'contacts' : [contact.json_representation for contact in self._active_contacts.values()]
        }

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
        self.valid_until = None

        self.is_active = True
        self.is_successful = False

    @property
    def is_canceled(self):
        return False

    @property
    def is_accepted(self):
        return self.connected_at != None

    def check_is_active(self):
        return not self.is_accepted or self.seconds_left() > 0

    def accepted_seconds_ago(self):
        return (timezone.now()-self.connected_at.replace(tzinfo=None)).seconds

    @property
    def seconds_left(self):
        return max(0, settings.CONTACT_CHECKING_TIMEOUT  - self.accepted_seconds_ago())

    def can_be_connected_word(self, word):
        return self.game.can_be_contact_word(word)

    def accept(self, user, word):
        nowtime = timezone.now()
        self.connected_at =  nowtime
        self.connected_user = user
        self.connected_word = word

        valid_until = nowtime + timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)
        self.valid_until = valid_until
        self.game.valid_until = valid_until
        self.game.last_accepted_contact = self


    @property
    def json_representation(self):
        result = {
            'id' : self.id,
            'author_id' : self.author.id,
            'desc' : self.description,
        }

        if self.connected_user:
            result['connection'] = {
                'user_id' : self.connected_user.id,
                'seconds_left' : self.seconds_left
            }

        return result
