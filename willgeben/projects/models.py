from django.db import models
from config.settings.base import AUTH_USER_MODEL
from willgeben.categories.models import ItemTag

PROJECT_STATUS_CHOICES = [
    (0, 'Planung'),
    (1, 'Laufend'), 
    (2, 'Pausiert'),
    (3, 'Abgeschlossen'),
    (4, 'Abgebrochen')
]


class Project(models.Model):
    """
    Project model for managing community projects.
    Projects are collaborative efforts that community members can participate in.
    """
    active = models.BooleanField(default=True)
    creator = models.ForeignKey(AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='created_projects')
    participants = models.ManyToManyField(AUTH_USER_MODEL,
                                        related_name='projects',
                                        blank=True)
    name = models.CharField(max_length=255, verbose_name="Projekt Name")
    description = models.TextField(verbose_name="Beschreibung")
    goals = models.TextField(blank=True, null=True, verbose_name="Ziele")
    requirements = models.TextField(blank=True, null=True, verbose_name="Anforderungen")
    status = models.IntegerField(choices=PROJECT_STATUS_CHOICES, default=0, verbose_name="Status")
    start_date = models.DateField(blank=True, null=True, verbose_name="Startdatum")
    end_date = models.DateField(blank=True, null=True, verbose_name="Enddatum")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ort")
    max_participants = models.PositiveIntegerField(blank=True, null=True, verbose_name="Max. Teilnehmer")
    intern = models.BooleanField(default=False, verbose_name="Nur für Interne")
    contact_info = models.TextField(blank=True, null=True, verbose_name="Kontakt Info")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekte"
        ordering = ['-date_created']

    def __str__(self):
        return self.name

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def has_space(self):
        if self.max_participants:
            return self.participant_count < self.max_participants
        return True


class ProjectTagRelation(models.Model):
    """Many-to-many relationship between Projects and ItemTags."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ItemTag, on_delete=models.CASCADE, related_name='projects')

    class Meta:
        unique_together = ('project', 'tag')

    def __str__(self):
        return f"{self.project.name} - {self.tag.name}"