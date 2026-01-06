# gallery/serializers.py
from rest_framework import serializers
from .models import GalleryCategory, GalleryPhoto

class GalleryPhotoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = GalleryPhoto
        fields = [
            'id', 
            'title', 
            'description', 
            'image', 
            'category', 
            'category_name',
            'date_taken', 
            'is_featured',
            'created_at'
        ]


class GalleryCategorySerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='photo_count', read_only=True)
    
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
    count = serializers.IntegerField(source='photo_count', read_only=True)
    
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