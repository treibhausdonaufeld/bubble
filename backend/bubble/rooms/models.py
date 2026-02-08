from django.db import models
from django.utils.translation import gettext_lazy as _


def upload_to_room_photos(instance: "Room", filename: str):
    """Upload path for room photos."""
    extension = filename.rsplit(".", maxsplit=1)[-1] if "." in filename else "jpg"
    return f"rooms/{instance.pk}/photo.{extension}"


class Room(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=255,
        help_text=_("Name of the room"),
    )
    description = models.TextField(
        _("Description"),
        help_text=_("Detailed description of the room"),
    )
    photo = models.ImageField(
        _("Photo"),
        upload_to=upload_to_room_photos,
        blank=True,
        null=True,
        help_text=_("Photo of the room"),
    )
    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
    )

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["name"]

    def __str__(self):
        return self.name
