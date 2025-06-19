from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from willgeben.categories.models import EventType

from .models import Event

User = get_user_model()


class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
        )
        self.event_type = EventType.objects.create(name="Test Type")

    def test_event_creation(self):
        start_dt = timezone.now() + timedelta(days=1)
        end_dt = start_dt + timedelta(hours=2)
        event = Event.objects.create(
            name="Test Event",
            description="Test description",
            organizer=self.user,
            event_type=self.event_type,
            start_date=start_dt.date(),
            end_date=end_dt.date(),
            start_time=start_dt.time(),
            end_time=end_dt.time(),
            location="Test Location",
        )
        assert event.name == "Test Event"
        assert event.active
        assert event.attendee_count == 0
        assert event.has_space
        assert event.is_upcoming
