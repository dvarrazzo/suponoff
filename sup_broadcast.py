#!/usr/bin/env python3
"""
Read events from supervisor and write the supervisor state into redis

This script is designed to be installed as supervisor event listener.
"""

import sys

from supcast import config
from supcast import handlers
from supcast import supcredis

import logging
logger = logging.getLogger()
logging.basicConfig(
	level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s')

def write_stdout(s):
	sys.stdout.write(s)
	sys.stdout.flush()

def write_stderr(s):
	sys.stderr.write(s)
	sys.stderr.flush()

def main():
	config.set_config(config.parse_command_line())
	supcredis.register()

	while 1:
		write_stdout('READY\n') # transition from ACKNOWLEDGED to READY

		line = sys.stdin.readline()  # read header line from stdin
		handle_line(line)
		write_stdout('RESULT 2\nOK') # transition from READY to ACKNOWLEDGED

def handle_line(line):
		logger.debug("line: %s", line.rstrip())

		headers = dict([ x.split(':') for x in line.split() ])
		data = sys.stdin.read(int(headers['len'])) # read the event payload
		logger.debug("data: %s", data) # print the event payload to stderr

		try:
			handler = getattr(handlers, headers['eventname'])
		except AttributeError:
			logger.error("handler not found: %s", headers['eventname'])
			return

		try:
			handler(headers, data)
		except Exception:
			logger.exception("error handling %s", headers['eventname'])


if __name__ == '__main__':
	main()
