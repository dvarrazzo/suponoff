from . import config

group_tags = {}

def set(group, tags):
    group_tags[group] = list(tags)

def get(group):
    return list(group_tags.get(group, []))

def remove(group):
    group_tags.pop(group, None)

def get_all():
    return group_tags.copy()

def set_all():
    group_tags.clear()
    cfg = config.get_config()
    for section, conf in cfg.items():
        if ':' in section and 'tags' in conf:
            group_tags[section.rsplit(':')[1]] = parse(conf['tags'])

def parse(s):
    return [ t.strip() for t in s.split(',') ]
