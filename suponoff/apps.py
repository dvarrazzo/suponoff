from django.apps import AppConfig
from django.conf import settings

import supcast

class SupOnOffAppConfig(AppConfig):
	name = 'suponoff'
	verbose_name = "Supervisor On/Off interface"

	def ready(self):
		supcast.set_redis_url(settings.SUP_REDIS_URL)
