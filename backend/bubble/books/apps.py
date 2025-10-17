from django.apps import AppConfig


class BooksConfig(AppConfig):
    name = "bubble.books"

    def ready(self):
        import bubble.books.signals  # noqa: F401, PLC0415
