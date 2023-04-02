"""
Django command to create fake tags and populate the database with them.
"""
from faker import Faker
from django.core.management import BaseCommand


from core.models import Tag


class Command(BaseCommand):
    """Django command to populate the database with tags."""

    def handle(self, *args, **options):
        for _ in range(30):
            fake = Faker()
            name = fake.word()
            tag = Tag.objects.create(name=name)
            tag.save()