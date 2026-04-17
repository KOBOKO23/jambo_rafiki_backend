"""Public and admin endpoints for destination-aware image handling."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.image_placement_serializers import (
    IMAGE_PLACEMENT_CONFIG,
    IMAGE_PLACEMENT_CHOICES,
    ImagePlacementRecordSerializer,
    ImagePlacementUploadSerializer,
    build_absolute_file_url,
    get_destination_label,
)
from core.models import PageSection, SiteSetting


class PublicImagePlacementView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        destination_filter = request.query_params.get('destination')
        records = []

        for section in PageSection.objects.select_related('page').filter(is_active=True).order_by('page__sort_order', 'sort_order', 'id'):
            if not section.image:
                continue
            destination = f'{section.page.slug}_{section.section_type}'
            if destination_filter and destination_filter != destination:
                continue
            records.append({
                'destination': destination,
                'destination_label': get_destination_label(destination) if destination in IMAGE_PLACEMENT_CONFIG else f'{section.page.title} / {section.section_type.replace("_", " ").title()}',
                'source_type': 'page_section',
                'object_id': section.id,
                'title': section.title,
                'image_url': build_absolute_file_url(request, section.image),
                'stored_path': section.image.name,
                'page_slug': section.page.slug,
                'section_type': section.section_type,
                'is_active': section.is_active,
                'updated_at': section.updated_at,
            })

        site_settings = SiteSetting.objects.first()
        if site_settings is not None:
            for destination, field_name in [('site_logo', 'logo'), ('site_favicon', 'favicon')]:
                file_field = getattr(site_settings, field_name)
                if not file_field:
                    continue
                if destination_filter and destination_filter != destination:
                    continue
                records.append({
                    'destination': destination,
                    'destination_label': get_destination_label(destination),
                    'source_type': 'site_setting',
                    'object_id': site_settings.id,
                    'title': site_settings.site_name,
                    'image_url': build_absolute_file_url(request, file_field),
                    'stored_path': file_field.name,
                    'page_slug': '',
                    'section_type': '',
                    'is_active': True,
                    'updated_at': site_settings.updated_at,
                })

        serializer = ImagePlacementRecordSerializer(records, many=True)
        return Response({'results': serializer.data})


class AdminImagePlacementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            'destinations': [
                {
                    'value': value,
                    'label': label,
                    'kind': IMAGE_PLACEMENT_CONFIG[value]['kind'],
                }
                for value, label in IMAGE_PLACEMENT_CHOICES
            ]
        })

    def post(self, request):
        serializer = ImagePlacementUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            'message': f"Image saved to {result['destination_label']}.",
            **result,
        }, status=status.HTTP_201_CREATED)
