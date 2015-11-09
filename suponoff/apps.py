from django.apps import AppConfig
from django.conf import settings

import supcast.config

class SupOnOffAppConfig(AppConfig):
	name = 'suponoff'
	verbose_name = "Supervisor On/Off interface"

	def ready(self):
		class DummyConf: pass
		conf = DummyConf()
		conf.redis = settings.SUP_REDIS_URL
		supcast.config.set_config(conf)
