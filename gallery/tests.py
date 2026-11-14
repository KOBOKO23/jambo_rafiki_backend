"""
Tests for the gallery app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import GalleryCategory, GalleryPhoto
import datetime
from io import BytesIO
from PIL import Image


class GalleryCategoryModelTest(TestCase):

    def setUp(self):
        self.category = GalleryCategory.objects.create(
            name="Community Events",
            description="Photos from community events.",
            icon="Users",
            color="from-pink-500 to-rose-500",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.category), "Community Events")

    def test_slug_auto_generated(self):
        self.assertEqual(self.category.slug, "community-events")

    def test_slug_not_overwritten_on_resave(self):
        self.category.name = "Changed Name"
        self.category.save()
        self.assertEqual(self.category.slug, "community-events")

    def test_photo_count_property_empty(self):
        self.assertEqual(self.category.photo_count, 0)

    def test_photo_count_increments(self):
        GalleryPhoto.objects.create(
            title="Test Photo",
            image=SimpleUploadedFile("test.jpg", b"x", content_type="image/jpeg"),
            category=self.category,
            date_taken=datetime.date.today(),
        )
        self.assertEqual(self.category.photo_count, 1)

    def test_inactive_photos_excluded_from_count(self):
        GalleryPhoto.objects.create(
            title="Inactive Photo",
            image=SimpleUploadedFile("test.jpg", b"x", content_type="image/jpeg"),
            category=self.category,
            date_taken=datetime.date.today(),
            is_active=False,
        )
        self.assertEqual(self.category.photo_count, 0)


class GalleryPhotoModelTest(TestCase):

    def setUp(self):
        self.category = GalleryCategory.objects.create(
            name="Education",
            description="Education photos.",
        )
        self.photo = GalleryPhoto.objects.create(
            title="Children in Class",
            image=SimpleUploadedFile("class.jpg", b"x", content_type="image/jpeg"),
            category=self.category,
            date_taken=datetime.date.today(),
        )

    def test_str_representation(self):
        self.assertEqual(str(self.photo), "Children in Class")

    def test_default_is_active_true(self):
        self.assertTrue(self.photo.is_active)

    def test_default_is_featured_false(self):
        self.assertFalse(self.photo.is_featured)


class GalleryAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.category = GalleryCategory.objects.create(
            name="Community Events",
            description="Community event photos.",
            slug="community-events",
        )
        self.inactive_category = GalleryCategory.objects.create(
            name="Hidden Category",
            description="Not shown.",
            slug="hidden-category",
            is_active=False,
        )
        self.photo = GalleryPhoto.objects.create(
            title="Test Photo",
            image=SimpleUploadedFile("test.jpg", b"x", content_type="image/jpeg"),
            category=self.category,
            date_taken=datetime.date.today(),
            is_featured=True,
        )
        self.inactive_photo = GalleryPhoto.objects.create(
            title="Hidden Photo",
            image=SimpleUploadedFile("hidden.jpg", b"x", content_type="image/jpeg"),
            category=self.category,
            date_taken=datetime.date.today(),
            is_active=False,
        )

    def _get_results(self, response):
        """Handle both paginated and non-paginated responses"""
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    # ------------------------------------------------------------------ #
    # Categories                                                           #
    # ------------------------------------------------------------------ #

    def test_list_categories_returns_active_only(self):
        url = reverse('gallery-category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        names = [c['name'] for c in results]
        self.assertIn("Community Events", names)
        self.assertNotIn("Hidden Category", names)

    def test_retrieve_category_by_slug(self):
        url = reverse('gallery-category-detail', args=['community-events'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Community Events")

    def test_category_detail_includes_photos(self):
        url = reverse('gallery-category-detail', args=['community-events'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('photos', response.data)
        self.assertIn('image_url', response.data['photos'][0])

    def test_category_list_is_read_only(self):
        url = reverse('gallery-category-list')
        response = self.client.post(url, {'name': 'New'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ------------------------------------------------------------------ #
    # Photos                                                               #
    # ------------------------------------------------------------------ #

    def test_list_photos_returns_active_only(self):
        url = reverse('gallery-photo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        titles = [p['title'] for p in results]
        self.assertIn("Test Photo", titles)
        self.assertNotIn("Hidden Photo", titles)
        self.assertTrue(results[0]['image_url'].startswith('http'))

    def test_featured_photos_endpoint(self):
        url = reverse('gallery-photo-featured')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [p['title'] for p in response.data]
        self.assertIn("Test Photo", titles)

    def test_random_photos_endpoint(self):
        url = reverse('gallery-photo-random')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_photos_filter_by_category(self):
        url = reverse('gallery-photo-list')
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_photos_search(self):
        url = reverse('gallery-photo-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        titles = [p['title'] for p in results]
        self.assertIn("Test Photo", titles)

    def test_photo_list_is_read_only(self):
        url = reverse('gallery-photo-list')
        response = self.client.post(url, {'title': 'New'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class GalleryCacheInvalidationSignalTest(TestCase):

    def test_gallery_photo_write_clears_cache(self):
        category = GalleryCategory.objects.create(
            name="Signal Category",
            description="Signal test category",
        )
        with patch('gallery.signals.cache.clear') as clear_cache:
            GalleryPhoto.objects.create(
                title="Signal Photo",
                image=SimpleUploadedFile("signal.jpg", b"x", content_type="image/jpeg"),
                category=category,
                date_taken=datetime.date.today(),
            )
        clear_cache.assert_called_once()


class GalleryAdminAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com',
        )

    def _make_image_file(self, name='admin.png'):
        image = Image.new('RGB', (1, 1), color=(255, 0, 0))
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type='image/png')

    def test_public_cannot_list_admin_gallery_categories(self):
        response = self.client.get(reverse('admin-gallery-category-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_gallery_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse('admin-gallery-category-list'),
            {
                'name': 'Admin Events',
                'description': 'Managed through the CMS',
                'icon': 'Users',
                'color': 'from-blue-500 to-cyan-500',
                'order': 2,
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'admin-events')

    def test_admin_can_create_gallery_photo(self):
        self.client.force_authenticate(user=self.admin)
        category = GalleryCategory.objects.create(
            name='CMS Media',
            description='Media library category',
        )
        response = self.client.post(
            reverse('admin-gallery-photo-list'),
            {
                'title': 'CMS Photo',
                'description': 'Uploaded from admin',
                'image': self._make_image_file(),
                'category': category.id,
                'date_taken': datetime.date.today().isoformat(),
                'is_featured': True,
                'is_active': True,
                'order': 1,
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('image_url', response.data)

class UploadedImageOptimisationTest(TestCase):
    """New uploads are rotated upright, downscaled and stripped of EXIF/GPS metadata."""

    def _phone_photo(self):
        from PIL import Image
        image = Image.new('RGB', (4000, 3000), 'orange')
        exif = Image.Exif()
        exif[0x0112] = 6  # orientation: rotate 90° clockwise to display
        exif[0x8825] = {1: 'S', 2: (0.0, 31.0, 0.0)}  # GPS IFD
        buffer = BytesIO()
        image.save(buffer, format='JPEG', exif=exif)
        return SimpleUploadedFile('phone.jpg', buffer.getvalue(), content_type='image/jpeg')

    def test_new_upload_is_rotated_resized_and_metadata_free(self):
        from PIL import Image
        category = GalleryCategory.objects.create(name='Children', description='x')
        photo = GalleryPhoto.objects.create(
            title='Phone upload', image=self._phone_photo(), category=category,
            date_taken=datetime.date(2026, 1, 1),
        )
        with Image.open(photo.image.path) as stored:
            self.assertEqual(stored.size, (1500, 2000))  # portrait after rotation, capped at 2000px
            exif = stored.getexif()
            self.assertIsNone(exif.get(0x0112))
            self.assertIsNone(exif.get(0x8825))
        photo.image.delete(save=False)
