from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'suponoff.views.home', name='suponoff_home'),
    url(r'^action$', 'suponoff.views.action', name='suponoff_action'),
    url(r'^group_action$', 'suponoff.views.group_action', name='suponoff_group_action'),
    url(r'^data$', 'suponoff.views.get_data', name='suponoff_data'),
    url(r'^data/program-logs$', 'suponoff.views.get_program_logs',
        name='suponoff_program_logs'),
)
