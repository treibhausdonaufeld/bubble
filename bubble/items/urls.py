from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    # Main item list
    path("", views.ItemListView.as_view(), name="list"),
    # Item detail
    path("<int:pk>/", views.ItemDetailView.as_view(), name="detail"),
    # Two-step item creation
    path("create/", views.ItemCreateImagesView.as_view(), name="create"),
    # Item CRUD operations (login required)
    path("<int:pk>/edit/", views.ItemUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ItemDeleteView.as_view(), name="delete"),
    # Processing status check
    path(
        "processing-status/<int:pk>/",
        views.check_processing_status,
        name="processing_status",
    ),
    # User's item management
    path("my-items/", views.MyItemsView.as_view(), name="my_items"),
    path("<int:pk>/toggle-status/", views.toggle_item_status, name="toggle_status"),
    # Image management
    path("delete-image/<int:image_id>/", views.delete_image, name="delete_image"),
    # AJAX endpoints
    path("api/subcategories/", views.get_subcategories, name="get_subcategories"),
]
