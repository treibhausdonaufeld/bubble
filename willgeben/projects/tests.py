from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Project

User = get_user_model()


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
        )

    def test_project_creation(self):
        project = Project.objects.create(
            name="Test Project",
            description="Test description",
            creator=self.user,
        )
        assert project.name == "Test Project"
        assert str(project) == "Test Project"
        assert project.active
        assert project.status == 0  # Planning
        assert project.participant_count == 0
        assert project.has_space
