"""
Tests for the testimonials app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status as drf_status
from django.contrib.auth.models import User
from .models import Testimonial


class TestimonialModelTest(TestCase):

    def setUp(self):
        self.testimonial = Testimonial.objects.create(
            name="Rev. John Omondi",
            email="john@example.com",
            role="community_member",
            text="Jambo Rafiki is transforming lives in our community.",
        )

    def test_str_representation(self):
        self.assertIn("Rev. John Omondi", str(self.testimonial))
        self.assertIn("Pending", str(self.testimonial))

    def test_default_status_pending(self):
        self.assertEqual(self.testimonial.status, 'pending')

    def test_approve_method(self):
        self.testimonial.approve()
        self.assertEqual(self.testimonial.status, 'approved')
        self.assertIsNotNone(self.testimonial.approved_at)

    def test_reject_method(self):
        self.testimonial.reject()
        self.assertEqual(self.testimonial.status, 'rejected')

    def test_display_role_uses_custom_if_set(self):
        self.testimonial.role_custom = "Community Leader"
        self.testimonial.save()
        self.assertEqual(self.testimonial.display_role, "Community Leader")

    def test_display_role_falls_back_to_choice_label(self):
        self.assertEqual(self.testimonial.display_role, "Community Member")


class TestimonialAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        self.list_url = reverse('testimonial-list')
        self.pending_url = reverse('testimonial-pending')
        self.valid_payload = {
            "name": "Mary Achieng",
            "email": "mary@example.com",
            "role": "volunteer",
            "text": "Working with these amazing children has changed my life completely.",
        }

    def _create_testimonial(self, status='pending', **kwargs):
        data = {
            'name': 'Test Person',
            'email': 'test@example.com',
            'role': 'other',
            'text': 'A test testimonial that is long enough to be valid.',
            **kwargs
        }
        t = Testimonial.objects.create(**data)
        if status == 'approved':
            t.approve()
        elif status == 'rejected':
            t.reject()
        return t

    def _get_results(self, response):
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    # ------------------------------------------------------------------ #
    # Public list — approved only                                         #
    # ------------------------------------------------------------------ #

    def test_public_list_returns_approved_only(self):
        self._create_testimonial(status='approved', name='Approved Person',
                                 email='approved@example.com')
        self._create_testimonial(status='pending', name='Pending Person',
                                 email='pending@example.com')
        self._create_testimonial(status='rejected', name='Rejected Person',
                                 email='rejected@example.com')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        results = self._get_results(response)
        names = [t['name'] for t in results]
        self.assertIn('Approved Person', names)
        self.assertNotIn('Pending Person', names)
        self.assertNotIn('Rejected Person', names)

    def test_public_list_does_not_expose_email(self):
        self._create_testimonial(status='approved')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        for item in self._get_results(response):
            self.assertNotIn('email', item)

    def test_public_list_includes_display_role(self):
        self._create_testimonial(status='approved', role='volunteer')
        response = self.client.get(self.list_url)
        results = self._get_results(response)
        self.assertIn('display_role', results[0])

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    def test_public_can_submit_testimonial(self):
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_submitted_testimonial_is_pending(self):
        self.client.post(self.list_url, self.valid_payload, format='json')
        testimonial = Testimonial.objects.filter(email='mary@example.com').first()
        self.assertIsNotNone(testimonial)
        self.assertEqual(testimonial.status, 'pending')

    def test_submit_missing_name_returns_400(self):
        payload = {**self.valid_payload, 'name': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_email_returns_400(self):
        payload = {**self.valid_payload, 'email': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_submit_invalid_email_returns_400(self):
        payload = {**self.valid_payload, 'email': 'not-an-email'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_submit_short_text_returns_400(self):
        payload = {**self.valid_payload, 'text': 'Too short'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_submit_with_custom_role(self):
        payload = {**self.valid_payload, 'email': 'custom@example.com',
                   'role_custom': 'Church Pastor'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)
        testimonial = Testimonial.objects.filter(email='custom@example.com').first()
        self.assertIsNotNone(testimonial)
        self.assertEqual(testimonial.display_role, 'Church Pastor')

    # ------------------------------------------------------------------ #
    # Admin: pending list                                                  #
    # ------------------------------------------------------------------ #

    def test_public_cannot_view_pending(self):
        response = self.client.get(self.pending_url)
        self.assertEqual(response.status_code, drf_status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_pending(self):
        self.client.force_authenticate(user=self.admin)
        self._create_testimonial(status='pending')
        response = self.client.get(self.pending_url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertGreaterEqual(len(results), 1)

    def test_pending_list_excludes_approved_and_rejected(self):
        self.client.force_authenticate(user=self.admin)
        self._create_testimonial(status='pending', name='Pending',
                                 email='p@example.com')
        self._create_testimonial(status='approved', name='Approved',
                                 email='a@example.com')
        self._create_testimonial(status='rejected', name='Rejected',
                                 email='r@example.com')
        response = self.client.get(self.pending_url)
        results = self._get_results(response)
        names = [t['name'] for t in results]
        self.assertIn('Pending', names)
        self.assertNotIn('Approved', names)
        self.assertNotIn('Rejected', names)

    # ------------------------------------------------------------------ #
    # Admin: approve                                                       #
    # ------------------------------------------------------------------ #

    def test_admin_can_approve_testimonial(self):
        self.client.force_authenticate(user=self.admin)
        testimonial = self._create_testimonial(status='pending')
        url = reverse('testimonial-approve', args=[testimonial.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, 'approved')
        self.assertIsNotNone(testimonial.approved_at)

    def test_approved_testimonial_appears_in_public_list(self):
        self.client.force_authenticate(user=self.admin)
        testimonial = self._create_testimonial(status='pending', name='Soon Public',
                                               email='soon@example.com')
        url = reverse('testimonial-approve', args=[testimonial.id])
        self.client.patch(url)

        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        results = self._get_results(response)
        names = [t['name'] for t in results]
        self.assertIn('Soon Public', names)

    def test_public_cannot_approve(self):
        testimonial = self._create_testimonial(status='pending')
        url = reverse('testimonial-approve', args=[testimonial.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, drf_status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------ #
    # Admin: reject                                                        #
    # ------------------------------------------------------------------ #

    def test_admin_can_reject_testimonial(self):
        self.client.force_authenticate(user=self.admin)
        testimonial = self._create_testimonial(status='pending')
        url = reverse('testimonial-reject', args=[testimonial.id])
        response = self.client.patch(url, {'notes': 'Spam submission'}, format='json')
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, 'rejected')
        self.assertEqual(testimonial.notes, 'Spam submission')

    def test_rejected_testimonial_not_in_public_list(self):
        self.client.force_authenticate(user=self.admin)
        testimonial = self._create_testimonial(status='pending', name='Rejected Person',
                                               email='rej@example.com')
        url = reverse('testimonial-reject', args=[testimonial.id])
        self.client.patch(url)

        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        results = self._get_results(response)
        names = [t['name'] for t in results]
        self.assertNotIn('Rejected Person', names)

    def test_public_cannot_reject(self):
        testimonial = self._create_testimonial(status='pending')
        url = reverse('testimonial-reject', args=[testimonial.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, drf_status.HTTP_403_FORBIDDEN)