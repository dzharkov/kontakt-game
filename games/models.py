from django.utils import timezone
from datetime import timedelta

from app import settings

GAME_STATE_NOT_STARTED = 'not_started'
GAME_STATE_MASTER_SELECTION = 'master_selection'
GAME_STATE_RUNNING = 'running'
GAME_STATE_COMPLETE = 'complete'

class Game(object):

    def __init__(self):
        self.room = None
        self.master = None
        self.guessed_word = None
        self.guessed_letters = None
        self.state = GAME_STATE_NOT_STARTED

        self._active_contacts = dict()
        self._master_contenders = dict()

        self._user_words = set()

        self._select_master_at = None

        self.last_successful_contact = None
        self.last_accepted_contact = None

    def add_active_contact(self, contact):
        self._active_contacts[contact.id] = contact

    def add_used_word(self, word):
        self._user_words.add(word)

    def is_word_used(self, word):
        return word in self._user_words

    def start_master_selection_process(self):
        now = timezone.now()
        self._select_master_at = now + timedelta(seconds=settings.MASTER_SELECTION_TIMEOUT)
        self.state = GAME_STATE_MASTER_SELECTION
        self._master_contenders = dict()

    def terminate_master_selection_process(self):
        self._select_master_at = None
        self.state = GAME_STATE_NOT_STARTED
        self._master_contenders = dict()

    def is_user_already_master_contender(self, user):
        return user.id in self._master_contenders

    def add_master_contender(self, user, proposed_word):
        self._master_contenders[user.id] = (user, proposed_word)

    @property
    def master_contenders_applications(self):
        return self._master_contenders.values()

    @property
    def seconds_left_before_master_selection(self):
        if not self._select_master_at:
            return 0
        return max(0, (self._select_master_at - timezone.now()).seconds)

    @property
    def select_master_at(self):
        if not self._select_master_at:
            return 0
        return self._select_master_at

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

    @property
    def master_contenders(self):
        return map(lambda x: x[0], self._master_contenders.values())

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
    def has_active_accepted_contact(self):
        return self.last_accepted_contact and self.last_accepted_contact.is_active

    def end(self):
        self.guessed_letters = len(self.guessed_word)
        self.remove_active_contacts()
        self.state = GAME_STATE_COMPLETE

    @property
    def is_running(self):
        return self.state == GAME_STATE_RUNNING

    @property
    def is_complete(self):
        return self.state == GAME_STATE_COMPLETE

    @property
    def is_master_selecting(self):
        return self.state == GAME_STATE_MASTER_SELECTION

    @property
    def is_not_started(self):
        return self.state == GAME_STATE_NOT_STARTED

    @property
    def is_active(self):
        return self.is_running or self.is_master_selecting

    def show_next_letter(self):
        self.guessed_letters+=1

    @property
    def last_visible_letter(self):
        return self.guessed_word[self.guessed_letters-1]

    @property
    def json_representation(self):

        if self.is_running or self.is_complete:
            result = {
                'available_word_part' : self.available_word_part(),
                'word_length' : len(self.guessed_word),
                'state' : self.state,
                'contacts' : [contact.json_representation for contact in self._active_contacts.values()]
            }
            if self.is_running:
                result['master_id'] = self.master.id
        else:
            result = {
                'state' : self.state
            }

        if self.is_master_selecting:
            result['master_contenders'] = map(lambda x: { 'user_id' : x.id } , self.master_contenders)

        if self.last_accepted_contact:
            result['accepted_contact'] = {
                'id':self.last_accepted_contact.id,
                'seconds_left':self.last_accepted_contact.seconds_left
            }

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
        self.is_canceled = False
        self.is_successful = False

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
