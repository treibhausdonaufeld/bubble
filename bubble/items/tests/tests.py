"""Tests for items API."""

# mypy: ignore-errors

from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage
from rest_framework import status
from rest_framework.test import APIClient

from bubble.items.models import Image, Item
from bubble.items.tests.factories import ItemOwnerUserFactory

TEST_PASSWORD = "testpass123"  # noqa: S105


class ImageAPITestCase(TestCase):
    """Test cases for Image API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test users with item permissions
        self.user1 = ItemOwnerUserFactory(
            username="testuser1", email="test1@example.com", password=TEST_PASSWORD
        )
        self.user2 = ItemOwnerUserFactory(
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
        self.client.login(username="testuser1", password=TEST_PASSWORD)

        test_image = self.create_test_image()
        data = {"item": str(self.item1.uuid), "original": test_image, "ordering": 1}

        url = reverse("api:image-list")  # Using the image endpoint
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED, response.status_code
        assert Image.objects.filter(item=self.item1).exists()

    def test_create_image_as_non_owner_fails(self):
        """Test that non-owner cannot create images for someone else's item."""
        self.client.login(username="testuser2", password=TEST_PASSWORD)

        test_image = self.create_test_image()
        data = {
            "item": str(self.item1.uuid),  # user2 trying to add image to user1's item
            "original": test_image,
            "ordering": 1,
        }

        url = reverse("api:image-list")  # Using the image endpoint
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "You can only create images for items you own" in str(response.json())
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
        self.client.login(username="testuser1", password=TEST_PASSWORD)

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
        self.client.login(username="testuser1", password=TEST_PASSWORD)

        test_image = self.create_test_image()
        data = {"item": "invalid-uuid", "original": test_image, "ordering": 1}

        url = reverse("api:image-list")
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class ItemFilterAPITestCase(TestCase):
    """Tests for ItemViewSet filtering functionality."""

    def setUp(self):
        self.user = ItemOwnerUserFactory(
            username="filteruser", email="filter@example.com", password=TEST_PASSWORD
        )
        self.other = ItemOwnerUserFactory(
            username="otheruser", email="other@example.com", password=TEST_PASSWORD
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create items with varying attributes
        self.item_draft = Item.objects.create(
            name="Draft Hammer",
            description="A strong hammer",
            user=self.user,
            sale_price=Decimal("5.00"),
            status=1,  # assuming DRAFT
            category="TOOLS",
        )
        self.item_available = Item.objects.create(
            name="Available Saw",
            description="Sharp saw",
            user=self.user,
            sale_price=Decimal("15.00"),
            rental_price=Decimal("3.00"),
            status=2,  # AVAILABLE
            category="TOOLS",
        )
        self.item_deactivated = Item.objects.create(
            name="Hidden Screwdriver",
            description="Small screwdriver",
            user=self.other,
            sale_price=Decimal("7.00"),
            status=3,  # some other status
            category="HARDWARE",
        )

    def test_filter_by_status_multiple_params(self):
        # Test the recommended way with multiple status parameters
        url = reverse("api:item-list") + "?status=1&status=2"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = {i["name"] for i in response.json()["results"]}
        assert {self.item_draft.name, self.item_available.name}.issubset(names)

    def test_filter_published_true(self):
        # Published filter should include items with published statuses only
        url = reverse("api:item-list") + "?published=true"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = {i["name"] for i in response.json()["results"]}
        assert self.item_available.name in names

    def test_filter_price_range(self):
        url = reverse("api:item-list") + "?min_sale_price=6&max_sale_price=10"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = {i["name"] for i in response.json()["results"]}
        assert self.item_draft.name not in names  # price 5 excluded
        assert self.item_deactivated.name in names  # price 7 within range

    def test_filter_search(self):
        url = reverse("api:item-list") + "?search=saw"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = {i["name"] for i in response.json()["results"]}
        assert self.item_available.name in names
        assert self.item_draft.name not in names

    def test_filter_owner(self):
        url = reverse("api:item-list") + f"?user={self.user.pk}"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        owners = {i["name"] for i in response.json()["results"]}
        assert self.item_deactivated.name not in owners
        assert self.item_available.name in owners


class ItemOwnerUserFactoryTestCase(TestCase):
    """Test cases for ItemOwnerUserFactory."""

    def test_item_owner_user_factory_creates_user_with_group(self):
        """Test that ItemOwnerUserFactory creates a user in the Item Owners group."""
        user = ItemOwnerUserFactory()

        assert user.groups.filter(name="Item Owners").exists()
        assert user.username is not None
        assert user.email is not None

    def test_item_owner_user_factory_with_password(self):
        """Test that ItemOwnerUserFactory creates a user with a custom password."""
        password = TEST_PASSWORD  # Use the existing test password constant
        user = ItemOwnerUserFactory(password=password)

        assert user.check_password(password)
        assert user.groups.filter(name="Item Owners").exists()
