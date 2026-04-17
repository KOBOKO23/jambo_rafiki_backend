# gallery/serializers.py
from rest_framework import serializers
from django.conf import settings
from .models import GalleryCategory, GalleryPhoto

class GalleryPhotoSerializer(serializers.ModelSerializer):
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
            'created_at'
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def validate_image(self, value):
        max_size = getattr(settings, 'MAX_IMAGE_UPLOAD_SIZE', 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError('Image file is too large.')

        content_type = getattr(value, 'content_type', '') or ''
        if content_type and not content_type.startswith('image/'):
            raise serializers.ValidationError('Only image uploads are allowed.')
        return value


class GalleryCategorySerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = GalleryCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'color',
            'count'
        ]


class GalleryCategoryDetailSerializer(serializers.ModelSerializer):
    photos = GalleryPhotoSerializer(many=True, read_only=True)
    count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = GalleryCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'color',
            'count',
            'photos'
        ]