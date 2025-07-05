from django.urls import path

from .views import TagCreateView
from .views import TagDeleteView
from .views import TagDetailView
from .views import TagListView
from .views import TagUpdateView

app_name = "tags"

urlpatterns = [
    path("", TagListView.as_view(), name="list"),
    path("create/", TagCreateView.as_view(), name="create"),
    path("<int:pk>/", TagDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TagUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", TagDeleteView.as_view(), name="delete"),
]
