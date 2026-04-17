"""Admin views for gallery content management."""

from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAdminUser

from core.audit import log_audit_event
from gallery.models import GalleryCategory, GalleryPhoto
from gallery.admin_serializers import (
    GalleryCategoryAdminDetailSerializer,
    GalleryCategoryAdminSerializer,
    GalleryPhotoAdminSerializer,
)


class GalleryCategoryAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        queryset = GalleryCategory.objects.annotate(
            photo_count=Count('photos', filter=Q(photos__is_active=True), distinct=True)
        )
        if self.action == 'retrieve':
            return queryset.prefetch_related('photos')
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GalleryCategoryAdminDetailSerializer
        return GalleryCategoryAdminSerializer

    def perform_create(self, serializer):
        category = serializer.save()
        log_audit_event(
            'gallery.category_created',
            actor=self.request.user,
            target=category,
            source='gallery.admin.create_category',
            metadata={'name': category.name, 'slug': category.slug},
        )

    def perform_update(self, serializer):
        category = serializer.save()
        log_audit_event(
            'gallery.category_updated',
            actor=self.request.user,
            target=category,
            source='gallery.admin.update_category',
            metadata={'name': category.name, 'slug': category.slug},
        )

    def perform_destroy(self, instance):
        log_audit_event(
            'gallery.category_deleted',
            actor=self.request.user,
            target=instance,
            source='gallery.admin.delete_category',
            metadata={'name': instance.name, 'slug': instance.slug},
        )
        return super().perform_destroy(instance)


class GalleryPhotoAdminViewSet(viewsets.ModelViewSet):
    queryset = GalleryPhoto.objects.select_related('category').all()
    serializer_class = GalleryPhotoAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name']
    ordering_fields = ['date_taken', 'created_at', 'updated_at', 'order', 'title']
    ordering = ['-is_featured', '-date_taken', 'order']

    def perform_create(self, serializer):
        photo = serializer.save()
        log_audit_event(
            'gallery.photo_created',
            actor=self.request.user,
            target=photo,
            source='gallery.admin.create_photo',
            metadata={'title': photo.title, 'category_id': photo.category_id},
        )

    def perform_update(self, serializer):
        photo = serializer.save()
        log_audit_event(
            'gallery.photo_updated',
            actor=self.request.user,
            target=photo,
            source='gallery.admin.update_photo',
            metadata={'title': photo.title, 'category_id': photo.category_id},
        )

    def perform_destroy(self, instance):
        log_audit_event(
            'gallery.photo_deleted',
            actor=self.request.user,
            target=instance,
            source='gallery.admin.delete_photo',
            metadata={'title': instance.title, 'category_id': instance.category_id},
        )
        return super().perform_destroy(instance)