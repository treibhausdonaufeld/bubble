from django.urls import path

from . import views

# Dynamic content type URLs
# These patterns will be included with a content_type slug prefix
urlpatterns = [
    # Content list by type
    path("", views.ContentListView.as_view(), name="list"),
    # Content detail
    path("<int:pk>/", views.ContentDetailView.as_view(), name="detail"),
    # Content CRUD operations (login required)
    path("create/", views.ContentCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.ContentUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ContentDeleteView.as_view(), name="delete"),
    # User's content management
    path("my-items/", views.MyContentView.as_view(), name="my_items"),
    path("<int:pk>/toggle-status/", views.toggle_content_status, name="toggle_status"),
    # Image management
    path("delete-image/<int:image_id>/", views.delete_image, name="delete_image"),
    # AJAX endpoints
    path("api/subcategories/", views.get_subcategories, name="get_subcategories"),
]
