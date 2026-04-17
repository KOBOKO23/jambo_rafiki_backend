from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Child, Sponsorship


@receiver(post_save, sender=Child)
@receiver(post_delete, sender=Child)
@receiver(post_save, sender=Sponsorship)
@receiver(post_delete, sender=Sponsorship)
def invalidate_public_sponsorship_cache(**kwargs):
    """Invalidate cached sponsorship/child public responses after writes."""
    cache.clear()
