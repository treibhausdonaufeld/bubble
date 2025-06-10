from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.categories.models import ServiceCategory, ItemTag


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
    availability = models.TextField(blank=True, null=True, verbose_name="Availability")
    intern = models.BooleanField(default=False, verbose_name="Intern Only")
    display_contact = models.BooleanField(default=True, verbose_name="Display Contact Info")
    th_payment = models.BooleanField(default=False, blank=True, null=True, verbose_name="TH Payment Accepted")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-date_created']

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