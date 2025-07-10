from django.db import models
from django.utils.translation import gettext_lazy as _


class ItemCategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class ItemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )

    # Ordering field for menu display
    ordering = models.IntegerField(
        default=1,
        help_text=_("Order of display in navigation menu (lower numbers appear first)"),
    )

    objects = ItemCategoryManager()

    class Meta:
        verbose_name_plural = _("Item Categories")
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

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

    def is_leaf_category(self):
        """Check if this category has no subcategories (is a leaf category)"""
        return not self.subcategories.exists()

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
