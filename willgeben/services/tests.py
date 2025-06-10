from django.test import TestCase
from django.contrib.auth import get_user_model
from willgeben.categories.models import ServiceCategory
from .models import Service

User = get_user_model()


class ServiceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.category = ServiceCategory.objects.create(
            name='Test Category'
        )

    def test_service_creation(self):
        service = Service.objects.create(
            name='Test Service',
            description='Test description',
            user=self.user,
            category=self.category,
            price=25.00
        )
        self.assertEqual(service.name, 'Test Service')
        self.assertEqual(str(service), 'Test Service')
        self.assertTrue(service.active)
        self.assertTrue(service.display_contact)