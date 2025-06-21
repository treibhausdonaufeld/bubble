from django.contrib import admin

from .models import Image
from .models import Item

admin.site.register(Item)
admin.site.register(Image)

# Register your models here.
