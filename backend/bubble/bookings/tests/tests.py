"""Tests for booking API endpoints and auto-confirmation logic."""

from datetime import timedelta

from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from bubble.bookings.models import Booking, BookingStatus
from bubble.bookings.tests.factories import (
    BookingFactory,
    ItemFactory,
    SelfServiceItemFactory,
)
from bubble.core.permissions_config import DefaultGroup
from bubble.users.tests.factories import UserFactory


class BookingAutoConfirmTestCase(APITestCase):
    """Test auto-confirmation of bookings for self-service items."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create default group
        self.default_group, _ = Group.objects.get_or_create(name=DefaultGroup.DEFAULT)

        # Create users
        self.item_owner = UserFactory()
        self.item_owner.groups.add(self.default_group)

        self.booking_user = UserFactory()
        self.booking_user.groups.add(self.default_group)

        # Create items
        self.regular_item = ItemFactory(user=self.item_owner, rental_self_service=False)
        self.self_service_item = SelfServiceItemFactory(user=self.item_owner)

    def test_booking_regular_item_stays_pending(self):
        """Test booking regular item stays in PENDING status."""
        self.client.force_authenticate(user=self.booking_user)

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.regular_item.uuid),
                "offer": "20.00",
                "time_to": timezone.now() + timedelta(days=1),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == BookingStatus.PENDING

        # Verify in database
        booking = Booking.objects.get(uuid=response.data["uuid"])
        assert booking.status == BookingStatus.PENDING

    def test_booking_self_service_item_auto_confirms(self):
        """Test booking self-service item gets CONFIRMED status."""
        self.client.force_authenticate(user=self.booking_user)

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.self_service_item.uuid),
                "offer": "15.00",
                "time_to": timezone.now() + timedelta(days=1),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == BookingStatus.CONFIRMED

        # Verify in database
        booking = Booking.objects.get(uuid=response.data["uuid"])
        assert booking.status == BookingStatus.CONFIRMED

    def test_self_service_booking_visible_in_public_endpoint(self):
        """Test auto-confirmed booking appears in public endpoint."""
        self.client.force_authenticate(user=self.booking_user)

        # Create a self-service booking
        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.self_service_item.uuid),
                "offer": "15.00",
                "time_to": timezone.now() + timedelta(days=1),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        booking_uuid = response.data["uuid"]

        # Check it appears in public bookings list
        response = self.client.get("/api/public-bookings/")
        assert response.status_code == status.HTTP_200_OK

        booking_uuids = [b["uuid"] for b in response.data["results"]]
        assert booking_uuid in booking_uuids

    def test_pending_booking_not_visible_in_public_endpoint(self):
        """Test PENDING bookings don't appear in public endpoint."""
        self.client.force_authenticate(user=self.booking_user)

        # Create a regular (pending) booking
        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.regular_item.uuid),
                "offer": "20.00",
                "time_to": timezone.now() + timedelta(days=1),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        booking_uuid = response.data["uuid"]
        assert response.data["status"] == BookingStatus.PENDING

        # Check it does NOT appear in public bookings list
        response = self.client.get("/api/public-bookings/")
        assert response.status_code == status.HTTP_200_OK

        booking_uuids = [b["uuid"] for b in response.data["results"]]
        assert booking_uuid not in booking_uuids

    def test_booking_no_open_ended_without_time_to_fails(self):
        """Test booking without time_to fails when open-ended not allowed."""
        self.client.force_authenticate(user=self.booking_user)

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.regular_item.uuid),
                "offer": "20.00",
                # Intentionally not providing time_to
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "time_to" in response.data
        assert "required" in response.data["time_to"][0].lower()


