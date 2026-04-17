"""Admin-only CMS views for pages, navigation, banners, settings, and media."""

from __future__ import annotations

from django.db.models import Max
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import log_audit_event
from core.cms_serializers import (
    BannerSerializer,
    ContentRevisionSerializer,
    MediaAssetSerializer,
    NavigationMenuItemSerializer,
    NavigationMenuSerializer,
    PageDetailSerializer,
    PageSectionSerializer,
    PageSerializer,
    RedirectRuleSerializer,
    SiteSettingSerializer,
)
from core.models import (
    Banner,
    ContentRevision,
    MediaAsset,
    NavigationMenu,
    NavigationMenuItem,
    Page,
    PageSection,
    RedirectRule,
    SiteSetting,
)


class SiteSettingView(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self):
        settings_obj, _ = SiteSetting.objects.get_or_create(singleton_key=1)
        return settings_obj

    def get(self, request):
        serializer = SiteSettingSerializer(self.get_object(), context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        instance = self.get_object()
        serializer = SiteSettingSerializer(instance, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(singleton_key=1)
        log_audit_event(
            'site_settings.updated',
            actor=request.user,
            target=instance,
            source='core.cms.site_setting_put',
        )
        return Response(serializer.data)

    def patch(self, request):
        instance = self.get_object()
        serializer = SiteSettingSerializer(instance, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(singleton_key=1)
        log_audit_event(
            'site_settings.updated',
            actor=request.user,
            target=instance,
            source='core.cms.site_setting_patch',
        )
        return Response(serializer.data)


class AuditModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

    def _audit_source(self):
        return f'core.cms.{self.basename}'

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit_event(
            f'{self.basename}.created',
            actor=self.request.user,
            target=instance,
            source=self._audit_source(),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit_event(
            f'{self.basename}.updated',
            actor=self.request.user,
            target=instance,
            source=self._audit_source(),
        )

    def perform_destroy(self, instance):
        model_name = instance._meta.model_name
        target_id = str(instance.pk)
        super().perform_destroy(instance)
        log_audit_event(
            f'{self.basename}.deleted',
            actor=self.request.user,
            target_model=model_name,
            target_id=target_id,
            source=self._audit_source(),
        )


class PageViewSet(AuditModelViewSet):
    queryset = Page.objects.select_related('parent', 'created_by', 'updated_by').prefetch_related('sections')
    serializer_class = PageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'summary', 'status']
    ordering_fields = ['updated_at', 'title', 'sort_order', 'status', 'published_at']
    ordering = ['sort_order', 'title']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'preview']:
            return PageDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user, updated_by=self.request.user)
        self._create_revision(instance, status=ContentRevision.STATUS_DRAFT, summary='Initial draft')
        log_audit_event(
            'page.created',
            actor=self.request.user,
            target=instance,
            source='core.cms.page',
        )

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        self._create_revision(instance, status=instance.status, summary='Page updated')
        log_audit_event(
            'page.updated',
            actor=self.request.user,
            target=instance,
            source='core.cms.page',
            metadata={'status': instance.status},
        )

    def _create_revision(self, page: Page, status: str, summary: str = '') -> ContentRevision:
        latest_version = ContentRevision.objects.filter(entity_type='page', entity_id=str(page.id)).aggregate(
            latest=Max('version')
        )['latest']
        next_version = (latest_version or 0) + 1
        snapshot = PageDetailSerializer(page, context={'request': self.request}).data
        return ContentRevision.objects.create(
            entity_type='page',
            entity_id=str(page.id),
            version=next_version,
            status=status,
            author=self.request.user,
            summary=summary,
            snapshot=snapshot,
            published_by=self.request.user if status == ContentRevision.STATUS_PUBLISHED else None,
            published_at=timezone.now() if status == ContentRevision.STATUS_PUBLISHED else None,
        )

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        page = self.get_object()
        page.status = Page.STATUS_PUBLISHED
        page.published_at = timezone.now()
        page.scheduled_for = None
        page.updated_by = request.user
        page.save(update_fields=['status', 'published_at', 'scheduled_for', 'updated_by', 'updated_at'])

        self._create_revision(page, status=ContentRevision.STATUS_PUBLISHED, summary='Published')
        log_audit_event(
            'page.published',
            actor=request.user,
            target=page,
            source='core.cms.page.publish',
        )

        serializer = self.get_serializer(page)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        page = self.get_object()
        page.status = Page.STATUS_ARCHIVED
        page.updated_by = request.user
        page.save(update_fields=['status', 'updated_by', 'updated_at'])

        self._create_revision(page, status=ContentRevision.STATUS_ARCHIVED, summary='Archived')
        log_audit_event(
            'page.archived',
            actor=request.user,
            target=page,
            source='core.cms.page.archive',
        )

        serializer = self.get_serializer(page)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        page = self.get_object()
        scheduled_for = request.data.get('scheduled_for')
        if not scheduled_for:
            return Response({'scheduled_for': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        # Reuse serializer parsing to validate datetime format.
        parse_serializer = PageSerializer(page, data={'scheduled_for': scheduled_for}, partial=True)
        parse_serializer.is_valid(raise_exception=True)

        page.status = Page.STATUS_SCHEDULED
        page.scheduled_for = parse_serializer.validated_data['scheduled_for']
        page.updated_by = request.user
        page.save(update_fields=['status', 'scheduled_for', 'updated_by', 'updated_at'])

        self._create_revision(page, status=ContentRevision.STATUS_DRAFT, summary='Scheduled')
        log_audit_event(
            'page.scheduled',
            actor=request.user,
            target=page,
            source='core.cms.page.schedule',
            metadata={'scheduled_for': page.scheduled_for.isoformat()},
        )

        serializer = self.get_serializer(page)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


class PageSectionViewSet(AuditModelViewSet):
    queryset = PageSection.objects.select_related('page')
    serializer_class = PageSectionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['page__title', 'section_type', 'title', 'subtitle']
    ordering_fields = ['sort_order', 'updated_at', 'created_at']
    ordering = ['sort_order', 'id']


class NavigationMenuViewSet(AuditModelViewSet):
    queryset = NavigationMenu.objects.prefetch_related('items')
    serializer_class = NavigationMenuSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'location']
    ordering_fields = ['name', 'updated_at', 'location']
    ordering = ['location', 'name']


class NavigationMenuItemViewSet(AuditModelViewSet):
    queryset = NavigationMenuItem.objects.select_related('menu', 'page', 'parent')
    serializer_class = NavigationMenuItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['label', 'menu__name', 'url', 'page__title']
    ordering_fields = ['sort_order', 'updated_at', 'created_at']
    ordering = ['sort_order', 'id']


class BannerViewSet(AuditModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message', 'placement']
    ordering_fields = ['priority', 'updated_at', 'starts_at', 'ends_at']
    ordering = ['-priority', '-updated_at']


class RedirectRuleViewSet(AuditModelViewSet):
    queryset = RedirectRule.objects.all()
    serializer_class = RedirectRuleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['source_path', 'target_url']
    ordering_fields = ['source_path', 'updated_at']
    ordering = ['source_path']


class MediaAssetViewSet(AuditModelViewSet):
    queryset = MediaAsset.objects.all()
    serializer_class = MediaAssetSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'alt_text', 'caption', 'category']
    ordering_fields = ['created_at', 'updated_at', 'category', 'usage_count']
    ordering = ['-created_at']


class ContentRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentRevision.objects.select_related('author', 'published_by').all()
    serializer_class = ContentRevisionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['entity_type', 'entity_id', 'summary', 'status']
    ordering_fields = ['created_at', 'version', 'status']
    ordering = ['-created_at']
