from django.db import models
from config.settings.base import AUTH_USER_MODEL
from categories.models import Category, Tag

STATUS_CHOICES = [(0, 'new'), (1, 'used'), (2, 'old')]


class Item(models.Model):
  active = models.BooleanField(default=True)
  user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='items')
  category = models.ForeignKey(Category,
                               on_delete=models.CASCADE,
                               related_name='items')
  name = models.CharField(max_length=255)
  description = models.TextField(blank=True, null=True)
  intern = models.BooleanField(default=False)
  display_contact = models.BooleanField(default=True)
  price = models.DecimalField(max_digits=10,
                              decimal_places=2,
                              blank=True,
                              null=True)
  th_payment = models.BooleanField(default=False, blank=True, null=True)
  date_created = models.DateTimeField(auto_now_add=True)
  date_updated = models.DateTimeField(auto_now=True)
  status = models.IntegerField(blank=True, null=True, choices=STATUS_CHOICES)
  profile_img_frame = models.CharField(max_length=255, blank=True, null=True)

  def __str__(self):
    return self.name


class ItemTagRelation(models.Model):
  item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='tags')
  tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='items')

  class Meta:
    unique_together = ('item', 'tag')

  def __str__(self):
    return f"{self.item.name} - {self.tag.name}"


class Image(models.Model):
  fname = models.CharField(max_length=255)
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='images')
  ordering = models.IntegerField(default=0)

  def __str__(self):
    return f"Image for {self.item.name} ({self.fname})"
