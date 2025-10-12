from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bubble.books"

    def ready(self):
        import bubble.books.signals  # noqa: F401, PLC0415
