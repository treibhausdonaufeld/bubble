from django.urls import path

from .views import (
    CheckFavoriteStatusView,
    DeleteFavoriteView,
    FavoriteListCreateView,
    FavoriteListDeleteView,
    FavoriteListDetailView,
    FavoriteListListView,
    FavoriteListUpdateView,
    GetUserFavoriteListsView,
    ManageFavoriteView,
    ManualFavoriteCreateView,
    ToggleFavoriteView,
    UserFavoritesView,
)

app_name = "favorites"
urlpatterns = [
    # Existing favorites URLs
    path("check/", CheckFavoriteStatusView.as_view(), name="check"),
    path("toggle/", ToggleFavoriteView.as_view(), name="toggle"),
    path("delete/<int:pk>/", DeleteFavoriteView.as_view(), name="delete"),
    path("user/<str:username>/", UserFavoritesView.as_view(), name="user_list"),
    path("create/", ManualFavoriteCreateView.as_view(), name="create_manual"),
    path("manage/", ManageFavoriteView.as_view(), name="manage"),
    # FavoriteList URLs
    path("lists/", FavoriteListListView.as_view(), name="list_list"),
    path("lists/create/", FavoriteListCreateView.as_view(), name="list_create"),
    path("lists/<int:pk>/", FavoriteListDetailView.as_view(), name="list_detail"),
    path("lists/<int:pk>/edit/", FavoriteListUpdateView.as_view(), name="list_edit"),
    path(
        "lists/<int:pk>/delete/", FavoriteListDeleteView.as_view(), name="list_delete"
    ),
    # AJAX URLs
    path("api/user-lists/", GetUserFavoriteListsView.as_view(), name="api_user_lists"),
]
