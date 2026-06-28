"""Create (or update) an admin superuser non-interactively.

Usage:
    python manage.py seed_admin
    python manage.py seed_admin --email admin@skillmatch.com --password Secret123!
    # or via environment variables:
    ADMIN_EMAIL=... ADMIN_PASSWORD=... python manage.py seed_admin

Defaults to admin@skillmatch.com / Admin@12345 if nothing is provided.
Safe to run repeatedly — it updates the existing account instead of failing.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEFAULT_EMAIL = "admin@skillmatch.com"
DEFAULT_PASSWORD = "Admin@12345"
DEFAULT_NAME = "SkillMatch Admin"


class Command(BaseCommand):
    help = "Create or update the admin superuser used by the /admin panel."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL", DEFAULT_EMAIL))
        parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD", DEFAULT_PASSWORD))
        parser.add_argument("--name", default=os.environ.get("ADMIN_NAME", DEFAULT_NAME))

    def handle(self, *args, **opts):
        email = opts["email"].strip().lower()
        password = opts["password"]
        name = opts["name"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"full_name": name, "role": "admin", "is_staff": True, "is_superuser": True},
        )
        # Always enforce the admin attributes + (re)set the password.
        user.full_name = name or user.full_name
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} admin account:"))
        self.stdout.write(f"  email:    {email}")
        self.stdout.write(f"  password: {password}")
        self.stdout.write(self.style.WARNING("Change this password after first login in production."))
