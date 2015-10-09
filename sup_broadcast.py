#!/usr/bin/env python3
"""
Read events from supervisor and write the supervisor state into redis

This script is designed to be installed as supervisor event listener.
"""

import sys
import urllib.parse
import redis

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

opt = None

def main():
	global opt
	opt = parse_cmdline()
	register_in_redis()

	while 1:
		write_stdout('READY\n') # transition from ACKNOWLEDGED to READY
		line = sys.stdin.readline()  # read header line from stdin
		logger.debug("line: %s", line.rstrip())

		headers = dict([ x.split(':') for x in line.split() ])
		if headers['eventname'] == 'TICK_60':
			register_in_redis()

		data = sys.stdin.read(int(headers['len'])) # read the event payload
		logger.debug("data: %s", data) # print the event payload to stderr

		write_stdout('RESULT 2\nOK') # transition from READY to ACKNOWLEDGED

_redis = None

def register_in_redis():
	global _redis
	if _redis is None:
		logger.info("connecting to redis at %s" % opt.redis)
		pool = redis.ConnectionPool.from_url(opt.redis)
		_redis = redis.StrictRedis(connection_pool=pool)

	r = _redis

	key = 'sup-url-%s' % url2name(opt.url)
	logger.info("storing %s -> %s", key, opt.url)
	r.setex(key, 100, opt.url)

def url2name(url):
    url = urllib.parse.urlparse(url)
    if url.port == 9001:
        return url.hostname
    else:
        return '%s-%s' % (url.hostname, url.port)

def parse_cmdline():
	from argparse import ArgumentParser
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('url', metavar="URL",
		help="url to reach this supervisor")
	parser.add_argument('redis', metavar="REDIS",
		help="redis connection url instance to broadcast to")

	opt  = parser.parse_args()
	return opt

if __name__ == '__main__':
	main()
