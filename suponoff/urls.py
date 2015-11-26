from django.conf.urls import patterns, url

urlpatterns = patterns(
    'suponoff.views',
    url(r'^$', 'home', name='home'),
    url(r'^action$', 'action', name='action'),
    url(r'^group_action$', 'group_action', name='group_action'),
    url(r'^monitor$', 'monitor', name='monitor'),
    url(r'^data$', 'get_data', name='data'),
    url(r'^data/program-logs$', 'get_program_logs', name='program_logs'),
)
