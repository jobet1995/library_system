from django.apps import AppConfig


class ReportsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "report"
    # Use a custom label to avoid conflicts
    label = "reports_app"
