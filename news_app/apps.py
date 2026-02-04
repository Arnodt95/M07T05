from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """
    App configuration for the News Application.

    Signals are imported in ready() to register receivers at startup.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "news_app"

    def ready(self):
        # Register signals
        from . import signals  # noqa: F401
