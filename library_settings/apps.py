from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LibrarySettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "library_settings"
    verbose_name = _("Library Settings")
    
    def ready(self):
        # Import signals to register them
        import library_settings.signals  # noqa
