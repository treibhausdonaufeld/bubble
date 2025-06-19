from django.db import models
from config.settings.base import AUTH_USER_MODEL
from bubble.categories.models import ItemCategory
from bubble.tags.models import ItemTag

STATUS_CHOICES = [(0, 'New'), (1, 'Used'), (2, 'Old')]
ITEM_TYPE_CHOICES = [(0, 'Sell'), (1, 'Give Away'), (2, 'Borrow'), (3, 'Need')]


class Item(models.Model):
    active = models.BooleanField(default=True)
    user = models.ForeignKey(AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='items')
    category = models.ForeignKey(ItemCategory,
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
    item_type = models.IntegerField(choices=ITEM_TYPE_CHOICES, default=0)
    profile_img_frame = models.ImageField(upload_to='items/', blank=True, null=True)
    profile_img_frame_alt = models.CharField(max_length=255, blank=True, null=True)

    # Add class constants for easy access
    STATUS_CHOICES = STATUS_CHOICES
    ITEM_TYPE_CHOICES = ITEM_TYPE_CHOICES

    def __str__(self):
        return self.name


class ItemTagRelation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ItemTag, on_delete=models.CASCADE, related_name='items')

    class Meta:
        unique_together = ('item', 'tag')

    def __str__(self):
        return f"{self.item.name} - {self.tag.name}"


class Image(models.Model):
  fname = models.ImageField(upload_to='items/images/')
  fname_alt = models.CharField(max_length=255, blank=True, null=True)
  item = models.ForeignKey(Item,
                           on_delete=models.CASCADE,
                           related_name='images')
  ordering = models.IntegerField(default=0)

  def __str__(self):
    return f"Image for {self.item.name} ({self.fname})"
