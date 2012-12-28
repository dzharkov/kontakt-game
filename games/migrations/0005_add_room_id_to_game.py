# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.add_column('games_game', 'room_id', models.IntegerField(null=False, blank=False))
        db.execute("UPDATE games_game SET room_id = 1")

    def backwards(self, orm):
        db.delete_column('games_game', 'room_id')

    models = {
        
    }

    complete_apps = ['games']