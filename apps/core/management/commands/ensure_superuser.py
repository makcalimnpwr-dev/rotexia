import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from env vars if it doesn't exist (safe to run repeatedly)."

    def handle(self, *args, **options):
        username = (os.getenv("DJANGO_SUPERUSER_USERNAME") or "").strip()
        email = (os.getenv("DJANGO_SUPERUSER_EMAIL") or "").strip()
        password = (os.getenv("DJANGO_SUPERUSER_PASSWORD") or "").strip()

        # If not configured, do nothing (success)
        if not username or not password:
            self.stdout.write("ensure_superuser: env not set; skipping.")
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user:
            # ensure it is superuser/staff
            changed = False
            if not getattr(user, "is_superuser", False):
                user.is_superuser = True
                changed = True
            if not getattr(user, "is_staff", False):
                user.is_staff = True
                changed = True
            if email and getattr(user, "email", "") != email:
                user.email = email
                changed = True
            if changed:
                user.save()
                self.stdout.write(f"ensure_superuser: updated existing user '{username}'.")
            else:
                self.stdout.write(f"ensure_superuser: user '{username}' already exists.")
            return

        user = User.objects.create_superuser(username=username, email=email or None, password=password)
        self.stdout.write(f"ensure_superuser: created superuser '{user.username}'.")









