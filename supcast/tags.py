from . import config

import logging
logger = logging.getLogger()


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
	for section in cfg.sections():
		for name, value in cfg.items(section, raw=True):
			if name != 'tags':
				continue
			if ':' in section:
				group_tags[section.rsplit(':')[1]] = parse(value)
			elif section == 'supervisord':
				group_tags[None] = parse(value)

def parse(s):
	return [ t.strip() for t in s.split(',') ]
