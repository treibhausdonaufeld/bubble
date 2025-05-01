from django.db import models

TYPE_CHOICES = [
    (0, 'sell'),
    (1, 'book'),
    (2, 'give away'),
    (3, 'service'),
]

class Category(models.Model):
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True, null=True)
  prompt_name = models.TextField(blank=True, null=True)
  prompt_description = models.TextField(blank=True, null=True)
  type = models.IntegerField(choices=TYPE_CHOICES, blank=True, null=True)
  parent_category = models.ForeignKey('self',
                                      on_delete=models.CASCADE,
                                      related_name='subcategories',
                                      blank=True,
                                      null=True)

  class Meta:
    verbose_name_plural = "Categories"

  def __str__(self):
    return self.name

  def get_hierarchy(self):
    """Returns the full category hierarchy path"""
    if self.parent_category:
      return f"{self.parent_category.get_hierarchy()} > {self.name}"
    return self.name


class Tag(models.Model):
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True, null=True)

  def __str__(self):
    return self.name


class CategoryAvailableTagRelation(models.Model):
  category = models.ForeignKey(Category,
                               on_delete=models.CASCADE,
                               related_name='available_tags')
  tag = models.ForeignKey(Tag,
                          on_delete=models.CASCADE,
                          related_name='available_in_categories')

  class Meta:
    unique_together = ('category', 'tag')

  def __str__(self):
    return f"{self.category.name} - {self.tag.name}"
