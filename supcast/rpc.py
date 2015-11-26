from six.moves import xmlrpc_client

from . import config

import logging
logger = logging.getLogger()

_cli = None

def client():
    global _cli
    if _cli is None:
        cfg = config.get_config()
        url = cfg.url + "/RPC2"
        logger.info("connecting to rpc at %s" % url)
        _cli = xmlrpc_client.ServerProxy(url, verbose=False)

    return _cli

def get_all_procs_info():
    cli = client()
    procs = cli.supervisor.getAllProcessInfo()
    return procs
