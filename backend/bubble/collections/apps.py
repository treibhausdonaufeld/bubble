import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

with contextlib.suppress(ImportError):
    import bubble.collections.signals  # noqa: F401


class CollectionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bubble.collections"
    verbose_name = _("Collections")
