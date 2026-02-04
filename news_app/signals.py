from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Article
from .functions.notify import notify_on_approval


@receiver(pre_save, sender=Article)
def track_previous_approval(sender, instance: Article, **kwargs):
    """
    Track the previous approved value before saving.

    This allows detection of the approval transition:
    False -> True
    """
    if not instance.pk:
        instance._previous_approved = False
        return

    try:
        prev = Article.objects.get(pk=instance.pk)
        instance._previous_approved = prev.approved
    except Article.DoesNotExist:
        instance._previous_approved = False


@receiver(post_save, sender=Article)
def on_article_saved(sender, instance: Article, created: bool, **kwargs):
    """
    On article save, if approval transitioned from False to True:
    - email subscribers
    - post to X
    """
    prev = getattr(instance, "_previous_approved", False)
    if instance.approved and not prev:
        notify_on_approval(instance)
