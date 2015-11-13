import re
import logging
import urllib.parse
from collections import defaultdict

import redis

from . import config

logger = logging.getLogger()

TIMEOUT = 100

class Key:
    def __init__(self, attr, sup=None, group=None, proc=None):
        self.attr = attr
        self.sup = sup
        self.group = group
        self.proc = proc

    def __str__(self):
        rv = []
        if self.sup:
            sup = self.sup
        else:
            cfg = config.get_config()
            sup = url2name(cfg.url)
        rv.append("sup[%s]" % sup)

        if self.group:
            rv.append("group[%s]" % self.group)

        if self.proc:
            rv.append("proc[%s]" % self.proc)

        rv.append('.')
        rv.append(self.attr)

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


def register():
    cfg = config.get_config()
    setex(Key('url'), cfg.url)

def set_process_state(data):
    group = data['group']
    proc = data['name']
    setex(Key("statename", group=group, proc=proc), data['statename'])
    if data.get('pid'):
        setex(Key("pid", group=group, proc=proc), data['pid'])
    else:
        delete(Key("pid", group=group, proc=proc))

def remove_group(group):
    r = server()
    for k in r.scan_iter(r'sup\[[^\]]*\]group\[%s\]*' % group):
        delete(k)

def get_sups():
    r = server()
    servers = []
    for k in r.scan_iter(r'sup\[[^\]]*\]\.url'):
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
    # recursive defaultdict!
    rdict = lambda: defaultdict(rdict)
    rv = rdict()

    # Supervisors attributes
    r = server()
    for rk in r.scan_iter('sup\[*'):
        v = r.get(rk)
        if v is None: continue
        v = v.decode('utf8')
        k = Key.parse(rk)

        if k.group is None:
            rv['supervisors'][k.sup][k.attr] = v
        elif k.proc is None:
            rv['supervisors'][k.sup] \
                ['groups'][k.group][k.attr] = v
        else:
            rv['supervisors'][k.sup] \
                ['groups'][k.group] \
                ['processes'][k.proc][k.attr] = v

    return rv

def set_group_tags(group, tags):
    k = str(Key('tags', group=group))
    setex(k, ','.join(tags))


def delete(k):
    logger.debug("removing %s", k)
    server().delete(str(k))

def setex(k, value):
    logger.debug("storing %s -> %s", k, value)
    server().setex(str(k), TIMEOUT, value)


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
