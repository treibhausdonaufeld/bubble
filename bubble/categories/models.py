from django.db import models
from django.utils.translation import gettext_lazy as _


class ItemCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    prompt_name = models.TextField(blank=True)
    prompt_description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )

    # Fields for content type definition
    url_slug = models.SlugField(
        max_length=50,
        blank=True,
        help_text=_("URL path for this content type (e.g., 'sachen', 'events')"),
    )

    # Ordering field for menu display
    ordering = models.IntegerField(
        default=1,
        help_text=_("Order of display in navigation menu (lower numbers appear first)"),
    )

    # Schema definition for custom fields
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "JSON schema for custom fields specific to this category. "
            "Format: {'field_name': {'type': 'choice', 'label': 'Size', "
            "'choices': ['S', 'M', 'L'], 'required': true}}",
        ),
    )

    class Meta:
        verbose_name_plural = _("Item Categories")
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name

    def get_hierarchy(self):
        """Returns the full category hierarchy path"""
        if self.parent_category:
            return f"{self.parent_category.get_hierarchy()} > {self.name}"
        return self.name

    @property
    def is_root_category(self):
        """Check if this is a root category (no parent)"""
        return self.parent_category is None

    def get_root_category(self):
        """Get the root category of this category's hierarchy"""
        if self.is_root_category:
            return self
        current = self
        while current.parent_category is not None:
            current = current.parent_category
        return current

    def get_descendants(self, *, include_self=False):
        """Get all descendant categories"""
        descendants = []
        if include_self:
            descendants.append(self)

        # Recursively get all subcategories
        def _get_subcategories(category):
            for subcategory in category.subcategories.all():
                descendants.append(subcategory)
                _get_subcategories(subcategory)

        _get_subcategories(self)
        return descendants
