"""Admin serializers for gallery content management."""

from __future__ import annotations

from rest_framework import serializers

from gallery.models import GalleryCategory, GalleryPhoto


class GalleryPhotoAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryPhoto
        fields = [
            'id',
            'title',
            'description',
            'image',
            'image_url',
            'category',
            'category_name',
            'date_taken',
            'is_featured',
            'is_active',
            'order',
            'created_at',
            'updated_at',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request is not None else url

    def validate_image(self, value):
        from django.conf import settings

        max_size = getattr(settings, 'MAX_IMAGE_UPLOAD_SIZE', 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError('Image file is too large.')

        content_type = getattr(value, 'content_type', '') or ''
        if content_type and not content_type.startswith('image/'):
            raise serializers.ValidationError('Only image uploads are allowed.')
        return value


class GalleryCategoryAdminSerializer(serializers.ModelSerializer):
    photo_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = GalleryCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'color',
            'order',
            'is_active',
            'created_at',
            'photo_count',
        ]


class GalleryCategoryAdminDetailSerializer(GalleryCategoryAdminSerializer):
    photos = GalleryPhotoAdminSerializer(many=True, read_only=True)

    class Meta(GalleryCategoryAdminSerializer.Meta):
        fields = GalleryCategoryAdminSerializer.Meta.fields + ['photos']