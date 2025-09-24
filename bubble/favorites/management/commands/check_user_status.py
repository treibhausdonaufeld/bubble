from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Check user status and make superuser if needed"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to check")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)

            self.stdout.write(f"User: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Is superuser: {user.is_superuser}")
            self.stdout.write(f"Is staff: {user.is_staff}")
            self.stdout.write(f"Is active: {user.is_active}")

            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Made {username} a superuser!"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"{username} is already a superuser!")
                )

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
