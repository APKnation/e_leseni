from django.apps import AppConfig


class LicencesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'licences'

    def ready(self):
        from . import signals  # noqa: F401
