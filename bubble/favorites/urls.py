from django.urls import path

from .views import DeleteFavoriteView
from .views import ToggleFavoriteView
from .views import UserFavoritesView

app_name = "favorites"
urlpatterns = [
    path("toggle/", ToggleFavoriteView.as_view(), name="toggle"),
    path("delete/<int:pk>/", DeleteFavoriteView.as_view(), name="delete"),
    path("user/<str:username>/", UserFavoritesView.as_view(), name="user_list"),
]
