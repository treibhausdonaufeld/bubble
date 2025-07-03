"""Management command to create authentication tokens for users."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

User = get_user_model()


class Command(BaseCommand):
    help = "Create authentication token for a user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to create token for")
        parser.add_argument(
            "--regenerate",
            action="store_true",
            help="Regenerate token if it already exists",
        )

    def handle(self, *args, **options):
        username = options["username"]
        regenerate = options["regenerate"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        if regenerate:
            # Delete existing token if it exists
            Token.objects.filter(user=user).delete()

        token, created = Token.objects.get_or_create(user=user)

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Token created for user "{username}": {token.key}'),
            )
        elif regenerate:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Token regenerated for user "{username}": {token.key}',
                ),
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Token already exists for user "{username}": {token.key}',
                ),
            )
            self.stdout.write(
                self.style.WARNING("Use --regenerate to create a new token"),
            )
