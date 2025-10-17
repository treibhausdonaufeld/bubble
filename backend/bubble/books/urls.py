from rest_framework.routers import SimpleRouter

from .api.views import (
    AuthorViewSet,
    BookViewSet,
    GenreViewSet,
    PublisherViewSet,
    ShelfViewSet,
)

router = SimpleRouter()

router.register("books", BookViewSet, basename="book")
router.register("authors", AuthorViewSet, basename="author")
router.register("genres", GenreViewSet, basename="genre")
router.register("publishers", PublisherViewSet, basename="publisher")
router.register("shelves", ShelfViewSet, basename="shelf")

urlpatterns = router.urls
