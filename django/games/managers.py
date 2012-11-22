# -*- coding: utf-8 -*-
from django.db import models

class GameManager(models.Manager):
    def get_dummy_game(self):
        return self.get(pk=1)

class ContactManager(models.Manager):
    def create_dummy_contacts_for_game(self):
        from django.db import connection, transaction
        #transaction.
        cursor = connection.cursor()
        transaction.enter_transaction_management(True)
        cursor.execute("TRUNCATE games_contact")
        cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL),(2,1,'2012-11-22 17:09:04',4,'модуль','кусок чего-либо',NULL,NULL,NULL)")
        transaction.commit()
        #if transaction.is_managed():
        #    transaction.commit()
