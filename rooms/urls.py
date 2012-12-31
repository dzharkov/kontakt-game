from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms.views',
    # Examples:
    url(r'^(?P<room_id>\d+)/(?P<user_id>\d+)$', 'room'),
    url(r'^clear$', 'clear_room'),
    url(r'^create$', 'create'),
    url(r'^edit/(?P<id>\d+)$', 'edit'),
    url(r'^list$', 'list'),
)
