from django.urls import path

from . import views

# Dynamic content type URLs
# These patterns will be included with a content_type slug prefix
urlpatterns = [
    # Content list by type
    path("", views.ContentListView.as_view(), name="list"),
    # Content detail
    path("<int:pk>/", views.ContentDetailView.as_view(), name="detail"),
]
