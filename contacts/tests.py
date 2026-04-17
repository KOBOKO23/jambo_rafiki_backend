"""
Tests for the contacts app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import ContactSubmission


class ContactSubmissionModelTest(TestCase):

    def setUp(self):
        self.submission = ContactSubmission.objects.create(
            name="John Omondi",
            email="john@example.com",
            subject="Test Subject",
            message="This is a test message for the contact form.",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.submission), "John Omondi - Test Subject")

    def test_default_is_read_false(self):
        self.assertFalse(self.submission.is_read)

    def test_mark_as_read(self):
        self.submission.mark_as_read()
        self.assertTrue(self.submission.is_read)

    def test_ordering_latest_first(self):
        second = ContactSubmission.objects.create(
            name="Mary Achieng",
            email="mary@example.com",
            subject="Another Subject",
            message="Another test message here.",
        )
        submissions = ContactSubmission.objects.all()
        self.assertEqual(submissions[0], second)

    def test_created_at_auto_set(self):
        self.assertIsNotNone(self.submission.created_at)

    def test_updated_at_auto_set(self):
        self.assertIsNotNone(self.submission.updated_at)


class ContactSubmissionAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        self.list_url = reverse('contact-list')
        self.valid_payload = {
            "name": "John Omondi",
            "email": "john@example.com",
            "subject": "Inquiry about programs",
            "message": "I would like to know more about your programs.",
        }

    def test_public_can_submit_contact_form(self):
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_submit_creates_correct_record(self):
        self.client.post(self.list_url, self.valid_payload, format='json')
        submission = ContactSubmission.objects.filter(email='john@example.com').first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.name, "John Omondi")
        self.assertFalse(submission.is_read)

    def test_submit_missing_name_returns_400(self):
        payload = {**self.valid_payload, 'name': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_email_returns_400(self):
        payload = {**self.valid_payload, 'email': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_invalid_email_returns_400(self):
        payload = {**self.valid_payload, 'email': 'not-an-email'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_short_message_returns_400(self):
        payload = {**self.valid_payload, 'message': 'Hi'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_subject_returns_400(self):
        payload = {**self.valid_payload, 'subject': ''}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_cannot_list_submissions(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_cannot_retrieve_submission(self):
        submission = ContactSubmission.objects.create(
            name='Test', email='test@example.com',
            subject='Test', message='Test message content here.'
        )
        url = reverse('contact-detail', args=[submission.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_submissions(self):
        self.client.force_authenticate(user=self.admin)
        ContactSubmission.objects.create(
            name='Test', email='test@example.com',
            subject='Test', message='Test message content here.'
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # View uses pagination — results are in response.data['results']
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_admin_can_retrieve_submission(self):
        self.client.force_authenticate(user=self.admin)
        submission = ContactSubmission.objects.create(
            name='Test', email='test@example.com',
            subject='Test', message='Test message content here.'
        )
        url = reverse('contact-detail', args=[submission.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test')

    def test_admin_can_mark_as_read(self):
        self.client.force_authenticate(user=self.admin)
        submission = ContactSubmission.objects.create(
            name='Test', email='test@example.com',
            subject='Test', message='Test message content here.'
        )
        url = reverse('contact-mark-read', args=[submission.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.is_read)

    def test_public_cannot_mark_as_read(self):
        submission = ContactSubmission.objects.create(
            name='Test', email='test@example.com',
            subject='Test', message='Test message content here.'
        )
        url = reverse('contact-mark-read', args=[submission.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)