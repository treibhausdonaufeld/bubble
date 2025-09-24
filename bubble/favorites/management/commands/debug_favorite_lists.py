from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from bubble.favorites.models import Favorite, FavoriteList

User = get_user_model()


class Command(BaseCommand):
    help = "Debug FavoriteList functionality for a specific user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to debug")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
            return

        self.stdout.write(f"Debugging favorite lists for user: {user.username}")

        # Show all lists accessible to user
        accessible_lists = FavoriteList.get_user_accessible_lists(user)
        self.stdout.write(f"\nAccessible lists ({accessible_lists.count()}):")
        for fl in accessible_lists:
            self.stdout.write(f"  - {fl.name} (ID: {fl.id})")
            self.stdout.write(f"    Owner: {fl.user.username}")
            self.stdout.write(f"    Default: {fl.is_default}")
            self.stdout.write(f"    Can edit: {fl.can_edit(user)}")
            self.stdout.write(f"    Can view: {fl.can_view(user)}")

            # Show shared users
            if fl.shared_with.exists():
                shared_users = ", ".join([u.username for u in fl.shared_with.all()])
                self.stdout.write(f"    Shared with: {shared_users}")

            if fl.editors.exists():
                editor_users = ", ".join([u.username for u in fl.editors.all()])
                self.stdout.write(f"    Editors: {editor_users}")

            self.stdout.write(f"    Favorites count: {fl.favorites.count()}")
            self.stdout.write("")

        # Show user's favorites
        favorites = Favorite.objects.filter(user=user)
        self.stdout.write(f"User's favorites ({favorites.count()}):")
        for fav in favorites:
            list_name = fav.favorite_list.name if fav.favorite_list else "No list"
            self.stdout.write(f"  - {fav.title} -> {list_name}")

        self.stdout.write(self.style.SUCCESS("Debug complete!"))
