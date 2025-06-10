from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.categories.models import ItemTag

EVENT_TYPE_CHOICES = [
    (0, 'Workshop'),
    (1, 'Gemeinschaftsveranstaltung'),
    (2, 'Bildungsveranstaltung'),
    (3, 'Soziale Veranstaltung'),
    (4, 'Freiwilligenarbeit'),
    (5, 'Sonstiges')
]


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
    event_type = models.IntegerField(choices=EVENT_TYPE_CHOICES, default=0, verbose_name="Event Typ")
    start_datetime = models.DateTimeField(verbose_name="Start Datum & Zeit")
    end_datetime = models.DateTimeField(verbose_name="End Datum & Zeit")
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
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.name} - {self.start_datetime.strftime('%d.%m.%Y')}"

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
        return self.start_datetime > timezone.now()

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