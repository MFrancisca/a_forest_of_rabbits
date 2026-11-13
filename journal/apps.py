from django.apps import AppConfig


class JournalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'journal'
    verbose_name = 'Blog'

    def ready(self):
        from journal import signals  # noqa: F401  (connects the receivers)
