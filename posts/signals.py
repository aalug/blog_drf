"""
Signals for the posts' app.
"""
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from core.models import Post, Vote


@receiver(pre_delete, sender=Post)
def delete_related_tags(sender, instance, **kwargs):
    """Delete tags related to the post if they are not used
       by any other post."""
    for tag in instance.tags.all():
        # if length is 1, that means that this tag is
        # connected only to this one post that is being deleted
        if len(tag.post_set.all()) == 1:
            tag.delete()


@receiver(post_save, sender=Vote)
def calculate_user_points_add_vote(sender, instance, **kwargs):
    """After saving a vote, calculate points of the user
       whose comment received a vote."""
    comment_author_profile = instance.comment.author.user_profile

    if instance.vote_type == Vote.UPVOTE:
        comment_author_profile.points += 1
    else:
        comment_author_profile.points -= 1

    comment_author_profile.save()


@receiver(pre_delete, sender=Vote)
def calculate_user_points_delete_vote(sender, instance, **kwargs):
    """Before deleting a vote, calculate points of the user
       that has previously received a vote."""
    comment_author_profile = instance.comment.author.user_profile
    if instance.vote_type == Vote.UPVOTE:
        # Upvote is being deleted, subtract 1 point
        # that was previously added
        comment_author_profile.points -= 1
    else:
        # Downvote is being deleted, add 1 point
        # that was previously subtracted
        comment_author_profile.points += 1

    comment_author_profile.save()
