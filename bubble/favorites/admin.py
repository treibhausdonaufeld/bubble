from django.contrib import admin

from .models import Favorite
from .models import Interest

admin.site.register(Favorite)
admin.site.register(Interest)

# Register your models here.
