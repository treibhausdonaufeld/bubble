from django.urls import path

from . import views
from . import views_step

app_name = "items"

urlpatterns = [
    # Main item list
    path("", views.ItemListView.as_view(), name="list"),
    # Item detail
    path("<int:pk>/", views.ItemDetailView.as_view(), name="detail"),
    # Two-step item creation
    path("create/", views_step.ItemCreateStepOneView.as_view(), name="create"),
    path(
        "create/step1/",
        views_step.ItemCreateStepOneView.as_view(),
        name="create_step1",
    ),
    path(
        "create/step2/<int:pk>/",
        views_step.ItemCreateStepTwoView.as_view(),
        name="create_step2",
    ),
    # Item CRUD operations (login required)
    path("<int:pk>/edit/", views.ItemUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ItemDeleteView.as_view(), name="delete"),
    # Draft item management
    path("drafts/", views_step.DraftItemsView.as_view(), name="drafts"),
    path("drafts/<int:pk>/delete/", views_step.delete_draft_item, name="delete_draft"),
    # Processing status check
    path(
        "processing-status/<int:pk>/",
        views_step.check_processing_status,
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
