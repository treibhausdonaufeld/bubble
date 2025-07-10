from django.urls import path

from .views import RoomDetailView, RoomListView

app_name = "rooms"

urlpatterns = [
    path("", RoomListView.as_view(), name="list"),
    path("<int:pk>/", RoomDetailView.as_view(), name="detail"),
]
