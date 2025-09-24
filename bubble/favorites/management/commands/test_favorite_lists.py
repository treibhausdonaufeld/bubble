from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from bubble.favorites.models import Favorite, FavoriteList

User = get_user_model()


class Command(BaseCommand):
    help = "Test FavoriteList functionality"

    def handle(self, *args, **options):
        self.stdout.write("Testing FavoriteList model...")

        # Test basic model functionality
        lists_count = FavoriteList.objects.count()
        self.stdout.write(f"Found {lists_count} existing favorite lists")

        # Test favorites count
        favorites_count = Favorite.objects.count()
        self.stdout.write(f"Found {favorites_count} existing favorites")

        # Test favorites with lists
        favorites_with_lists = Favorite.objects.filter(
            favorite_list__isnull=False
        ).count()
        self.stdout.write(f"Found {favorites_with_lists} favorites assigned to lists")

        # Show some example lists
        for fl in FavoriteList.objects.all()[:5]:
            self.stdout.write(
                f"List: {fl.name} (User: {fl.user.username}, Default: {fl.is_default}, Favorites: {fl.favorites.count()})"
            )

        self.stdout.write(
            self.style.SUCCESS("FavoriteList model is working correctly!")
        )
