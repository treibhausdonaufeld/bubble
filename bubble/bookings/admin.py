from django.contrib import admin

from .models import Booking
from .models import ExceptionalOpeningHour
from .models import OpeningHour

admin.site.register(Booking)
admin.site.register(OpeningHour)
admin.site.register(ExceptionalOpeningHour)

# Register your models here.
