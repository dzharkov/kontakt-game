from django.utils import timezone
from datetime import timedelta

from app import settings

class Game(object):

    def __init__(self):
        self.room = None
        self.master = None
        self.guessed_word = None
        self.guessed_letters = None

        self._active_contacts = dict()

        self.last_successful_contact = None
        self.last_accepted_contact = None
        self.is_active = True

    def add_active_contact(self, contact):
        self._active_contacts[contact.id] = contact

    def remove_active_contact(self, contact):
        if contact == self.last_accepted_contact:
            self.last_accepted_contact = None
        if contact == self.last_successful_contact:
            self.last_successful_contact = None
        del self._active_contacts[contact.id]

    def remove_active_contacts(self):
        self.last_successful_contact = None
        self.last_successful_contact = None
        self._active_contacts = dict()

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
    def state(self):
        return 'running' if self.guessed_letters < len(self.guessed_word) else 'complete'

    @property
    def has_active_accepted_contact(self):
        return self.last_accepted_contact and self.last_accepted_contact.is_active

    def end(self):
        self.guessed_letters = len(self.guessed_word)
        self.remove_active_contacts()
        self.is_active = False

    def show_next_letter(self):
        self.guessed_letters+=1

    @property
    def last_visible_letter(self):
        return self.guessed_word[self.guessed_letters-1]

    @property
    def json_representation(self):
        result = {
            'id' : self.id,
            'master_id' : self.master.id,
            'available_word_part' : self.available_word_part(),
            'word_length' : len(self.guessed_word),
            'state' : self.state,
            'contacts' : [contact.json_representation for contact in self._active_contacts.values()]
        }

        if self.last_accepted_contact:
            result['accepted_contact'] = self.last_accepted_contact.id

        return result

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

    def is_right_word(self, word):
        return self.word.lower() == word.lower()

    def game_word_guessed(self):
        return self.is_right_word(self.game.guessed_word)

    def get_broken(self):
        self.is_active = False

    @property
    def check_at(self):
        return self.connected_at + timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)

    def accept(self, user, word):
        nowtime = timezone.now()
        self.connected_at =  nowtime
        self.connected_user = user
        self.connected_word = word

        self.game.last_accepted_contact = self

    def is_connected_word_right(self):
        return self.is_accepted and self.is_right_word(self.connected_word)

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
