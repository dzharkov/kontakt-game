from django.db import models, connection, transaction
from django.contrib.auth.models import User
from games.managers import GAME_TABLE_NAME

class Room(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    owner = models.ForeignKey(User)
    online_amount = models.IntegerField(blank=False, default=0)

    def save(self, *args, **kwargs):
        is_new = self.id is None

        super(Room, self).save(*args, **kwargs)

        if is_new:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO " + GAME_TABLE_NAME + " SET room_id = " + str(self.id) + ", master_id = NULL, guessed_word = NULL, guessed_letters = NULL")
            transaction.commit_unless_managed()