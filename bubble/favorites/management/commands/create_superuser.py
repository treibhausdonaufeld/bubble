from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser programmatically'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the superuser')
        parser.add_argument('email', type=str, help='Email for the superuser')
        parser.add_argument('password', type=str, help='Password for the superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            return
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superuser {username} created successfully!')
        )