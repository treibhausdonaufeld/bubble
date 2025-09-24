from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from bubble.favorites.models import FavoriteList

User = get_user_model()


class Command(BaseCommand):
    help = "Create a test favorite list for debugging"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to create list for")
        parser.add_argument(
            "--name", type=str, default="Test List", help="Name of the list"
        )

    def handle(self, *args, **options):
        username = options["username"]
        list_name = options["name"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
            return

        # Create a test list
        test_list = FavoriteList.objects.create(
            name=list_name, user=user, is_default=False
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Created test list "{list_name}" (ID: {test_list.id}) for user {username}'
            )
        )
