# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.utils.log import logger

from app import settings

class CachingManager(models.Manager):
    def get_by_id(self,id):
        return self.get(pk=id)

class GameManager(CachingManager):
    def get_dummy_game(self):
        return self.get(pk=1)

class ContactManager(CachingManager):
    use_for_related_fields = True

    def active_accepted_query(self):
        return Q(connected_at__isnull=False, connected_at__gt=ContactManager.get_earliest_time_of_active_contacts())

    def active(self):
        return self.filter(Q(connected_at__isnull=True) | self.active_accepted_query())

    def active_accepted(self):
        return self.active().filter(self.active_accepted_query())

    def create_dummy_contacts_for_game(self):
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