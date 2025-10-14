from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from bubble.books.api.views import BookViewSet
from bubble.books.models import Book

User = get_user_model()


@pytest.mark.django_db
class TestBookViewSetISBNUpdate:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            password="test12345",  # noqa: S106
        )
        self.book = Book.objects.create(
            name="Test Book", isbn="9780980200447", user=self.user
        )
        self.view = BookViewSet.as_view({"post": "isbn_update"})
        self.url = f"/api/books/{self.book.uuid}/isbn_update/"

    @patch("bubble.books.services.OpenLibraryService.update_book_from_isbn")
    def test_isbn_update_success(self, mock_update):
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_200_OK
        mock_update.assert_called_once_with(self.book, isbn=None)

    def test_isbn_update_no_isbn(self):
        self.book.isbn = ""
        self.book.save()
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["error"]
            == "Book does not have an ISBN and none was provided."
        )

    @patch("bubble.books.services.OpenLibraryService.update_book_from_isbn")
    def test_isbn_update_service_error(self, mock_update):
        mock_update.side_effect = Exception("Service unavailable")
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request, uuid=str(self.book.uuid))

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Failed to fetch data" in response.data["error"]
