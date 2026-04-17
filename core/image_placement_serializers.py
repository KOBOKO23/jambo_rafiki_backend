"""Serializers for destination-aware image placement workflows."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from core.models import MediaAsset, Page, PageSection, SiteSetting
from gallery.models import GalleryCategory, GalleryPhoto


IMAGE_PLACEMENT_CONFIG = {
    'home_hero': {
        'label': 'Home page / Hero section',
        'kind': 'page_section',
        'page_slug': 'home',
        'page_title': 'Home',
        'section_type': 'hero',
        'singular': True,
    },
    'home_featured_programs': {
        'label': 'Home page / Featured Programs section',
        'kind': 'page_section',
        'page_slug': 'home',
        'page_title': 'Home',
        'section_type': 'featured_programs',
        'singular': False,
    },
    'home_programs': {
        'label': 'Home page / Programs section',
        'kind': 'page_section',
        'page_slug': 'home',
        'page_title': 'Home',
        'section_type': 'programs',
        'singular': False,
    },
    'home_recent_activities': {
        'label': 'Home page / Recent Activities section',
        'kind': 'page_section',
        'page_slug': 'home',
        'page_title': 'Home',
        'section_type': 'recent_activities',
        'singular': False,
    },
    'home_stories_of_hope': {
        'label': 'Home page / Stories of Hope section',
        'kind': 'page_section',
        'page_slug': 'home',
        'page_title': 'Home',
        'section_type': 'stories_of_hope',
        'singular': False,
    },
    'about_director': {
        'label': 'About page / Director section',
        'kind': 'page_section',
        'page_slug': 'about',
        'page_title': 'About',
        'section_type': 'director',
        'singular': True,
    },
    'gallery_grid': {
        'label': 'Gallery page / Gallery grid',
        'kind': 'gallery_photo',
    },
    'media_library': {
        'label': 'Dashboard / Media Library',
        'kind': 'media_asset',
    },
    'site_logo': {
        'label': 'Site branding / Logo',
        'kind': 'site_setting',
        'site_field': 'logo',
    },
    'site_favicon': {
        'label': 'Site branding / Favicon',
        'kind': 'site_setting',
        'site_field': 'favicon',
    },
}

IMAGE_PLACEMENT_CHOICES = [(key, value['label']) for key, value in IMAGE_PLACEMENT_CONFIG.items()]


def get_destination_label(destination: str) -> str:
    config = IMAGE_PLACEMENT_CONFIG.get(destination)
    return config['label'] if config is not None else destination


def build_absolute_file_url(request, file_field):
    if not file_field:
        return ''
    url = file_field.url
    if request is None:
        return url
    return request.build_absolute_uri(url)


def get_or_create_page(slug: str, title: str) -> Page:
    page, _ = Page.objects.get_or_create(
        slug=slug,
        defaults={
            'title': title,
            'template': slug,
            'status': Page.STATUS_PUBLISHED,
            'published_at': timezone.now(),
        },
    )
    return page


class ImagePlacementRecordSerializer(serializers.Serializer):
    destination = serializers.CharField()
    destination_label = serializers.CharField()
    source_type = serializers.CharField()
    object_id = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, required=False)
    image_url = serializers.CharField(allow_blank=True, required=False)
    stored_path = serializers.CharField(allow_blank=True, required=False)
    page_slug = serializers.CharField(allow_blank=True, required=False)
    section_type = serializers.CharField(allow_blank=True, required=False)
    is_active = serializers.BooleanField(required=False)
    updated_at = serializers.DateTimeField(required=False)


class ImagePlacementUploadSerializer(serializers.Serializer):
    destination = serializers.ChoiceField(choices=IMAGE_PLACEMENT_CHOICES)
    image = serializers.ImageField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subtitle = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    cta_label = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    cta_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    alt_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    caption = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sort_order = serializers.IntegerField(required=False, default=0)
    is_active = serializers.BooleanField(required=False, default=True)
    is_featured = serializers.BooleanField(required=False, default=False)
    date_taken = serializers.DateField(required=False)

    def validate(self, attrs):
        uploaded_file = attrs.get('image') or attrs.get('file')
        if uploaded_file is None:
            raise serializers.ValidationError({'image': ['An image or file upload is required.']})

        destination = attrs['destination']
        if destination in {'gallery_grid', 'media_library'} and not attrs.get('title'):
            attrs['title'] = uploaded_file.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()

        if destination in {'home_hero', 'home_featured_programs', 'home_programs', 'home_recent_activities', 'home_stories_of_hope', 'about_director'} and not attrs.get('title'):
            attrs['title'] = get_destination_label(destination)

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        destination = validated_data['destination']
        uploaded_file = validated_data.pop('image', None) or validated_data.pop('file', None)
        destination_config = IMAGE_PLACEMENT_CONFIG[destination]

        if destination_config['kind'] == 'page_section':
            page = get_or_create_page(destination_config['page_slug'], destination_config['page_title'])
            section_defaults = {
                'title': validated_data.get('title', ''),
                'subtitle': validated_data.get('subtitle', ''),
                'body': validated_data.get('body', ''),
                'cta_label': validated_data.get('cta_label', ''),
                'cta_url': validated_data.get('cta_url', ''),
                'image': uploaded_file,
                'sort_order': validated_data.get('sort_order', 0),
                'is_active': validated_data.get('is_active', True),
            }
            if destination_config['singular']:
                section, _ = PageSection.objects.update_or_create(
                    page=page,
                    section_type=destination_config['section_type'],
                    defaults=section_defaults,
                )
            else:
                section = PageSection.objects.create(
                    page=page,
                    section_type=destination_config['section_type'],
                    **section_defaults,
                )
            return {
                'destination': destination,
                'destination_label': destination_config['label'],
                'source_type': 'page_section',
                'object_id': section.id,
                'title': section.title,
                'image_url': build_absolute_file_url(request, section.image),
                'stored_path': section.image.name,
                'page_slug': page.slug,
                'section_type': section.section_type,
                'is_active': section.is_active,
                'updated_at': section.updated_at,
                'data': {
                    'id': section.id,
                    'page': section.page_id,
                    'section_type': section.section_type,
                    'title': section.title,
                    'subtitle': section.subtitle,
                    'body': section.body,
                    'cta_label': section.cta_label,
                    'cta_url': section.cta_url,
                },
            }

        if destination_config['kind'] == 'gallery_photo':
            category_name = validated_data.get('category', '').strip()
            gallery_category = None
            if category_name:
                gallery_category, _ = GalleryCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': '', 'icon': 'Images'},
                )
            elif GalleryCategory.objects.filter(slug='gallery').exists():
                gallery_category = GalleryCategory.objects.get(slug='gallery')
            else:
                gallery_category, _ = GalleryCategory.objects.get_or_create(
                    name='Gallery',
                    defaults={'description': 'General gallery photos', 'icon': 'Images'},
                )

            photo = GalleryPhoto.objects.create(
                title=validated_data['title'],
                description=validated_data.get('description', ''),
                image=uploaded_file,
                category=gallery_category,
                date_taken=validated_data.get('date_taken') or timezone.localdate(),
                is_featured=validated_data.get('is_featured', False),
                is_active=validated_data.get('is_active', True),
                order=validated_data.get('sort_order', 0),
            )
            return {
                'destination': destination,
                'destination_label': destination_config['label'],
                'source_type': 'gallery_photo',
                'object_id': photo.id,
                'title': photo.title,
                'image_url': build_absolute_file_url(request, photo.image),
                'stored_path': photo.image.name,
                'page_slug': '',
                'section_type': '',
                'is_active': photo.is_active,
                'updated_at': photo.created_at,
                'data': {
                    'id': photo.id,
                    'title': photo.title,
                    'description': photo.description,
                    'category': photo.category_id,
                    'date_taken': photo.date_taken,
                    'is_featured': photo.is_featured,
                    'is_active': photo.is_active,
                    'order': photo.order,
                },
            }

        if destination_config['kind'] == 'media_asset':
            asset = MediaAsset.objects.create(
                title=validated_data['title'],
                file=uploaded_file,
                alt_text=validated_data.get('alt_text', ''),
                caption=validated_data.get('caption', ''),
                category=validated_data.get('category', ''),
            )
            return {
                'destination': destination,
                'destination_label': destination_config['label'],
                'source_type': 'media_asset',
                'object_id': asset.id,
                'title': asset.title,
                'image_url': build_absolute_file_url(request, asset.file),
                'stored_path': asset.file.name,
                'page_slug': '',
                'section_type': '',
                'is_active': True,
                'updated_at': asset.updated_at,
                'data': {
                    'id': asset.id,
                    'title': asset.title,
                    'alt_text': asset.alt_text,
                    'caption': asset.caption,
                    'category': asset.category,
                    'size': asset.size,
                    'usage_count': asset.usage_count,
                },
            }

        if destination_config['kind'] == 'site_setting':
            settings_obj, _ = SiteSetting.objects.get_or_create(singleton_key=1)
            site_field = destination_config['site_field']
            setattr(settings_obj, site_field, uploaded_file)
            settings_obj.save(update_fields=[site_field, 'updated_at'])
            return {
                'destination': destination,
                'destination_label': destination_config['label'],
                'source_type': 'site_setting',
                'object_id': settings_obj.id,
                'title': settings_obj.site_name,
                'image_url': build_absolute_file_url(request, getattr(settings_obj, site_field)),
                'stored_path': getattr(settings_obj, site_field).name,
                'page_slug': '',
                'section_type': '',
                'is_active': True,
                'updated_at': settings_obj.updated_at,
                'data': {
                    'id': settings_obj.id,
                    'site_name': settings_obj.site_name,
                    'logo_url': build_absolute_file_url(request, settings_obj.logo),
                    'favicon_url': build_absolute_file_url(request, settings_obj.favicon),
                },
            }

        raise serializers.ValidationError({'destination': ['Unsupported destination.']})
