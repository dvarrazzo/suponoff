"""
Handle messages received by the XMLRPC interface
"""

import json

from . import config
from . import supcredis

import logging
logger = logging.getLogger()


def handle(type, data):
    try:
        handler = globals()[type]
    except KeyError:
        logger.error("remote handler not found: %s", type)
        return

    handler(data)


def monitor(data):
    data = json.loads(data)
    name = config.get_name()
    for proc in data:
        if proc['supervisor'] != name:
            logger.warn("been asked to monitor %s: not mine", proc)
            continue
        supcredis.register_monitor(proc['group'], proc['process'])
