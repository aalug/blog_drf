"""
Django command to create fake posts and populate the database with them.
"""
import random
import requests

from io import BytesIO
from PIL import Image
from faker import Faker

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from core.models import Post, Tag


class Command(BaseCommand):
    """Django command to populate the database with posts."""

    def handle(self, *args, **options):
        email = 'admin1@example.com'
        author = get_user_model().objects.filter(email=email).first()
        if not author:
            author = get_user_model().objects.create_superuser(
                email=email,
                password='admin123',
                username='admin1'
            )
        for _ in range(30):
            fake = Faker()
            title = fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None)
            slug = slugify(title)
            description = fake.text(max_nb_chars=200)
            body = fake.text(max_nb_chars=1000)

            # Get an image
            img_url = fake.image_url()
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))

            # Convert the image to JPEG format
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            cover_image = SimpleUploadedFile(
                name='image.jpg',
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )

            tags = Tag.objects.all().order_by('?')[:random.randint(1, 5)]
            post = Post.objects.create(
                title=title,
                slug=slug,
                author=author,
                description=description,
                body=body,
                cover_image=cover_image,
            )
            post.tags.set(tags)
            post.save()
