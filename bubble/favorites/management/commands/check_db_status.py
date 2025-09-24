from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from bubble.favorites.models import Favorite, FavoriteList

User = get_user_model()


class Command(BaseCommand):
    help = "Check database status"

    def handle(self, *args, **options):
        self.stdout.write("Checking database status...")

        users_count = User.objects.count()
        lists_count = FavoriteList.objects.count()
        favorites_count = Favorite.objects.count()

        self.stdout.write(f"Users: {users_count}")
        self.stdout.write(f"Favorite Lists: {lists_count}")
        self.stdout.write(f"Favorites: {favorites_count}")

        if users_count > 0:
            self.stdout.write("\nSample users:")
            for user in User.objects.all()[:5]:
                self.stdout.write(f"  - {user.username}")

        self.stdout.write(self.style.SUCCESS("Database appears to be intact!"))
