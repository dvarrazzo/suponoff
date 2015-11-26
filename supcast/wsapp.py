#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()

import json
from argparse import ArgumentParser

from flask import Flask
from flask_socketio import SocketIO

import supcast.config
import supcast.supcredis

import logging
logger = logging.getLogger()

def redis_listener(socketio):
	r = supcast.supcredis.server()
	ps = r.pubsub()
	ps.subscribe('process')
	for msg in ps.listen():
		if msg['type'] != 'message':
			continue
		try:
			socketio.emit('process',
						  json.loads(msg['data'].decode('utf8')),
						  namespace='/ws')
		except:
			logger.exception('error sending')

def main(**kwargs):
	opt = parse_cmdline()
	app = Flask('supcast.wsapp')
	app.config['SECRET_KEY'] = 'TODO: some secret?'
	socketio = SocketIO(app, async_mode='eventlet')
	eventlet.spawn(redis_listener, socketio)
	supcast.config.set_redis_url(opt.redis)
	socketio.run(app, host=opt.host, port=opt.port, **kwargs)

def parse_cmdline():
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('--host', default='127.0.0.1',
		help="listen host to bind [default: %(default)s]")
	parser.add_argument('--port', type=int, default=5000,
		help="listen port to bind [default: %(default)s]")
	parser.add_argument('--redis', metavar="URL",
		default="redis://localhost:6379",
		help="where supervisors are storing data? [default: %(default)s]")

	opt = parser.parse_args()

	return opt

if __name__ == '__main__':
	main(debug=True)
