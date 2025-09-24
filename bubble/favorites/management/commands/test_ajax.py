import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from bubble.favorites.views import GetUserFavoriteListsView

User = get_user_model()


class Command(BaseCommand):
    help = "Test the AJAX endpoint for getting user favorite lists"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to test")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
            return

        # Create a fake request
        factory = RequestFactory()
        request = factory.get("/favorites/api/user-lists/")
        request.user = user

        # Test the view
        view = GetUserFavoriteListsView()
        response = view.get(request)

        self.stdout.write(f"Response status: {response.status_code}")

        # Parse the JSON response
        data = json.loads(response.content)
        self.stdout.write(f"Response data: {json.dumps(data, indent=2)}")

        self.stdout.write(self.style.SUCCESS("AJAX test complete!"))
