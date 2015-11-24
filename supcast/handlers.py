from . import rpc
from . import tags
from . import config
from . import supcredis


import logging
logger = logging.getLogger()


def refresh_all():
	supcredis.register()

	procs = rpc.get_all_procs_info()
	for proc in procs:
		supcredis.set_process_state(proc)

	for group, tagslist in tags.get_all().items():
		supcredis.set_group_tags(group, tagslist)

def process_state(headers, data):
	data = parse_data(data)
	# state has the same structure of the getProcessInfo XMLRPC structure
	# limited to the fields we care about
	state = dict(
		statename= headers['eventname'].rsplit('_', 1)[1],
		group=data['groupname'],
		name=data['processname'],
		pid=data.get('pid', None))
	supcredis.set_process_state(state)


def SUPERVISOR_STATE_CHANGE_RUNNING(headers, data):
	refresh_all()

def SUPERVISOR_STATE_CHANGE_STOPPING(headers, data):
	logger.info('stopping')

def TICK_60(headers, data):
	refresh_all()

PROCESS_STATE_STARTING  = process_state
PROCESS_STATE_RUNNING   = process_state
PROCESS_STATE_BACKOFF   = process_state
PROCESS_STATE_STOPPING  = process_state
PROCESS_STATE_EXITED    = process_state
PROCESS_STATE_STOPPED   = process_state
PROCESS_STATE_FATAL     = process_state
PROCESS_STATE_UNKNOWN   = process_state


def PROCESS_GROUP_ADDED(headers, data):
	config.reread()

	data = parse_data(data)
	group = data['groupname']
	tagslist = tags.get(group)
	supcredis.set_group_tags(group, tagslist)

def PROCESS_GROUP_REMOVED(headers, data):
	data = parse_data(data)
	group = data['groupname']
	tags.remove(group)
	supcredis.remove_group(group)



def parse_data(data):
	return dict([ x.split(':') for x in data.split() ])

