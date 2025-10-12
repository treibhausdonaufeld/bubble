from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from bubble.bookings.urls import router as bookings_router
from bubble.books.urls import router as books_router
from bubble.items.urls import router as items_router
from bubble.users.api.views import ProfileViewSet, UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("profiles", ProfileViewSet, basename="profile")

router.registry.extend(items_router.registry)
router.registry.extend(bookings_router.registry)
router.registry.extend(books_router.registry)

app_name = "api"
urlpatterns = router.urls
