from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Project

User = get_user_model()


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    def test_project_creation(self):
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            creator=self.user
        )
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(str(project), 'Test Project')
        self.assertTrue(project.active)
        self.assertEqual(project.status, 0)  # Planning
        self.assertEqual(project.participant_count, 0)
        self.assertTrue(project.has_space)