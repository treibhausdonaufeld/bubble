from rest_framework.routers import SimpleRouter

from .api.views import ImageViewSet, ItemViewSet

router = SimpleRouter()

router.register("items", ItemViewSet, basename="item")
router.register("images", ImageViewSet, basename="image")

urlpatterns = router.urls
