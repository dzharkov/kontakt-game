# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.delete_column('games_game', 'is_active')
        db.add_column('games_game', 'state', models.CharField(null=False, blank=False, default='not_started', max_length=20))
        db.execute("UPDATE games_game SET state = 'running'")

    def backwards(self, orm):
        db.delete_column('games_game', 'state')
        db.add_column('games_game', 'is_active', models.BooleanField(default=True))

    models = {
        
    }

    complete_apps = ['games']