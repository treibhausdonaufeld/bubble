from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.categories.models import ItemTag, EventType


class Event(models.Model):
    """
    Event model for managing community events.
    Events are scheduled activities that community members can attend.
    """
    active = models.BooleanField(default=True)
    organizer = models.ForeignKey(AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='organized_events')
    attendees = models.ManyToManyField(AUTH_USER_MODEL,
                                     related_name='events',
                                     blank=True)
    name = models.CharField(max_length=255, verbose_name="Event Name")
    description = models.TextField(verbose_name="Beschreibung")
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, verbose_name="Event Typ")
    start_date = models.DateField(verbose_name="Start Datum")
    end_date = models.DateField(verbose_name="End Datum")
    is_full_day = models.BooleanField(default=False, verbose_name="Ganztägig")
    start_time = models.TimeField(blank=True, null=True, verbose_name="Start Zeit")
    end_time = models.TimeField(blank=True, null=True, verbose_name="End Zeit")
    location = models.CharField(max_length=255, verbose_name="Ort")
    max_attendees = models.PositiveIntegerField(blank=True, null=True, verbose_name="Max. Teilnehmer")
    price = models.DecimalField(max_digits=10,
                              decimal_places=2,
                              blank=True,
                              null=True,
                              verbose_name="Preis")
    requirements = models.TextField(blank=True, null=True, verbose_name="Voraussetzungen")
    materials_needed = models.TextField(blank=True, null=True, verbose_name="Benötigte Materialien")
    intern = models.BooleanField(default=False, verbose_name="Nur für Interne")
    registration_required = models.BooleanField(default=True, verbose_name="Anmeldung erforderlich")
    contact_info = models.TextField(blank=True, null=True, verbose_name="Kontakt Info")
    profile_picture = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name="Profilbild")
    profile_picture_alt = models.CharField(max_length=255, blank=True, null=True, verbose_name="Profilbild Alt Text")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_date', 'start_time']

    def __str__(self):
        return f"{self.name} - {self.start_date.strftime('%d.%m.%Y')}"

    @property
    def attendee_count(self):
        return self.attendees.count()

    @property
    def has_space(self):
        if self.max_attendees:
            return self.attendee_count < self.max_attendees
        return True

    @property
    def is_upcoming(self):
        from django.utils import timezone
        from datetime import datetime, time

        now = timezone.now()
        if self.is_full_day:
            return self.start_date >= now.date()
        else:
            start_time = self.start_time or time(0, 0)
            start_datetime = timezone.make_aware(datetime.combine(self.start_date, start_time))
            return start_datetime > now

    @property
    def is_full(self):
        return not self.has_space


class EventTagRelation(models.Model):
    """Many-to-many relationship between Events and ItemTags."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ItemTag, on_delete=models.CASCADE, related_name='events')

    class Meta:
        unique_together = ('event', 'tag')

    def __str__(self):
        return f"{self.event.name} - {self.tag.name}"


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='event_images/', verbose_name="Bild Datei")
    fname = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dateiname")
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alt Text")
    order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")

    class Meta:
        ordering = ['order']
        verbose_name = "Event Bild"
        verbose_name_plural = "Event Bilder"

    def __str__(self):
        return f"{self.event.name} - Bild {self.order + 1}"