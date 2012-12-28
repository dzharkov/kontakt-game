# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.alter_column('games_game', 'master_id', models.IntegerField(null=True))
        db.alter_column('games_game', 'guessed_word', models.CharField(max_length=30, null=True))
        db.alter_column('games_game', 'guessed_letters', models.SmallIntegerField(null=True))

    def backwards(self, orm):
        db.alter_column('games_game', 'master_id', models.IntegerField(null=False))
        db.alter_column('games_game', 'guessed_word', models.CharField(max_length=30, null=False))
        db.alter_column('games_game', 'guessed_letters', models.SmallIntegerField(null=False))

    models = {
        
    }

    complete_apps = ['games']