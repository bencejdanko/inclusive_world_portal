from django.apps import AppConfig

class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inclusive_world_portal.portal"

    def ready(self):
        from . import signals  # noqa
