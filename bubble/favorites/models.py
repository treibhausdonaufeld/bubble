from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from config.settings.base import AUTH_USER_MODEL


class FavoriteList(models.Model):
    """Model representing a collection of favorites that can be shared."""

    name = models.CharField(_("List Name"), max_length=255)
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_favorite_lists",
        verbose_name=_("Owner"),
    )
    shared_with = models.ManyToManyField(
        AUTH_USER_MODEL,
        blank=True,
        related_name="shared_favorite_lists",
        verbose_name=_("Shared With"),
        help_text=_("Users who can view this list but cannot edit it"),
    )
    editors = models.ManyToManyField(
        AUTH_USER_MODEL,
        blank=True,
        related_name="editable_favorite_lists",
        verbose_name=_("Editors"),
        help_text=_("Users who can edit and delete items in this list"),
    )
    is_default = models.BooleanField(
        _("Default List"),
        default=False,
        help_text=_("Default list for new favorites"),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Favorite List")
        verbose_name_plural = _("Favorite Lists")

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def can_edit(self, user):
        """Check if a user can edit this favorite list."""
        return user == self.user or user in self.editors.all()

    def can_view(self, user):
        """Check if a user can view this favorite list."""
        return (
            user == self.user
            or user in self.shared_with.all()
            or user in self.editors.all()
        )

    @classmethod
    def get_user_accessible_lists(cls, user):
        """Get all lists accessible to a user (owned, shared, or editable)."""
        return cls.objects.filter(
            models.Q(user=user) | models.Q(shared_with=user) | models.Q(editors=user)
        ).distinct()

    @classmethod
    def get_or_create_default_list(cls, user):
        """Get or create the default favorite list for a user."""
        default_list, created = cls.objects.get_or_create(
            user=user,
            is_default=True,
            defaults={
                "name": _("My Favorites"),
            },
        )
        return default_list


class Favorite(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    favorite_list = models.ForeignKey(
        FavoriteList,
        on_delete=models.CASCADE,
        related_name="favorites",
        null=True,
        blank=True,
        verbose_name=_("Favorite List"),
        help_text=_("The list this favorite belongs to"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "url", "favorite_list")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def save(self, *args, **kwargs):
        """Ensure favorite is assigned to a favorite list."""
        if not self.favorite_list:
            self.favorite_list = FavoriteList.get_or_create_default_list(self.user)
        super().save(*args, **kwargs)

    @classmethod
    def get_user_favorites(cls, user):
        return cls.objects.filter(user=user)


@receiver(post_save, sender=AUTH_USER_MODEL)
def create_default_favorite_list(sender, instance, created, **kwargs):
    """Create a default favorite list when a user is created."""
    if created:
        FavoriteList.objects.create(
            user=instance,
            name=_("My Favorites"),
            is_default=True,
        )
