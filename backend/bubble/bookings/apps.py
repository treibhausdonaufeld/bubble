from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bubble.bookings"

    def ready(self):
        """Import signal handlers when the app is ready."""
        import bubble.bookings.signals  # noqa: PLC0415, F401
