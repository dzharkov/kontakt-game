# -*- coding: utf-8 -*-
from django.db import models, connection, transaction
from django.contrib.auth.models import User
from games.managers import GAME_TABLE_NAME
from games.models import GAME_STATE_COMPLETE, GAME_STATE_MASTER_SELECTION, GAME_STATE_NOT_STARTED, GAME_STATE_RUNNING

class Room(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    owner = models.ForeignKey(User, related_name='rooms_own')
    online_amount = models.IntegerField(blank=False, default=0)
    is_private = models.BooleanField(blank=False, default=False)
    invited = models.ManyToManyField(User, related_name='rooms')

    def save(self, *args, **kwargs):
        is_new = self.id is None

        super(Room, self).save(*args, **kwargs)

        if is_new:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO " + GAME_TABLE_NAME + " SET room_id = " + str(self.id) + ", master_id = NULL, guessed_word = NULL, guessed_letters = NULL")
            transaction.commit_unless_managed()

    @property
    def game_state(self):
        if not self.id:
            return None
        if not hasattr(self, '_game_state'):
            cursor = connection.cursor()
            cursor.execute("SELECT state FROM " + GAME_TABLE_NAME + " WHERE id = %s", self.id)
            self._game_state = cursor.fetchone()[0]

        return self._game_state

    @property
    def game_state_name(self):
        if self.game_state == GAME_STATE_COMPLETE:
            return u'Завершена'
        if self.game_state == GAME_STATE_MASTER_SELECTION:
            return u'Выбирается мастер'
        if self.game_state == GAME_STATE_NOT_STARTED:
            return u'Не начата'
        if self.game_state == GAME_STATE_RUNNING:
            return u'В процессе'