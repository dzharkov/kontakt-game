# -*- coding: utf-8 -*-
from django import forms
from models import Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('name', 'is_private')

    name = forms.CharField(min_length=5, max_length=100, required=True, label=u"Название")
    is_private = forms.BooleanField(label=u'Закрытая?', required=False)