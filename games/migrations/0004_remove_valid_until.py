# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.delete_column('games_game', 'valid_until')
        db.delete_column('games_contact', 'valid_until')

    def backwards(self, orm):
        db.add_column('games_game', 'valid_until', models.DateTimeField(null=True))
        db.add_column('games_contact', 'valid_until', models.DateTimeField(null=True))

    models = {
        
    }

    complete_apps = ['games']