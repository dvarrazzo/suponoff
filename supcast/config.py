"""
Configuration of the events handler
"""

from six.moves import urllib
from glob import glob
from argparse import ArgumentParser
from six.moves.configparser import ConfigParser, Error

import logging
logger = logging.getLogger()


_cfg = None

def get_config():
    """
    Get the configuration for the application.

    It must have been set before by `set_config()`.
    """
    global _cfg
    if _cfg is not None:
        return _cfg
    else:
        raise RuntimeError("app not configured")

def set_config(cfg):
    """
    Set the configuration for the application.

    It must be the object returned by `parse_config_files()` or
    `parse_command_line()`.
    """
    global _cfg
    _cfg = cfg

    from . import tags
    tags.set_all()

def set_redis_url(url):
    """
    Only set the redis url

    Using this instead of set_config() it is possible to use the supcast
    module to read the state out of redis (i.e. as a client would do, as
    opposite as what sup_broadcast does.
    """
    class DummyConf:
        def sections(self):
            return []

    conf = DummyConf()
    conf.redis = url
    set_config(conf)


def get_group(name):
    cfg = get_config()
    for sectname, sect in cfg.items():
        if ':' in sectname and sectname.rsplit(':', 1)[1] == name:
            return dict(sect)


def parse_command_line(args=None):
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', metavar="FILE",
        help="supervisor configuration file [default: %(default)s]")

    g = parser.add_mutually_exclusive_group()
    g.add_argument('--quiet', dest='loglevel', action='store_const',
        default=logging.INFO, const=logging.WARN, help="talk less")
    g.add_argument('--verbose', dest='loglevel', action='store_const',
        default=logging.INFO, const=logging.DEBUG, help="talk less")

    args = parser.parse_args(args)
    try:
        conf = parse_config_file(args.config)
    except Exception as e:
        parser.error("error reading config file %s: %s" % (args.config, e))

    logger = logging.getLogger()
    logger.setLevel(args.loglevel)

    return conf

def parse_config_file(filename):
    logger.debug("reading configuration file: %s", filename)
    cp = ConfigParser()
    with open(filename) as f:
        cp.readfp(f, filename=filename)

    if cp.has_option('include', 'files'):
        for fn in glob(cp.get('include', 'files')):
            cp.read(fn)

    cp.redis = cp.get('sup_broadcast', 'redis')
    cp.url = cp.get('sup_broadcast', 'supervisor_url')
    try:
        cp.ident = cp.get('supervisord', 'identifier')
    except Error:
        cp.ident = _url2name(cp.url)

    cp.config_file = filename

    return cp

def reread():
    cfg = get_config()
    set_config(parse_config_file(cfg.config_file))


def get_name():
    cfg = get_config()
    return cfg.ident

def _url2name(url):
    url = urllib.parse.urlparse(url)
    if url.port == 9001:
        return url.hostname
    else:
        return '%s-%s' % (url.hostname, url.port)
