# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Room.online_amount'
        db.add_column('rooms_room', 'online_amount',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Room.online_amount'
        db.delete_column('rooms_room', 'online_amount')


    models = {
    }

    complete_apps = ['rooms']