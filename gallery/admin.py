from django.contrib import admin
from .models import GalleryCategory, GalleryPhoto

class GalleryPhotoInline(admin.TabularInline):
    model = GalleryPhoto
    extra = 1
    fields = ('title', 'image', 'is_featured', 'is_active', 'order', 'date_taken')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order', 'photo_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    inlines = [GalleryPhotoInline]

@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_featured', 'is_active', 'order', 'date_taken', 'created_at')
    list_filter = ('category', 'is_active', 'is_featured', 'date_taken')
    search_fields = ('title', 'description')
    ordering = ('-is_featured', '-date_taken', 'order')
