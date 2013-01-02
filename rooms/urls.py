from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms.views',
    # Examples:
    url(r'^(?P<room_id>\d+)/(?P<user_id>\d+)$', 'authorize_user_and_redirect_to_room'),
    url(r'^(?P<room_id>\d+)$', 'room'),
    url(r'^clear$', 'clear_room'),
    url(r'^create$', 'create'),
    url(r'^edit/(?P<id>\d+)$', 'edit'),
    url(r'^delete/(?P<id>\d+)$', 'delete'),
    url(r'^list$', 'list'),
    url(r'^list/my$', 'my_list'),
)
