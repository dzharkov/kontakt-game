# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        for table in ('games_game', 'games_contact'):
            db.add_column(table, 'is_active', models.BooleanField(default=True))

        db.add_column('games_contact', 'is_successful', models.BooleanField(default=False))

    def backwards(self, orm):
        for table in ('games_game', 'games_contact'):
            db.delete_column(table, 'is_active')

        db.delete_column('games_contact', 'is_successful')

    models = {
        
    }

    complete_apps = ['games']