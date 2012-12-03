# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone
from models import *
from exceptions import GameError

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
            cursor.execute("SET foreign_key_checks = 1")
            cursor.execute(u"INSERT INTO `games_game` VALUES (1,2,'моделирование',2,NULL,1)")
            cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL,NULL,1,0),(2,1,'2012-11-22 17:09:04',4,'модуль','кусок чего-либо',NULL,NULL,NULL,NULL,1,0)")
        except Exception:
            transaction.rollback()
            return
        transaction.commit()

    @staticmethod
    def get_earliest_time_of_active_contacts():
        now = timezone.now()
        return now - timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)


from kontakt_tornado.database import db
from kontakt_tornado.managers import notification_manager, user_manager
from utils import exec_once
import heapq
import tornado.ioloop

GAME_TABLE_NAME = 'games_game'
CONTACT_TABLE_NAME = 'games_contact'

class GameManager(object):

    def __init__(self):
        self.active_games = dict()
        self.active_contacts = dict()
        self.timeout_callbacks = []

    def load_active_games(self):
        self.active_games = dict()
        self.active_contacts = dict()
        self.timeout_callbacks = []
        for row in db.query("SELECT * FROM %s" % GAME_TABLE_NAME):
            self.add_game_from_db_row(row)

        self.check_callbacks()

    def add_game_from_db_row(self, row):
        game = Game()
        for field, value in row.iteritems():
            game.__setattr__(field, value)

        game.master = user_manager.get_user_by_id(game.master_id)

        for contact_row in db.query("SELECT * FROM " + CONTACT_TABLE_NAME + " WHERE game_id = %s AND is_active=1", game.id):
            contact = self.add_contact_from_db_row(contact_row)
            game.add_active_contact(contact)
            contact.game = game
            if contact.is_accepted and (not game.last_accepted_contact or game.last_accepted_contact.connected_at <= contact.connected_at):
                game.last_accepted_contact = contact

            if contact.is_accepted:
                self.create_contact_check_task(contact)

        game.room_id = 1

        self.active_games[game.id] = game
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
        return self.active_games.values()[0]

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
        args_values.append(obj.id)
        db.execute("UPDATE " + table_name + " SET " + ( ", ".join( map(lambda x: x + '=%s', columns) ) ) +" WHERE id = %s", *args_values)

    def persist_game(self, game):
        game.master_id = game.master.id

        columns = ('master_id', 'guessed_word', 'guessed_letters', 'valid_until', 'is_active')

        self.persist_entity(game, GAME_TABLE_NAME, columns)

    def persist_contact(self, contact):
        if contact.is_accepted:
            contact.connected_user_id = contact.connected_user.id

        columns = ('connected_user_id', 'connected_word', 'connected_at', 'valid_until', 'is_active', 'is_successful')

        self.persist_entity(contact, CONTACT_TABLE_NAME, columns)

    def check_accepted_contact(self, contact):
        if not contact.is_accepted:
            raise Exception(u'trying to check unaccepted contact')
        if not contact.is_active:
            raise Exception(u'contact shouldn\'t be inactive')
        if contact.check_at > timezone.now():
            raise Exception(u'it\'s too early')

        game = contact.game

        if contact.is_connected_word_right():
            contact.is_successful = True
            for c in game.active_contacts:
                self.remove_contact(c)
            game.remove_active_contacts()
            notification_manager.emit_for_room(game.room_id, 'successful_contact_connection', contact_id=contact.id, word=contact.word)
            if contact.game_word_guessed() or game.guessed_letters+1 == game:
                game.end()
                notification_manager.emit_for_room(game.room_id, 'game_complete', word=game.guessed_word, is_word_guessed=contact.game_word_guessed())
            else:
                game.show_next_letter()
                notification_manager.emit_for_room(game.room_id, 'next_letter_opened', letter=game.last_visible_letter)
            self.persist_game(game)
        else:
            contact.is_active = False
            notification_manager.emit_for_room(game.room_id, 'unsuccessful_contact_connection', { 'contact_id' : contact.id })
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

        notification_manager.emit_for_room(game.room_id, 'accepted_contact', contact_id=contact_id, user_id=user.id, seconds_left=contact.seconds_left)

    def remove_contact(self, contact):
        del self.active_contacts[contact.id]
        contact.is_active = False
        self.persist_contact(contact)

    def break_contact(self, user, game, contact_id, word):
        self.check_callbacks()
        contact = self.find_active_contact(contact_id, game)
        if user != game.master:
            raise GameError(u'Только ведущий может обрывать контакт')
        if not contact.is_active:
            raise GameError(u'Контакт уже не активен')

        if contact.is_right_word(word):
            contact.get_broken()
            self.persist_contact(contact)
            self.remove_contact(contact)
            notification_manager.emit_for_room(game.room_id, 'broken_contact', contact_id=contact_id, user_id=user.id)
        else:
            notification_manager.emit_for_user_in_room(user.id, game.room_id, 'unsuccessful_contact_breaking', { 'contact_id' : contact_id })

game_manager = GameManager()
