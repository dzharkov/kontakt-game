# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone

from app import settings

class ContactManager(object):
    @staticmethod
    def create_dummy_contacts_for_game():
        from django.db import connection, transaction

        cursor = connection.cursor()
        transaction.enter_transaction_management(True)
        cursor.execute("TRUNCATE games_contact")
        cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL),(2,1,'2012-11-22 17:09:04',4,'модуль','кусок чего-либо',NULL,NULL,NULL)")
        transaction.commit()

    @staticmethod
    def get_earliest_time_of_active_contacts():
        now = timezone.now()
        return now - timedelta(seconds=settings.CONTACT_CHECKING_TIMEOUT)