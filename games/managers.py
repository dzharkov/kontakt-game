# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone
from models import *

from app import settings

class ContactManager(object):
    @staticmethod
    def create_dummy_contacts_for_game():
        from django.db import connection, transaction

        cursor = connection.cursor()
        transaction.enter_transaction_management(True)
        cursor.execute("SET foreign_key_checks = 0")
        cursor.execute("TRUNCATE games_contact")
        cursor.execute("TRUNCATE games_game")
        cursor.execute("SET foreign_key_checks = 1")
        cursor.execute(u"INSERT INTO `games_game` VALUES (1,2,'моделирование',2)")
        cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL),(2,1,'2012-11-22 17:09:04',4,'модуль','кусок чего-либо',NULL,NULL,NULL)")
        transaction.commit()

    @staticmethod
    def get_earliest_time_of_active_contacts():
        now = timezone.now()
        return now - timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)


from kontakt_tornado.database import db
from kontakt_tornado.managers import notification_manager, user_manager

GAME_TABLE_NAME = 'games_game'
CONTACT_TABLE_NAME = 'games_contact'

class GameManager(object):

    def __init__(self):
        self.active_games = dict()
        self.active_contacts = dict()

    def load_active_games(self):
        for row in db.query("SELECT * FROM %s" % GAME_TABLE_NAME):
            self.add_game_from_db_row(row)

    def add_game_from_db_row(self, row):
        game = Game()
        for field, value in row.iteritems():
            game.__setattr__(field, value)

        game.master = user_manager.get_user_by_id(game.master_id)

        for contact_row in db.query("SELECT * FROM " + CONTACT_TABLE_NAME + " WHERE game_id = %s", game.id):
            contact = self.add_contact_from_db_row(contact_row)
            game.add_active_contact(contact)
            contact.game = game

        self.active_games[game.id] = game
        return game

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

game_manager = GameManager()
