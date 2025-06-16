from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.categories.models import ServiceCategory, ItemTag

AVAILABILITY_CHOICES = [
    (0, 'Verfügbar'),
    (1, 'Überlastet'),
    (2, 'Nicht verfügbar'),
    (3, 'Urlaub')
]


class Service(models.Model):
    """
    Service model for managing services offered by users.
    Services are different from items as they represent activities or skills
    that users can provide rather than physical objects.
    """
    active = models.BooleanField(default=True)
    user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='services')
    category = models.ForeignKey(ServiceCategory,
                               on_delete=models.CASCADE,
                               related_name='services')
    name = models.CharField(max_length=255, verbose_name="Service Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10,
                              decimal_places=2,
                              verbose_name="Price per Hour")
    duration = models.DurationField(verbose_name="Typical Duration")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Location")
    availability = models.IntegerField(choices=AVAILABILITY_CHOICES, default=0, verbose_name="Availability Status")
    bookable = models.BooleanField(default=True, verbose_name="Bookable")
    profile_image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name="Profile Image")
    profile_image_alt = models.CharField(max_length=255, blank=True, null=True, verbose_name="Profile Image Alt Text")
    intern = models.BooleanField(default=False, verbose_name="Intern Only")
    display_contact = models.BooleanField(default=True, verbose_name="Display Contact Info")
    th_payment = models.BooleanField(default=False, blank=True, null=True, verbose_name="TH Payment Accepted")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-date_created']

    # Add class constants for easy access
    AVAILABILITY_CHOICES = AVAILABILITY_CHOICES

    def __str__(self):
        return self.name


class ServiceTagRelation(models.Model):
    """Many-to-many relationship between Services and ItemTags."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ItemTag, on_delete=models.CASCADE, related_name='services')

    class Meta:
        unique_together = ('service', 'tag')

    def __str__(self):
        return f"{self.service.name} - {self.tag.name}"


class ServiceImage(models.Model):
    fname = models.ImageField(upload_to='services/images/')
    fname_alt = models.CharField(max_length=255, blank=True, null=True)
    service = models.ForeignKey(Service,
                               on_delete=models.CASCADE,
                               related_name='images')
    ordering = models.IntegerField(default=0)

    def __str__(self):
        return f"Image for {self.service.name} ({self.fname})"