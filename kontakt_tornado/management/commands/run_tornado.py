from kontakt_tornado.socketio import start_server
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        start_server()
