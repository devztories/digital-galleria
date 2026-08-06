import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update a production admin account"

    def handle(self, *args, **options):

        User = get_user_model()

        # Get admin details from Render Environment Variables
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        # Make sure required values exist
        if not username or not password:
            self.stdout.write(
                self.style.ERROR(
                    "ADMIN_USERNAME and ADMIN_PASSWORD are required."
                )
            )
            return

        # Find existing user or create a new one
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
            }
        )

        # Make the user an admin
        user.email = email
        user.is_staff = True
        user.is_superuser = True

        # Securely hash and save password
        user.set_password(password)

        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Production admin created successfully."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Production admin updated successfully."
                )
            )