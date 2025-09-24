"""
URL patterns for books app.
"""
from django.urls import path

from . import views

app_name = "books"

urlpatterns = [
    # Main book list
    path("", views.BookListView.as_view(), name="list"),
    # Book detail
    path("<int:pk>/", views.BookDetailView.as_view(), name="detail"),
    # Book CRUD operations (login required)
    path("create/", views.BookCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.BookUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.BookDeleteView.as_view(), name="delete"),
    # User's book management
    path("my-books/", views.MyBooksView.as_view(), name="my_books"),
    # Search API endpoint
    path("api/search/", views.BookSearchAPIView.as_view(), name="search_api"),
]