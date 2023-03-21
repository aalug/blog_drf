"""
Signals for the posts' app.
"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from core.models import Post


@receiver(pre_delete, sender=Post)
def delete_related_tags(sender, instance, **kwargs):
    """Delete tags related to the post if they are not used
       by any other post."""
    for tag in instance.tags.all():
        # if length is 1, that means that this tag is
        # connected only to this one post that is being deleted
        if len(tag.post_set.all()) == 1:
            tag.delete()
