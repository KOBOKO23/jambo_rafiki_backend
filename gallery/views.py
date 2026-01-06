# gallery/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import GalleryCategory, GalleryPhoto
from .serializers import (
    GalleryCategorySerializer, 
    GalleryCategoryDetailSerializer,
    GalleryPhotoSerializer
)

class GalleryPhotoPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class GalleryCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryCategory.objects.filter(is_active=True)
    serializer_class = GalleryCategorySerializer
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GalleryCategoryDetailSerializer
        return GalleryCategorySerializer


class GalleryPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryPhoto.objects.filter(is_active=True).select_related('category')
    serializer_class = GalleryPhotoSerializer
    pagination_class = GalleryPhotoPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'date_taken']
    search_fields = ['title', 'description']
    ordering_fields = ['date_taken', 'created_at']
    ordering = ['-date_taken']
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured photos"""
        featured_photos = self.queryset.filter(is_featured=True)[:8]
        serializer = self.get_serializer(featured_photos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """Get random photos for scrolling section"""
        count = int(request.query_params.get('count', 30))
        random_photos = self.queryset.order_by('?')[:count]
        serializer = self.get_serializer(random_photos, many=True)
        return Response(serializer.data)