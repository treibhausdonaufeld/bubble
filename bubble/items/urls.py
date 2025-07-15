from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    # Main item list
    path("", views.ItemListView.as_view(), name="list"),
    # AI-powered similarity search
    path("search/", views.ItemSimilaritySearchView.as_view(), name="search"),
    # Search status endpoints
    path(
        "search-status/<str:search_id>/",
        views.check_search_status,
        name="search_status",
    ),
    path(
        "search-results/<str:search_id>/",
        views.get_search_results,
        name="search_results",
    ),
    path(
        "check-active-searches/",
        views.check_active_searches,
        name="check_active_searches",
    ),
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
    # Publishing status check
    path(
        "publishing-status/<int:pk>/",
        views.check_publishing_status,
        name="publishing_status",
    ),
    # Debug publishing status
    path(
        "debug-publishing/<int:pk>/",
        views.debug_publishing_status,
        name="debug_publishing",
    ),
    # Cancel processing
    path(
        "cancel-processing/<int:pk>/",
        views.cancel_processing,
        name="cancel_processing",
    ),
    # Retrigger processing
    path(
        "retrigger-processing/<int:pk>/",
        views.retrigger_processing,
        name="retrigger_processing",
    ),
    # User's item management
    path("my-items/", views.MyItemsView.as_view(), name="my_items"),
    path("<int:pk>/toggle-status/", views.toggle_item_status, name="toggle_status"),
    # Image management
    path("delete-image/<int:image_id>/", views.delete_image, name="delete_image"),
    # API endpoints
    path(
        "api/similarity-search/",
        views.api_similarity_search,
        name="api_similarity_search",
    ),
]
