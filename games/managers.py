# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone
from models import *
from exceptions import GameError
import random

from app import settings

class ContactManager(object):
    @staticmethod
    def create_dummy_contacts_for_game():
        from django.db import connection, transaction

        cursor = connection.cursor()
        transaction.enter_transaction_management(True)
        try:
            cursor.execute("SET foreign_key_checks = 0")
            cursor.execute("TRUNCATE games_contact")
            cursor.execute("TRUNCATE games_game")
            cursor.execute("TRUNCATE rooms_room")
            cursor.execute("SET foreign_key_checks = 1")

            cursor.execute(u"INSERT INTO `rooms_room` VALUES (1,'Любители моделей', 2)")
            cursor.execute(u"INSERT INTO `rooms_room` VALUES (2,'Экзистенциальная Россия', 2)")

            cursor.execute(u"INSERT INTO `games_game` VALUES (1,2,'моделирование',2,1,'running')")
            cursor.execute(u"INSERT INTO `games_game` VALUES (2,2,'прустота',8,2,'complete')")
            cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL,1,0),(2,1,'2012-11-22 17:09:04',4,'моделирование','Оно бывает имитационным, эволюционным, и изредка даже психологическим',NULL,NULL,NULL,1,0)")
        except Exception:
            transaction.rollback()
            return
        transaction.commit()

    @staticmethod
    def get_earliest_time_of_active_contacts():
        now = timezone.now()
        return now - timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)


from kontakt_tornado.database import db
from kontakt_tornado.managers import connection_manager, user_manager
from utils import exec_once
import heapq
import tornado.ioloop

GAME_TABLE_NAME = 'games_game'
CONTACT_TABLE_NAME = 'games_contact'

