from . import config

import logging
logger = logging.getLogger()


sup_tags = set()
group_tags = {}

def get(group):
    return list(group_tags.get(group, sup_tags))

def remove(group):
    group_tags.pop(group, None)

def get_all():
    return group_tags.copy()

def set_all():
    gtags = {}
    stags = []

    cfg = config.get_config()
    for section in cfg.sections():
        for name, value in cfg.items(section, raw=True):
            if name != 'tags':
                continue
            if ':' in section:
                gtags[section.rsplit(':')[1]] = parse(value)
            elif section == 'supervisord':
                stags = parse(value)

    # apply the supervisor tags to all the groups, sort
    for k in gtags:
        v = set(gtags[k])
        v.update(stags)
        gtags[k] = sorted(v)

    # replace tags
    global sup_tags, group_tags
    sup_tags = sorted(set(stags))
    group_tags = gtags

def parse(s):
    return [ t.strip() for t in s.split(',') ]
