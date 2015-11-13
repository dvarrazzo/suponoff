"""
Configuration of the events handler
"""

from glob import glob
from argparse import ArgumentParser
from configparser import ConfigParser

import logging

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

def get_group(name):
    cfg = get_config()
    for sectname, sect in cfg.items():
        if ':' in sectname and sectname.rsplit(':', 1)[1] == name:
            return dict(sect)


def parse_command_line(args=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', metavar="URL",
        help="supervisor configuration file [default: %(defaults)s]")
    parser.add_argument('--verbose', action='store_true',
        help="talk more")

    args = parser.parse_args(args)
    try:
        conf = parse_config_file(args.config)
    except Exception as e:
        parser.error("error reading config file %s: %s" % (args.config, e))

    logger = logging.getLogger()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return conf

def parse_config_file(filename):
    cp = ConfigParser()
    with open(filename) as f:
        cp.readfp(f, filename=filename)

    if cp.has_option('include', 'files'):
        for fn in glob(cp.get('include', 'files')):
            cp.read(fn)

    cp.redis = cp.get('sup_broadcast', 'redis')
    cp.url = cp.get('sup_broadcast', 'supervisor_url')
    cp.config_file = filename

    return cp

def reread():
    cfg = get_config()
    set_config(parse_config_file(cfg.config_file))
