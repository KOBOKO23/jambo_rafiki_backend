from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import GalleryCategory, GalleryPhoto


@receiver(post_save, sender=GalleryCategory)
@receiver(post_delete, sender=GalleryCategory)
@receiver(post_save, sender=GalleryPhoto)
@receiver(post_delete, sender=GalleryPhoto)
def invalidate_public_gallery_cache(**kwargs):
    """Invalidate cached gallery responses when public gallery data changes."""
    cache.clear()
