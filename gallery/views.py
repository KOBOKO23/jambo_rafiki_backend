# gallery/views.py
import random

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q, Count, Case, When, IntegerField, Min, Max
from django.db.models import Prefetch
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


PUBLIC_CACHE_TTL = 60 * 5 if not settings.DEBUG else 0
RANDOM_CACHE_TTL = 60 * 2 if not settings.DEBUG else 0


@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='list')
@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='retrieve')
class GalleryCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryCategory.objects.filter(is_active=True).annotate(
        count=Count('photos', filter=Q(photos__is_active=True), distinct=True)
    ).order_by('order', 'name')
    serializer_class = GalleryCategorySerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GalleryCategoryDetailSerializer
        return GalleryCategorySerializer

    def get_queryset(self):
        queryset = GalleryCategory.objects.filter(is_active=True).annotate(
            count=Count('photos', filter=Q(photos__is_active=True), distinct=True)
        ).order_by('order', 'name')

        if self.action == 'retrieve':
            active_photos = GalleryPhoto.objects.filter(is_active=True).select_related('category')
            queryset = queryset.prefetch_related(Prefetch('photos', queryset=active_photos))

        return queryset


@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='list')
@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='featured')
@method_decorator(cache_page(RANDOM_CACHE_TTL), name='random')
class GalleryPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryPhoto.objects.filter(is_active=True).select_related('category')
    serializer_class = GalleryPhotoSerializer
    pagination_class = GalleryPhotoPagination
    permission_classes = [AllowAny]
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
        count = max(1, min(int(request.query_params.get('count', 30)), 100))
        id_bounds = self.queryset.aggregate(min_id=Min('id'), max_id=Max('id'))
        min_id = id_bounds.get('min_id')
        max_id = id_bounds.get('max_id')
        if min_id is None or max_id is None:
            return Response([])

        sampled_ids = set()
        attempts = 0
        max_attempts = max(20, count * 10)

        while len(sampled_ids) < count and attempts < max_attempts:
            attempts += 1
            candidate = random.randint(min_id, max_id)

            nearest = self.queryset.filter(id__gte=candidate).values_list('id', flat=True).first()
            if nearest is None:
                nearest = self.queryset.filter(id__lte=candidate).values_list('id', flat=True).first()
            if nearest is not None:
                sampled_ids.add(nearest)

        if not sampled_ids:
            return Response([])

        sampled_ids = list(sampled_ids)[:count]
        preserved_order = Case(
            *[When(id=pk, then=pos) for pos, pk in enumerate(sampled_ids)],
            output_field=IntegerField(),
        )
        random_photos = self.queryset.filter(id__in=sampled_ids).order_by(preserved_order)
        serializer = self.get_serializer(random_photos, many=True)
        return Response(serializer.data)