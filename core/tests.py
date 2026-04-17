"""Tests for core admin API endpoints."""

from __future__ import annotations

from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from PIL import Image

from core.audit import log_audit_event
from core.admin import AdminUserCreationForm
from core.models import AuditEvent, BackgroundJob
from core.image_placement_serializers import IMAGE_PLACEMENT_CONFIG


class AdminUserCreationFormTest(TestCase):
    def test_email_is_required(self):
        form = AdminUserCreationForm(
            data={
                'username': 'new-admin',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username='existing', email='admin@example.com', password='StrongPass123!')
        form = AdminUserCreationForm(
            data={
                'username': 'new-admin',
                'email': 'ADMIN@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_valid_email_creates_user(self):
        form = AdminUserCreationForm(
            data={
                'username': 'new-admin',
                'email': 'admin@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )
        self.assertTrue(form.is_valid())


class AdminOverviewAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com',
        )

    def test_public_cannot_access_admin_overview(self):
        response = self.client.get(reverse('admin-overview'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_overview_returns_counts_and_recent_items(self):
        self.client.force_authenticate(user=self.admin)
        log_audit_event('test.event', actor=self.admin, source='core.tests', metadata={'kind': 'overview'})

        response = self.client.get(reverse('admin-overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('counts', response.data)
        self.assertIn('recent', response.data)
        self.assertIn('audit_events', response.data['recent'])
        self.assertGreaterEqual(len(response.data['recent']['audit_events']), 1)


class AuditEventAdminAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com',
        )
        self.event = AuditEvent.objects.create(
            event_type='test.event',
            source='core.tests',
            metadata={'hello': 'world'},
        )

    def test_admin_can_list_audit_events(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('admin-audit-event-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_public_cannot_list_audit_events(self):
        response = self.client.get(reverse('admin-audit-event-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BackgroundJobAdminAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com',
        )
        self.job = BackgroundJob.objects.create(
            job_type='send_email',
            payload={'subject': 'Hi', 'message': 'Hello', 'recipient_list': ['test@example.com']},
            status=BackgroundJob.STATUS_FAILED,
            attempts=2,
            max_attempts=3,
            last_error='boom',
        )

    def test_admin_can_retry_failed_job(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse('admin-background-job-retry', args=[self.job.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, BackgroundJob.STATUS_PENDING)
        self.assertEqual(self.job.attempts, 0)
        self.assertEqual(self.job.last_error, '')

    def test_public_cannot_retry_job(self):
        response = self.client.post(reverse('admin-background-job-retry', args=[self.job.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminSessionAuthAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com',
        )
        self.staff_user = User.objects.create_user(
            username='editor',
            password='editorpass',
            email='editor@example.com',
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='visitor',
            password='visitorpass',
            email='visitor@example.com',
            is_staff=False,
        )

    def _csrf_headers(self):
        csrf_response = self.client.get(reverse('admin-auth-csrf'))
        self.assertEqual(csrf_response.status_code, status.HTTP_200_OK)
        csrf_token = self.client.cookies['csrftoken'].value
        return {'HTTP_X_CSRFTOKEN': csrf_token}

    def test_login_with_username_and_current_user(self):
        headers = self._csrf_headers()
        response = self.client.post(
            reverse('admin-auth-login'),
            {'username': 'admin', 'password': 'adminpass'},
            format='json',
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'super_admin')

        me_response = self.client.get(reverse('admin-auth-me'))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'admin')

    def test_public_auth_alias_matches_frontend_contract(self):
        headers = self._csrf_headers()
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'admin', 'password': 'adminpass'},
            format='json',
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        me_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'admin')

    def test_login_with_email_and_logout(self):
        headers = self._csrf_headers()
        response = self.client.post(
            reverse('admin-auth-login'),
            {'email': 'editor@example.com', 'password': 'editorpass'},
            format='json',
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'admin')

        logout_headers = {'HTTP_X_CSRFTOKEN': response.data['csrf_token']}
        logout_response = self.client.post(reverse('admin-auth-logout'), **logout_headers)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get(reverse('admin-auth-me'))
        self.assertEqual(me_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_login_is_rejected(self):
        headers = self._csrf_headers()
        response = self.client.post(
            reverse('admin-auth-login'),
            {'username': 'visitor', 'password': 'visitorpass'},
            format='json',
            **headers,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_current_user_rejects_authenticated_non_staff_user(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('admin-auth-me'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_without_session_still_succeeds(self):
        headers = self._csrf_headers()
        response = self.client.post(reverse('admin-auth-logout'), **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CMSAdminAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='cms_admin',
            password='adminpass',
            email='cms-admin@example.com',
        )

    def _valid_image_upload(self, name='asset.png'):
        file_obj = BytesIO()
        image = Image.new('RGB', (12, 12), color='blue')
        image.save(file_obj, format='PNG')
        file_obj.seek(0)
        return SimpleUploadedFile(name, file_obj.read(), content_type='image/png')

    def test_admin_image_placement_options_are_exposed(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse('admin-image-placements'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('destinations', response.data)
        self.assertGreaterEqual(len(response.data['destinations']), 1)
        self.assertIn('home_hero', IMAGE_PLACEMENT_CONFIG)

    def test_admin_can_upload_home_hero_image_to_page_sections(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse('admin-image-placements'),
            {
                'destination': 'home_hero',
                'title': 'Homepage hero',
                'subtitle': 'Welcome',
                'body': 'Hero image body',
                'image': self._valid_image_upload('hero.png'),
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['destination'], 'home_hero')
        self.assertEqual(response.data['source_type'], 'page_section')
        self.assertTrue(response.data['image_url'])

    def test_public_image_placements_feed_returns_active_placements(self):
        self.client.force_authenticate(user=self.admin)

        placement_response = self.client.post(
            reverse('admin-image-placements'),
            {
                'destination': 'site_logo',
                'image': self._valid_image_upload('logo.png'),
            },
            format='multipart',
        )
        self.assertEqual(placement_response.status_code, status.HTTP_201_CREATED)

        public_response = self.client.get('/api/v1/content/image-placements/')
        self.assertEqual(public_response.status_code, status.HTTP_200_OK)
        results = public_response.data.get('results', public_response.data)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any(item['destination'] == 'site_logo' for item in results))

    def test_admin_can_read_and_update_site_settings(self):
        self.client.force_authenticate(user=self.admin)

        get_response = self.client.get(reverse('admin-site-settings'))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertIn('site_name', get_response.data)

        patch_response = self.client.patch(
            reverse('admin-site-settings'),
            {
                'site_name': 'Jambo Rafiki CMS',
                'support_email': 'support@example.com',
            },
            format='json',
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['site_name'], 'Jambo Rafiki CMS')

    def test_admin_page_workflow_creates_revisions(self):
        self.client.force_authenticate(user=self.admin)

        create_response = self.client.post(
            reverse('admin-page-list'),
            {
                'title': 'About Us',
                'summary': 'Who we are',
                'body': 'About page body',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        page_id = create_response.data['id']

        section_response = self.client.post(
            reverse('admin-page-section-list'),
            {
                'page': page_id,
                'section_type': 'hero',
                'title': 'Welcome',
                'body': 'Intro section',
                'sort_order': 1,
            },
            format='json',
        )
        self.assertEqual(section_response.status_code, status.HTTP_201_CREATED)

        publish_response = self.client.post(reverse('admin-page-publish', args=[page_id]))
        self.assertEqual(publish_response.status_code, status.HTTP_200_OK)
        self.assertEqual(publish_response.data['status'], 'published')

        revisions_response = self.client.get(reverse('admin-content-revision-list'))
        self.assertEqual(revisions_response.status_code, status.HTTP_200_OK)
        revisions = revisions_response.data.get('results', revisions_response.data)
        self.assertGreaterEqual(len(revisions), 2)

    def test_admin_can_manage_navigation_banner_redirect_and_media(self):
        self.client.force_authenticate(user=self.admin)

        menu_response = self.client.post(
            reverse('admin-navigation-menu-list'),
            {'name': 'Main Menu', 'location': 'header'},
            format='json',
        )
        self.assertEqual(menu_response.status_code, status.HTTP_201_CREATED)
        menu_id = menu_response.data['id']

        item_response = self.client.post(
            reverse('admin-navigation-item-list'),
            {
                'menu': menu_id,
                'label': 'Donate',
                'url': '/donate',
                'sort_order': 1,
            },
            format='json',
        )
        self.assertEqual(item_response.status_code, status.HTTP_201_CREATED)

        banner_response = self.client.post(
            reverse('admin-banner-list'),
            {
                'title': 'Spring Campaign',
                'message': 'Support children this season',
                'placement': 'hero',
                'priority': 10,
            },
            format='json',
        )
        self.assertEqual(banner_response.status_code, status.HTTP_201_CREATED)

        redirect_response = self.client.post(
            reverse('admin-redirect-rule-list'),
            {
                'source_path': '/legacy-about',
                'target_url': '/about',
                'status_code': 301,
            },
            format='json',
        )
        self.assertEqual(redirect_response.status_code, status.HTTP_201_CREATED)

        media_response = self.client.post(
            reverse('admin-media-asset-list'),
            {
                'title': 'Child Profile',
                'category': 'profiles',
                'file': self._valid_image_upload('child-profile.png'),
                'alt_text': 'Child portrait',
            },
            format='multipart',
        )
        self.assertEqual(media_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(media_response.data['file_url'])

    def test_public_cannot_access_cms_admin_routes(self):
        response = self.client.get(reverse('admin-page-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)