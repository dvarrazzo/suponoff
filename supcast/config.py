from argparse import ArgumentParser

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


def parse_command_line():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('url', metavar="URL",
        help="url to reach this supervisor")
    parser.add_argument('redis', metavar="REDIS",
        help="redis connection url instance to broadcast to")

    opt  = parser.parse_args()
    return opt
