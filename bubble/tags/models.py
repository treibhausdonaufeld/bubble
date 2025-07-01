from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ItemTag(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = _("Item Tags")

    def __str__(self):
        return self.name
