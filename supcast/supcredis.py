import re
import json
import logging
import urllib.parse
from collections import defaultdict, namedtuple

import redis

from . import config

logger = logging.getLogger()

TIMEOUT = 100

def key_here(attr=None, group=None, proc=None):
	cfg = config.get_config()
	sup = url2name(cfg.url)
	return Key(attr=attr, sup=sup, group=group, proc=proc)

class Key(namedtuple('Key', 'attr sup group proc')):
	def __str__(self):
		rv = []
		rv.append("sup[%s]" % self.sup)

		if self.group:
			rv.append("group[%s]" % self.group)

		if self.proc:
			rv.append("proc[%s]" % self.proc)

		if self.attr:
			rv.append('.')
			rv.append(self.attr)

		return ''.join(rv)

	def pattern(self):
		rv = []

		rv.append("sup\\[%s\\]" % self.sup)

		if self.group:
			rv.append("group\\[%s\\]" % self.group)

		if self.proc:
			rv.append("proc\\[%s\\]" % self.proc)

		if self.attr:
			rv.append('.')
			rv.append(self.attr)
		else:
			rv.append('*')

		return ''.join(rv)

	_parse_re = re.compile(r"""
		sup \[ (?P<sup>[^\]]+) \]
		(?: group \[ (?P<group>[^\]]+) \]
			(?: proc \[ (?P<proc>[^\]]+) \] )?
		)?
		\. (?P<attr>.*)
		""", re.VERBOSE)

	@classmethod
	def parse(cls, s):
		if isinstance(s, bytes):
			s = s.decode('utf-8')

		m = cls._parse_re.match(s)
		if m is None:
			raise ValueError("bad key pattern: %s" % s)

		return cls(**m.groupdict())

Key.__new__.__defaults__ = (None, None, None, None)


def register():
	cfg = config.get_config()
	change(key_here('url'), cfg.url)

def set_process_state(data):
	group = data['group']
	proc = data['name']
	ch = False
	k = key_here(group=group, proc=proc)
	ch |= change(k._replace(attr="statename"), data['statename'])
	ch |= change(k._replace(attr="pid"), data['pid'])
	if ch:
		state = json.dumps(get_state(k))
		logger.debug("broadcasting %s", state)
		server().publish('process', state)

def remove_group(group):
	r = server()
	for k in r.scan_iter(key_here(group=group).pattern()):
		delete(k)

def get_sups():
	r = server()
	servers = []
	for k in r.scan_iter(Key('url', sup='*').pattern()):
		k = Key.parse(k)
		servers.append(k.sup)

	servers.sort()
	return servers

def get_url(sup):
	r = server()
	k = Key('url', sup=sup)
	rv = r.get(str(k))
	if rv is not None:
		rv = rv.decode('utf8')

	return rv

def get_all_state():
	return get_state(Key())

def get_state(kin=None):
	# recursive defaultdict!
	rdict = lambda: defaultdict(rdict)
	rv = rdict()

	# Supervisors attributes
	r = server()
	for rk in r.scan_iter(r'sup\[*'):
		k = Key.parse(rk)
		v = r.get(rk)
		if v is None: continue
		v = parse_attr(k.attr, v)

		if kin is not None:
			if kin.sup is not None and k.sup is not None and kin.sup != k.sup:
				continue
			if kin.group is not None and k.group is not None and kin.group != k.group:
				continue
			if kin.proc is not None and k.proc is not None and kin.proc != k.proc:
				continue

		if k.group is None:
			rv['supervisors'][k.sup][k.attr] = v
		elif k.proc is None:
			rv['supervisors'][k.sup] \
				['groups'][k.group][k.attr] = v
		else:
			rv['supervisors'][k.sup] \
				['groups'][k.group] \
				['processes'][k.proc][k.attr] = v

	norec = lambda d: { k: norec(v) if isinstance(v, dict) else v
		for k, v in d.items() }
	return norec(rv)


def parse_attr(attr, v):
	if v is None:
		return None
	v = v.decode('utf8')
	if attr == 'tags':
		v = [ t.strip() for t in v.split(',') ]
	elif attr == 'pid':
		v = int(v)
	return v



def set_group_tags(group, tags):
	k = str(key_here('tags', group=group))
	setex(k, ','.join(tags))


def delete(k):
	logger.debug("removing %s", k)
	server().delete(str(k))

def setex(k, value):
	logger.debug("storing %s -> %s", k, value)
	server().setex(str(k), TIMEOUT, value)


def change(k, val):
	"""Set the k to val, delete if val is None.

	Also set an expire time and return True if the value really changed.
	"""
	k = str(k)
	if val is not None:
		if not isinstance(val, (str, bytes)):
			val = str(val)
		if isinstance(val, str):
			val = val.encode('utf8')

	p = server().pipeline()
	if val is not None:
		logger.debug("storing %s -> %s", k, val)
		p.getset(k, val)
		p.expire(k, TIMEOUT)
	else:
		logger.debug("removing %s", k)
		p.get(k)
		p.delete(k)

	oldval = p.execute()[0]
	return oldval != val


_redis = None

def server():
	cfg = config.get_config()

	global _redis
	if _redis is None:
		logger.info("connecting to redis at %s" % cfg.redis)
		pool = redis.ConnectionPool.from_url(cfg.redis)
		_redis = redis.StrictRedis(connection_pool=pool)

	return _redis


def url2name(url):
	url = urllib.parse.urlparse(url)
	if url.port == 9001:
		return url.hostname
	else:
		return '%s-%s' % (url.hostname, url.port)
