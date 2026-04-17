"""
Tests for the volunteers app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import VolunteerApplication


class VolunteerApplicationModelTest(TestCase):

    def setUp(self):
        self.application = VolunteerApplication.objects.create(
            name="David Mwangi",
            email="david@example.com",
            phone="0712345678",
            location="Nairobi, Kenya",
            skills="Teaching and mentoring children",
            availability="weekends",
            duration="3 months",
            motivation="I want to make a difference in these children's lives.",
        )

    def test_str_representation(self):
        self.assertIn("David Mwangi", str(self.application))
        self.assertIn("Pending", str(self.application))

    def test_default_status_pending(self):
        self.assertEqual(self.application.status, 'pending')

    def test_ordering_latest_first(self):
        second = VolunteerApplication.objects.create(
            name="Ann Chebet",
            email="ann@example.com",
            phone="0711111111",
            location="Kisumu, Kenya",
            skills="Medical care",
            availability="flexible",
            duration="1 month",
            motivation="I have medical skills to share with the community.",
        )
        applications = VolunteerApplication.objects.all()
        self.assertEqual(applications[0], second)


class VolunteerAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        # basename='volunteer' → URL names are volunteer-list, volunteer-detail etc.
        self.list_url = reverse('volunteer-list')
        self.valid_payload = {
            "name": "David Mwangi",
            "email": "david@example.com",
            "phone": "0712345678",
            "location": "Nairobi, Kenya",
            "skills": "Teaching and mentoring",
            "availability": "weekends",
            "duration": "3 months",
            "motivation": "I want to help the children and support their education.",
        }

    def _create_application(self):
        return VolunteerApplication.objects.create(
            name='Test Person',
            email='testperson@example.com',
            phone='0700000000',
            location='Nairobi',
            skills='Cooking',
            availability='flexible',
            duration='1 month',
            motivation='I want to support the children in any way I can.',
        )

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    def test_public_can_submit_application(self):
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_submit_creates_pending_record(self):
        self.client.post(self.list_url, self.valid_payload, format='json')
        application = VolunteerApplication.objects.filter(email='david@example.com').first()
        self.assertIsNotNone(application)
        self.assertEqual(application.status, 'pending')

    def test_submit_missing_name_returns_400(self):
        payload = {**self.valid_payload, 'name': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_skills_returns_400(self):
        payload = {**self.valid_payload, 'skills': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_short_motivation_returns_400(self):
        payload = {**self.valid_payload, 'motivation': 'help'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_invalid_email_returns_400(self):
        payload = {**self.valid_payload, 'email': 'bad-email'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_experience_and_areas_optional(self):
        payload = {k: v for k, v in self.valid_payload.items()
                   if k not in ('experience', 'areas_of_interest')}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ------------------------------------------------------------------ #
    # Admin                                                                #
    # ------------------------------------------------------------------ #

    def test_public_cannot_list_applications(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_applications(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_update_status_to_approved(self):
        self.client.force_authenticate(user=self.admin)
        application = self._create_application()
        url = reverse('volunteer-update-status', args=[application.id])
        response = self.client.patch(url, {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')

    def test_admin_can_update_status_to_rejected(self):
        self.client.force_authenticate(user=self.admin)
        application = self._create_application()
        url = reverse('volunteer-update-status', args=[application.id])
        response = self.client.patch(url, {'status': 'rejected'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, 'rejected')

    def test_invalid_status_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        application = self._create_application()
        url = reverse('volunteer-update-status', args=[application.id])
        response = self.client.patch(url, {'status': 'flying'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_cannot_update_status(self):
        application = self._create_application()
        url = reverse('volunteer-update-status', args=[application.id])
        response = self.client.patch(url, {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)