from django.db import models
from django.utils.translation import gettext_lazy as _


class ItemCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    prompt_name = models.TextField(blank=True, null=True)
    prompt_description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name_plural = _("Item Categories")

    def __str__(self):
        return self.name

    def get_hierarchy(self):
        """Returns the full category hierarchy path"""
        if self.parent_category:
            return f"{self.parent_category.get_hierarchy()} > {self.name}"
        return self.name


