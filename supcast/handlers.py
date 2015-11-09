from . import supcredis
from . import rpc

def TICK_60(headers, data):
	supcredis.register()
	procs = rpc.get_all_procs_info()
	for proc in procs:
		supcredis.set_process_state(proc)

def process_state(headers, data):
	data = dict([ x.split(':') for x in data.split() ])
	# state has the same structure of the getProcessInfo XMLRPC structure
	# limited to the fields we care about
	state = dict(
		statename= headers['eventname'].rsplit('_', 1)[1],
		group=data['groupname'],
		name=data['processname'],
		pid=data.get('pid', None))
	supcredis.set_process_state(state)

PROCESS_STATE_STARTING  = process_state
PROCESS_STATE_RUNNING   = process_state
PROCESS_STATE_BACKOFF   = process_state
PROCESS_STATE_STOPPING  = process_state
PROCESS_STATE_EXITED    = process_state
PROCESS_STATE_STOPPED   = process_state
PROCESS_STATE_FATAL     = process_state
PROCESS_STATE_UNKNOWN   = process_state
