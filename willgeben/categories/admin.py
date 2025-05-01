from django.contrib import admin
from .models import Category, Tag, CategoryAvailableTagRelation

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(CategoryAvailableTagRelation)

# Register your models here.