class GameManager(object):

    def __init__(self):
        self.active_contacts = dict()
        self.timeout_callbacks = []

    def load_active_games(self):
        self.current_game_in_room = dict()
        self.last_complete_game_in_room = dict()
        self.active_contacts = dict()
        self.timeout_callbacks = []
        for row in db.query("SELECT * FROM %s" % GAME_TABLE_NAME):
            self.add_game_from_db_row(row)

        self.check_callbacks()

    def add_game_from_db_row(self, row):
        game = Game()
        for field, value in row.iteritems():
            game.__setattr__(field, value)

        if game.master_id:
            game.master = user_manager.get_user_by_id(game.master_id)

        for contact_row in db.query("SELECT * FROM " + CONTACT_TABLE_NAME + " WHERE game_id = %s AND is_active=1", game.id):
            contact = self.add_contact_from_db_row(contact_row)
            game.add_active_contact(contact)
            contact.game = game
            if contact.is_accepted and (not game.last_accepted_contact or game.last_accepted_contact.connected_at <= contact.connected_at):
                game.last_accepted_contact = contact

            if contact.is_accepted:
                self.create_contact_check_task(contact)

        for word_row in db.query("SELECT word FROM " + CONTACT_TABLE_NAME + " WHERE game_id = %s AND is_active=0", game.id):
            game.add_used_word(word_row.word)

        self.current_game_in_room[game.room_id] = game

        return game

    def check_callbacks(self):
        now = timezone.now()
        while self.timeout_callbacks and self.timeout_callbacks[0][0] < now:
            timeout = heapq.heappop(self.timeout_callbacks)
            timeout[1]()

    def add_timeout_callback(self, start_at, callback):
        once_exec_callback = exec_once(callback)
        now = timezone.now()
        delta = max(start_at, now) - now
        tornado.ioloop.IOLoop.instance().add_timeout(delta, once_exec_callback)
        heapq.heappush(self.timeout_callbacks, (start_at, once_exec_callback))

    def create_contact_check_task(self, contact):
        self.add_timeout_callback(contact.check_at, lambda: self.check_accepted_contact(contact))

    def add_contact_from_db_row(self, row):
        contact = Contact()
        for field, value in row.iteritems():
            contact.__setattr__(field, value)

        contact.author = user_manager.get_user_by_id(contact.author_id)

        if contact.connected_user_id:
            contact.connected_user = user_manager.get_user_by_id(contact.connected_user_id)

        self.active_contacts[contact.id] = contact
        return contact

    def get_game_in_room(self, room_id):
        return self.current_game_in_room[room_id]

    def find_active_contact(self, id, game):
        try:
            result = self.active_contacts[id]
        except KeyError:
            raise GameError(u'Контакт не найден')

        if result.game != game:
            raise GameError(u'Контакт не принадлежит игре')
        return result

    def persist_entity(self, obj, table_name, columns):
        args_values=map(lambda x: obj.__getattribute__(x), columns)
        set_string = " SET " + ( ", ".join( map(lambda x: x + '=%s', columns) ) )
        if hasattr(obj, 'id'):
            args_values.append(obj.id)
            db.execute("UPDATE " + table_name + set_string +" WHERE id = %s", *args_values)
        else:
            obj.id = db.execute_lastrowid("INSERT INTO " + table_name + set_string, *args_values)

    def persist_game(self, game):
        if game.master:
            game.master_id = game.master.id
        else:
            game.master_id = None

        columns = ('room_id', 'master_id', 'guessed_word', 'guessed_letters', 'state')

        self.persist_entity(game, GAME_TABLE_NAME, columns)

    def persist_contact(self, contact):
        if not contact.is_active:
            contact.game.add_used_word(contact.word)

        if contact.is_accepted:
            contact.connected_user_id = contact.connected_user.id
        else:
            contact.connected_user_id = None

        contact.author_id = contact.author.id
        contact.game_id = contact.game.id

        columns = ('game_id', 'word', 'description', 'author_id', 'connected_user_id', 'connected_word', 'connected_at', 'is_active', 'is_successful', 'created_at')

        self.persist_entity(contact, CONTACT_TABLE_NAME, columns)

    def check_accepted_contact(self, contact):
        if not contact.is_accepted:
            raise Exception(u'trying to check unaccepted contact')
        if not contact.is_active:
            return
        if contact.check_at > timezone.now():
            raise Exception(u'it\'s too early')

        game = contact.game

        if contact.is_connected_word_right():
            contact.is_successful = True
            for c in game.active_contacts:
                self.remove_contact(c)
            game.remove_active_contacts()
            connection_manager.emit_for_room(game.room_id, 'successful_contact_connection', contact_id=contact.id, word=contact.word)
            if contact.game_word_guessed() or game.guessed_letters+1 == game:
                game.end()
                connection_manager.emit_for_room(game.room_id, 'game_complete', word=game.guessed_word, is_word_guessed=contact.game_word_guessed())
            else:
                game.show_next_letter()
                connection_manager.emit_for_room(game.room_id, 'next_letter_opened', letter=game.last_visible_letter)
            self.persist_game(game)
        else:
            contact.is_active = False
            connection_manager.emit_for_room(game.room_id, 'unsuccessful_contact_connection', { 'contact_id' : contact.id })
            self.remove_contact(contact)

        self.persist_contact(contact)

    def accept_contact(self, user, game, contact_id, word):
        self.check_callbacks()
        if game.has_active_accepted_contact:
            raise GameError(u'В игре уже есть принятый контакт')

        contact = self.find_active_contact(contact_id, game)

        if user == game.master:
            raise GameError(u'Ведущий не должен принимать контакт')
        if user == contact.author:
            raise GameError(u'Автор контакта не может его принимать')
        if contact.is_accepted:
            raise GameError(u'Контакт уже принят')
        if contact.is_canceled:
            raise GameError(u'Контакт был отменен')

        if not contact.can_be_connected_word(word):
            raise GameError(u'Вы выбрали явно неподходящее слово')

        contact.accept(user, word)

        self.persist_contact(contact)
        self.persist_game(game)

        self.create_contact_check_task(contact)

        connection_manager.emit_for_room(game.room_id, 'accepted_contact', contact_id=contact_id, user_id=user.id, seconds_left=contact.seconds_left)

    def remove_contact(self, contact):
        del self.active_contacts[contact.id]
        contact.is_active = False
        contact.game.remove_active_contact(contact)
        self.persist_contact(contact)

    def cancel_contact(self, user, game, contact_id):
        contact = self.find_active_contact(contact_id, game)

        if user != contact.author:
            raise GameError(u'Вы не автор контакта')

        if not contact.is_active:
            raise GameError(u'Контакт уже неактивен')

        if contact.is_accepted:
            raise GameError(u'Контакт уже принят')

        self.remove_contact(contact)

        connection_manager.emit_for_room(game.room_id, 'contact_canceled', contact_id=contact_id)

    def break_contact(self, user, game, contact_id, word):
        self.check_callbacks()
        contact = self.find_active_contact(contact_id, game)
        if user != game.master:
            raise GameError(u'Только ведущий может обрывать контакт')
        if not contact.is_active:
            raise GameError(u'Контакт уже не активен')

        if word == game.guessed_word:
            raise GameError(u'Нельзя пытаться разорвать контакт загаданным вами словом')

        if contact.is_right_word(word):
            contact.get_broken()
            self.persist_contact(contact)
            self.remove_contact(contact)
            connection_manager.emit_for_room(game.room_id, 'broken_contact', contact_id=contact_id, user_id=user.id)
        else:
            connection_manager.emit_for_user_in_room(user.id, game.room_id, 'unsuccessful_contact_breaking', { 'contact_id' : contact_id })

    def create_contact(self, user, game, contact_word, description):
        self.check_callbacks()

        if not game.is_running:
            raise GameError(u'Игра не запущена')

        if game.master == user:
            raise GameError(u'Ведущий не может создавать контакты')

        if len(filter(lambda x: x.author == user, game.active_contacts)) > 0:
            raise GameError(u'В игре уже есть ваш контакт')

        if game.is_word_used(contact_word):
            raise GameError(u'Контакт с таким словом уже был')

        if not game.can_be_contact_word(contact_word):
            raise GameError(u'Контакт с таким словом не может быть создан')

        if len(description) == 0:
            raise GameError(u'Нельзя создать контакт с пустым описанием')

        contact = Contact()
        contact.author = user
        contact.created_at = timezone.now()
        contact.word = contact_word
        contact.description = description

        contact.game = game
        self.persist_contact(contact)

        game.add_active_contact(contact)

        self.active_contacts[contact.id] = contact

        connection_manager.emit_for_room(game.room_id, 'contact_creation', contact=contact.json_representation)

        return

    def choose_master(self, game):
        room_id = game.room_id

        contenders = game.master_contenders

        game.terminate_master_selection_process()

        if len(contenders) < 1:
            if room_id in self.last_complete_game_in_room:
                self.current_game_in_room[room_id] = self.last_complete_game_in_room[room_id]

            connection_manager.emit_for_room(room_id, 'master_selection_unsuccessful', {})
        else:
            (master, word)  = contenders[random.randint(0, len(contenders)-1)]

            game.master = master
            game.guessed_word = word
            game.guessed_letters = 1
            game.state = GAME_STATE_RUNNING

            self.persist_game(game)

            connection_manager.emit_for_room(room_id, 'game_running', game=game.json_representation)


    def add_master_contender(self, game, user, word):
        if not game.is_master_selecting:
            raise GameError(u'Сейчас не время выбора ведущего')
        if len(word) < 5:
            raise GameError(u'Слишком короткое слово')
        if game.is_user_already_master_contender(user):
            raise GameError(u'Вы уже предложили свое слово')

        game.add_master_contender(user, word)
        connection_manager.emit_for_user_in_room(user.id, game.room_id, 'game_word_accepted', word=word)
        connection_manager.emit_for_room(game.room_id, 'master_contender', user_id=user.id)

    def start_game(self, user, room_id):
        current_game = self.get_game_in_room(room_id)

        if current_game.is_active:
            raise GameError(u'Игра уже запущена')

        if current_game.is_complete:
            self.last_complete_game_in_room[room_id] = current_game
            current_game = Game()
            current_game.room_id = room_id
            self.current_game_in_room[room_id] = current_game

        current_game.start_master_selection_process()

        self.add_timeout_callback(current_game.select_master_at, lambda: self.choose_master(current_game))

        connection_manager.emit_for_room(room_id, 'master_selection_started', seconds_left=current_game.seconds_left_before_master_selection, user_id=user.id)

game_manager = GameManager()
