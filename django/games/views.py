# -*- coding: utf-8 -*-
from models import *

from utils import contacts_lock

from app.utils import api_response
from exceptions import *


@api_response()
@contacts_lock
def accept_contact(request, id):
    user = request.user
    print user.pk
    contact = Contact.objects.get_by_id(id)

    if contact.is_active():
        raise GameError(u'Контакт не активен')

    if contact.is_canceled():
        raise GameError(u'Контакт отменен')

    if contact.author == user:
        raise GameError(u'Ваш же контакт')

    game = contact.game

    if game.has_active_accepted_contacts():
        raise GameError(u'Контакт в игре уже принят')

    word = request.GET['word']

    if not contact.can_be_connected_word(word):
        raise GameError(u'Предложенное слово не подходит')

    contact.accept(request.user, word)
    contact.save()

    return {}