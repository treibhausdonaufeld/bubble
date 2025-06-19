from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from willgeben.categories.models import ServiceCategory

from .models import Service

User = get_user_model()


class ServiceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
        )
        self.category = ServiceCategory.objects.create(
            name="Test Category",
        )

    def test_service_creation(self):
        service = Service.objects.create(
            name="Test Service",
            description="Test description",
            user=self.user,
            category=self.category,
            price=25.00,
            duration=timedelta(hours=1),
        )
        assert service.name == "Test Service"
        assert str(service) == "Test Service"
        assert service.active
        assert service.display_contact
