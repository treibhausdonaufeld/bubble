"""Tests for items API."""

from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage
from rest_framework import status
from rest_framework.test import APIClient

from bubble.items.models import Image, Item

User = get_user_model()

TEST_PASSWORD = "testpass123"  # noqa: S105


class ImageAPITestCase(TestCase):
    """Test cases for Image API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password=TEST_PASSWORD
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password=TEST_PASSWORD
        )

        # Create test items
        self.item1 = Item.objects.create(
            name="Test Item 1",
            description="A test item",
            user=self.user1,
            sale_price=Decimal("10.00"),
        )
        self.item2 = Item.objects.create(
            name="Test Item 2",
            description="Another test item",
            user=self.user2,
            sale_price=Decimal("15.00"),
        )

    def create_test_image(self):
        """Create a test image file."""
        image = PILImage.new("RGB", (100, 100), color="red")
        temp_file = BytesIO()
        image.save(temp_file, format="JPEG")
        temp_file.seek(0)
        return SimpleUploadedFile(
            name="test_image.jpg", content=temp_file.read(), content_type="image/jpeg"
        )

    def test_create_image_as_item_owner(self):
        """Test that item owner can create images for their item."""
        self.client.force_authenticate(user=self.user1)

        test_image = self.create_test_image()
        data = {"item": str(self.item1.uuid), "original": test_image, "ordering": 1}

        url = reverse("api:image-list")  # Using the image endpoint
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert Image.objects.filter(item=self.item1).exists()

    def test_create_image_as_non_owner_fails(self):
        """Test that non-owner cannot create images for someone else's item."""
        self.client.force_authenticate(user=self.user2)

        test_image = self.create_test_image()
        data = {
            "item": str(self.item1.uuid),  # user2 trying to add image to user1's item
            "original": test_image,
            "ordering": 1,
        }

        url = reverse("api:image-list")  # Using the image endpoint
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "You can only create images for items you own" in str(response.data)
        assert not Image.objects.filter(item=self.item1).exists()

    def test_create_image_unauthenticated_fails(self):
        """Test that unauthenticated users cannot create images."""
        test_image = self.create_test_image()
        data = {"item": str(self.item1.uuid), "original": test_image, "ordering": 1}

        url = reverse("api:image-list")  # Using the image endpoint
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Image.objects.filter(item=self.item1).exists()

    def test_create_multiple_images_as_owner(self):
        """Test that item owner can create multiple images for their item."""
        self.client.force_authenticate(user=self.user1)

        # Create first image
        test_image1 = self.create_test_image()
        data1 = {"item": str(self.item1.uuid), "original": test_image1, "ordering": 1}
        url = reverse("api:image-list")
        response1 = self.client.post(url, data1, format="multipart")
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second image
        test_image2 = self.create_test_image()
        data2 = {"item": str(self.item1.uuid), "original": test_image2, "ordering": 2}
        response2 = self.client.post(url, data2, format="multipart")
        assert response2.status_code == status.HTTP_201_CREATED

        image_count = 2
        assert Image.objects.filter(item=self.item1).count() == image_count

    def test_create_image_with_invalid_item_uuid(self):
        """Test that creating image with invalid item UUID fails."""
        self.client.force_authenticate(user=self.user1)

        test_image = self.create_test_image()
        data = {"item": "invalid-uuid", "original": test_image, "ordering": 1}

        url = reverse("api:image-list")
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
