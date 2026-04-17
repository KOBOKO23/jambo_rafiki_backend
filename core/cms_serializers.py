"""Serializers for CMS domain models managed from the admin API."""

from __future__ import annotations

from rest_framework import serializers

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


class SiteSettingSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteSetting
        fields = [
            'id',
            'site_name',
            'tagline',
            'logo',
            'logo_url',
            'favicon',
            'favicon_url',
            'primary_color',
            'secondary_color',
            'support_email',
            'support_phone',
            'address',
            'social_links',
            'seo_default_title',
            'seo_default_description',
            'homepage_title',
            'homepage_subtitle',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def get_logo_url(self, obj):
        if not obj.logo:
            return ''
        request = self.context.get('request')
        if request is None:
            return obj.logo.url
        return request.build_absolute_uri(obj.logo.url)

    def get_favicon_url(self, obj):
        if not obj.favicon:
            return ''
        request = self.context.get('request')
        if request is None:
            return obj.favicon.url
        return request.build_absolute_uri(obj.favicon.url)


class PageSectionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PageSection
        fields = [
            'id',
            'page',
            'section_type',
            'title',
            'subtitle',
            'body',
            'cta_label',
            'cta_url',
            'image',
            'image_url',
            'settings',
            'sort_order',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        if not obj.image:
            return ''
        request = self.context.get('request')
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = [
            'id',
            'title',
            'slug',
            'summary',
            'body',
            'status',
            'published_at',
            'scheduled_for',
            'seo_title',
            'seo_description',
            'canonical_url',
            'template',
            'parent',
            'sort_order',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']


class PageDetailSerializer(PageSerializer):
    sections = PageSectionSerializer(many=True, read_only=True)

    class Meta(PageSerializer.Meta):
        fields = PageSerializer.Meta.fields + ['sections']


class NavigationMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationMenuItem
        fields = [
            'id',
            'menu',
            'label',
            'page',
            'url',
            'parent',
            'sort_order',
            'is_active',
            'open_in_new_tab',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NavigationMenuSerializer(serializers.ModelSerializer):
    items = NavigationMenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = NavigationMenu
        fields = [
            'id',
            'name',
            'slug',
            'location',
            'is_active',
            'created_at',
            'updated_at',
            'items',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = [
            'id',
            'title',
            'message',
            'cta_label',
            'cta_url',
            'placement',
            'starts_at',
            'ends_at',
            'is_active',
            'priority',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RedirectRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedirectRule
        fields = [
            'id',
            'source_path',
            'target_url',
            'status_code',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MediaAssetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = [
            'id',
            'title',
            'file',
            'file_url',
            'alt_text',
            'caption',
            'category',
            'tags',
            'width',
            'height',
            'size',
            'usage_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'size', 'usage_count', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if not obj.file:
            return ''
        request = self.context.get('request')
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class ContentRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentRevision
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'version',
            'status',
            'author',
            'published_by',
            'summary',
            'snapshot',
            'created_at',
            'published_at',
        ]
        read_only_fields = ['id', 'version', 'author', 'created_at']
