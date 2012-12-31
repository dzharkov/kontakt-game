# -*- coding: utf-8 -*-
from django import forms
from models import Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('name', )

    name = forms.CharField(min_length=5, max_length=100, required=True, label=u"Название")