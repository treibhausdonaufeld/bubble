from django.apps import AppConfig


class BookingsConfig(AppConfig):
    name = "bubble.bookings"

    def ready(self):
        """Import signal handlers when the app is ready."""
        import bubble.bookings.beats  # noqa: PLC0415
        import bubble.bookings.signals  # noqa: PLC0415, F401
