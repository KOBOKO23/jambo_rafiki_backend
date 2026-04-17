"""
Tests for the newsletter app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import NewsletterSubscriber


class NewsletterSubscriberModelTest(TestCase):

    def setUp(self):
        self.subscriber = NewsletterSubscriber.objects.create(
            email="grace@example.com",
            name="Grace Atieno",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.subscriber), "grace@example.com")

    def test_default_is_active_true(self):
        self.assertTrue(self.subscriber.is_active)

    def test_unsubscribe_method_sets_is_active_false(self):
        self.subscriber.unsubscribe()
        self.subscriber.refresh_from_db()
        self.assertFalse(self.subscriber.is_active)
        self.assertIsNotNone(self.subscriber.unsubscribed_at)

    def test_email_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            NewsletterSubscriber.objects.create(email="grace@example.com")

    def test_subscribed_at_auto_set(self):
        self.assertIsNotNone(self.subscriber.subscribed_at)


class NewsletterAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        self.subscribe_url = reverse('newsletter-list')
        self.unsubscribe_url = reverse('newsletter-unsubscribe')

    # ------------------------------------------------------------------ #
    # Subscribe                                                            #
    # ------------------------------------------------------------------ #

    def test_public_can_subscribe(self):
        response = self.client.post(
            self.subscribe_url,
            {'email': 'new@example.com', 'name': 'New User'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertTrue(
            NewsletterSubscriber.objects.filter(email='new@example.com').exists()
        )

    def test_subscribe_name_optional(self):
        response = self.client.post(
            self.subscribe_url,
            {'email': 'noname@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_subscribe_invalid_email_returns_400(self):
        response = self.client.post(
            self.subscribe_url,
            {'email': 'not-valid'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_already_active_returns_200(self):
        NewsletterSubscriber.objects.create(
            email='exists@example.com', is_active=True
        )
        response = self.client.post(
            self.subscribe_url,
            {'email': 'exists@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('already subscribed', response.data['message'])

    def test_resubscribe_inactive_email(self):
        sub = NewsletterSubscriber.objects.create(
            email='old@example.com', is_active=False
        )
        response = self.client.post(
            self.subscribe_url,
            {'email': 'old@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sub.refresh_from_db()
        self.assertTrue(sub.is_active)

    # ------------------------------------------------------------------ #
    # Unsubscribe                                                          #
    # ------------------------------------------------------------------ #

    def test_public_can_unsubscribe(self):
        NewsletterSubscriber.objects.create(
            email='active@example.com', is_active=True
        )
        response = self.client.post(
            self.unsubscribe_url,
            {'email': 'active@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subscriber = NewsletterSubscriber.objects.get(email='active@example.com')
        self.assertFalse(subscriber.is_active)

    def test_unsubscribe_missing_email_returns_400(self):
        response = self.client.post(self.unsubscribe_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe_unknown_email_returns_200(self):
        response = self.client.post(
            self.unsubscribe_url,
            {'email': 'ghost@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    # Admin                                                                #
    # ------------------------------------------------------------------ #

    def test_public_cannot_list_subscribers(self):
        response = self.client.get(self.subscribe_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_subscribers(self):
        self.client.force_authenticate(user=self.admin)
        NewsletterSubscriber.objects.create(email='one@example.com')
        response = self.client.get(self.subscribe_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)