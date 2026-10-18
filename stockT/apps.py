from django.apps import AppConfig


class StockTConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stockT'
    verbose_name = 'Stock Management'

    def ready(self):
        # Register signal receivers.
        from . import signals  # noqa: F401