class PublicBookingViewSetTestCase(APITestCase):
    """Test PublicBookingViewSet functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create default group
        self.default_group, _ = Group.objects.get_or_create(name=DefaultGroup.DEFAULT)

        # Create users
        self.user = UserFactory()
        self.user.groups.add(self.default_group)

        # Create item
        self.item = ItemFactory(user=self.user)

        # Create bookings with different statuses
        self.pending_booking = BookingFactory(
            user=self.user, item=self.item, status=BookingStatus.PENDING
        )
        self.confirmed_booking = BookingFactory(
            user=self.user, item=self.item, status=BookingStatus.CONFIRMED
        )
        self.cancelled_booking = BookingFactory(
            user=self.user, item=self.item, status=BookingStatus.CANCELLED
        )
        self.completed_booking = BookingFactory(
            user=self.user, item=self.item, status=BookingStatus.COMPLETED
        )

    def test_public_bookings_list_only_confirmed(self):
        """Test public bookings endpoint only returns CONFIRMED bookings."""
        response = self.client.get("/api/public-bookings/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["uuid"] == str(self.confirmed_booking.uuid)

    def test_public_bookings_detail_confirmed(self):
        """Test confirmed booking detail is accessible."""
        response = self.client.get(
            f"/api/public-bookings/{self.confirmed_booking.uuid}/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["uuid"] == str(self.confirmed_booking.uuid)
        assert response.data["status"] == BookingStatus.CONFIRMED

    def test_public_bookings_detail_pending_not_found(self):
        """Test pending booking not accessible via public endpoint."""
        response = self.client.get(f"/api/public-bookings/{self.pending_booking.uuid}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_public_bookings_readonly(self):
        """Test public bookings endpoint is read-only."""
        self.client.force_authenticate(user=self.user)

        # Try to create
        response = self.client.post(
            "/api/public-bookings/",
            {"item": str(self.item.uuid), "offer": "10.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Try to update
        response = self.client.patch(
            f"/api/public-bookings/{self.confirmed_booking.uuid}/",
            {"status": BookingStatus.CANCELLED},
            format="json",
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Try to delete
        response = self.client.delete(
            f"/api/public-bookings/{self.confirmed_booking.uuid}/"
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_public_bookings_unauthenticated_access(self):
        """Test unauthenticated users can view public bookings."""
        # Don't authenticate
        response = self.client.get("/api/public-bookings/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_public_bookings_filter_by_item(self):
        """Test filtering public bookings by item UUID."""
        # Create another item and confirmed booking
        item2 = ItemFactory(user=self.user)
        booking2 = BookingFactory(
            user=self.user, item=item2, status=BookingStatus.CONFIRMED
        )

        # Filter by first item
        response = self.client.get(f"/api/public-bookings/?item={self.item.uuid}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["uuid"] == str(self.confirmed_booking.uuid)

        # Filter by second item
        response = self.client.get(f"/api/public-bookings/?item={item2.uuid}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["uuid"] == str(booking2.uuid)


class BookingTimeToValidationTestCase(APITestCase):
    """Test validation for time_to field based on item's rental_open_end setting."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create default group
        self.default_group, _ = Group.objects.get_or_create(name=DefaultGroup.DEFAULT)

        # Create users
        self.item_owner = UserFactory()
        self.item_owner.groups.add(self.default_group)

        self.booking_user = UserFactory()
        self.booking_user.groups.add(self.default_group)

        # Create items with different rental_open_end settings
        self.item_requires_end_time = ItemFactory(
            user=self.item_owner,
            rental_self_service=True,
            rental_open_end=False,
            rental_price="10.00",
        )
        self.item_allows_open_end = ItemFactory(
            user=self.item_owner,
            rental_self_service=True,
            rental_open_end=True,
            rental_price="15.00",
        )

    def test_booking_without_time_to_fails_when_open_end_not_allowed(self):
        """Test booking without time_to fails when open-ended not allowed."""
        self.client.force_authenticate(user=self.booking_user)

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.item_requires_end_time.uuid),
                "offer": "20.00",
                # Intentionally not providing time_to
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "time_to" in response.data
        assert "required" in response.data["time_to"][0].lower()

    def test_booking_without_time_to_succeeds_when_open_end_allowed(self):
        """Test booking without time_to succeeds when open-ended allowed."""
        self.client.force_authenticate(user=self.booking_user)

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.item_allows_open_end.uuid),
                "offer": "25.00",
                # Intentionally not providing time_to
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["time_to"] is None

        # Verify in database
        booking = Booking.objects.get(uuid=response.data["uuid"])
        assert booking.time_to is None

    def test_booking_with_time_to_succeeds_regardless_of_open_end_setting(self):
        """Test providing time_to succeeds regardless of rental_open_end."""
        self.client.force_authenticate(user=self.booking_user)

        # Test with item that requires end time
        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.item_requires_end_time.uuid),
                "offer": "20.00",
                "time_to": "2025-12-31T23:59:59Z",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["time_to"] is not None

        # Test with item that allows open end (but we're still providing time_to)
        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(self.item_allows_open_end.uuid),
                "offer": "25.00",
                "time_to": "2025-12-31T23:59:59Z",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["time_to"] is not None

    def test_booking_sale_item_without_time_to_succeeds(self):
        """Sale-only items should be bookable without a time_to value."""
        self.client.force_authenticate(user=self.booking_user)

        # Create a sale-only item (no rental price)
        sale_item = ItemFactory(
            user=self.item_owner,
            sale_price="100.00",
            rental_price=None,
            rental_self_service=False,
        )

        response = self.client.post(
            "/api/bookings/",
            {
                "item": str(sale_item.uuid),
                "offer": "100.00",
                # No time_to provided
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["time_to"] is None

        # Verify in database
        booking = Booking.objects.get(uuid=response.data["uuid"])
        assert booking.time_to is None
