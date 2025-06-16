from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from config.settings.base import AUTH_USER_MODEL


class User(AbstractUser):
  """
    Default custom user model for willgeben.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

  # First and last name do not cover name patterns around the globe
  name = CharField(_("Name of User"), blank=True, max_length=255)
  first_name = None  # type: ignore[assignment]
  last_name = None  # type: ignore[assignment]

  def get_absolute_url(self) -> str:
    """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
    return reverse("users:detail", kwargs={"username": self.username})


class Profile(models.Model):
  user = models.OneToOneField(AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='profile')
  address = models.TextField(blank=True, null=True)
  phone = models.CharField(max_length=15, blank=True, null=True)
  email_reminder = models.BooleanField(default=True)
  intern = models.BooleanField(default=False)
  bio = models.TextField(blank=True, null=True)
  profile_image = models.ImageField(upload_to='users/', blank=True, null=True)
  profile_image_alt = models.CharField(max_length=255, blank=True, null=True)
  is_superuser = models.BooleanField(default=False)
  last_login = models.DateTimeField(blank=True, null=True)
  date_joined = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
  if created:
    Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
  instance.profile.save()
