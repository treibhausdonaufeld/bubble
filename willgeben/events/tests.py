from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Event

User = get_user_model()


class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    def test_event_creation(self):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        event = Event.objects.create(
            name='Test Event',
            description='Test description',
            organizer=self.user,
            start_datetime=start_time,
            end_datetime=end_time,
            location='Test Location'
        )
        self.assertEqual(event.name, 'Test Event')
        self.assertTrue(event.active)
        self.assertEqual(event.attendee_count, 0)
        self.assertTrue(event.has_space)
        self.assertTrue(event.is_upcoming)