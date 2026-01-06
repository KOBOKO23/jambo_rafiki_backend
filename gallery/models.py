# gallery/models.py
from django.db import models
from django.utils.text import slugify

class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='Users')  # Lucide icon name
    color = models.CharField(max_length=100, default='from-pink-500 to-rose-500')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Gallery Categories"
        ordering = ['order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def photo_count(self):
        return self.photos.filter(is_active=True).count()


class GalleryPhoto(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/%Y/%m/')
    category = models.ForeignKey(
        GalleryCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='photos'
    )
    date_taken = models.DateField()
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Gallery Photos"
        ordering = ['-is_featured', '-date_taken', 'order']
    
    def __str__(self):
        return self.title