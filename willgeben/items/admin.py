from django.contrib import admin
from .models import Item, Image, ItemTagRelation

admin.site.register(Item)
admin.site.register(Image)
admin.site.register(ItemTagRelation)

# Register your models here.
