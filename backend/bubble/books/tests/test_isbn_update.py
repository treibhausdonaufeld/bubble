from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from bubble.books.api.views import BookViewSet
from bubble.books.models import Book
from bubble.core.permissions_config import DefaultGroup

User = get_user_model()


@pytest.mark.django_db
class TestBookViewSetISBNUpdate:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(  # pyright: ignore[reportAttributeAccessIssue]
            username="testuser",
            password="test12345",  # noqa: S106
        )
        # add user to default group to have permissions
        self.user.groups.add(Group.objects.get(name=DefaultGroup.DEFAULT))  # pyright: ignore[reportAttributeAccessIssue
        self.book = Book.objects.create(name="Test Book", user=self.user)
        self.view = BookViewSet.as_view({"put": "isbn_update"})
        self.url = f"/api/books/{self.book.uuid}/isbn_update/"

    @patch("bubble.books.services.isbnlib.cover")
    @patch("bubble.books.services.isbnlib.meta")
    @patch("bubble.books.services.isbnlib.canonical")
    def test_isbn_update_success(self, mock_canonical, mock_meta, mock_cover):
        mock_canonical.return_value = "9780980200447"
        mock_meta.return_value = {
            "Title": "Updated Book Title",
            "Authors": ["Test Author"],
            "Publisher": "Test Publisher",
            "Year": "2020",
            "ISBN-13": "9780980200447",
            "Language": "en",
        }
        mock_cover.return_value = {}

        request = self.factory.put(self.url, {"isbn": "9780-980200447"})
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        self.book.refresh_from_db()
        assert self.book.name == "Updated Book Title"
        assert self.book.isbn == "9780980200447"
        assert response.status_code == status.HTTP_200_OK
        mock_meta.assert_called_once_with("9780980200447", service="default")

    def test_isbn_update_no_isbn(self):
        self.book.isbn = ""
        self.book.save()
        request = self.factory.put(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["error"]
            == "Book does not have an ISBN and none was provided."
        )

    @patch("bubble.books.services.isbnlib.canonical")
    def test_isbn_update_invalid_isbn(self, mock_canonical):
        mock_canonical.return_value = None
        request = self.factory.put(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "Book does not have an ISBN and none was provided."
        }

    @patch("bubble.books.services.isbnlib.meta")
    @patch("bubble.books.services.isbnlib.canonical")
    def test_isbn_update_metadata_not_found(self, mock_canonical, mock_meta):
        mock_canonical.return_value = "9780980200447"
        mock_meta.return_value = None

        request = self.factory.put(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "Book does not have an ISBN and none was provided."
        }
