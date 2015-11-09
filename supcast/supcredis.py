import re
import logging
import urllib.parse

import redis

from . import config

logger = logging.getLogger()

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

        if self.proc and self.proc != self.group:
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
    setex(Key("state", group=group, proc=proc), data['statename'])
    if data.get('pid'):
        setex(Key("pid", group=group, proc=proc), data['pid'])
    else:
        delete(Key("pid", group=group, proc=proc))

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

def delete(k):
    logger.info("removing %s", k)
    server().delete(str(k))

def setex(k, value):
    logger.info("storing %s -> %s", k, value)
    server().setex(str(k), 100, value)


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
