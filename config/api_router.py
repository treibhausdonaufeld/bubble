from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from bubble.items.api.views import CategoryViewSet, ImageViewSet, ItemViewSet
from bubble.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("categories", CategoryViewSet, basename="category")
router.register("items", ItemViewSet, basename="item")
router.register("images", ImageViewSet, basename="image")


app_name = "api"
urlpatterns = router.urls
