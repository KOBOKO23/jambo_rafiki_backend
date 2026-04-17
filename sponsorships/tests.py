"""
Tests for the sponsorships app
-- Real models: Child, Sponsor, Sponsorship, SponsorshipInterest
   Real endpoints: /children/, /sponsors/, /sponsorships/, /interest/
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch
from decimal import Decimal
import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest


class ChildModelTest(TestCase):

    def setUp(self):
        self.child = Child.objects.create(
            first_name="Grace",
            last_name="Atieno",
            date_of_birth=datetime.date(2015, 6, 1),
            gender="F",
            bio="Grace loves reading and singing.",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.child), "Grace Atieno")

    def test_age_property(self):
        self.assertIsInstance(self.child.age, int)
        self.assertGreater(self.child.age, 0)

    def test_default_not_sponsored(self):
        self.assertFalse(self.child.is_sponsored)

    def test_default_needs_sponsor(self):
        self.assertTrue(self.child.needs_sponsor)


class SponsorModelTest(TestCase):

    def setUp(self):
        self.sponsor = Sponsor.objects.create(
            name="Hope Foundation",
            email="hope@foundation.org",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.sponsor), "Hope Foundation")


class SponsorshipModelTest(TestCase):

    def setUp(self):
        self.child = Child.objects.create(
            first_name="David", last_name="Ochieng",
            date_of_birth=datetime.date(2013, 3, 15),
            gender="M", bio="David loves football.",
        )
        self.sponsor = Sponsor.objects.create(
            name="Good Samaritan", email="good@samaritan.org"
        )
        self.sponsorship = Sponsorship.objects.create(
            child=self.child,
            sponsor=self.sponsor,
            monthly_amount=Decimal("50.00"),
            currency="USD",
            status="active",
            start_date=datetime.date.today(),
        )

    def test_str_representation(self):
        self.assertIn("Good Samaritan", str(self.sponsorship))
        self.assertIn("David", str(self.sponsorship))

    def test_default_status_pending(self):
        second_sponsor = Sponsor.objects.create(
            name="Second Sponsor", email="second@samaritan.org"
        )
        new = Sponsorship.objects.create(
            child=self.child,
            sponsor=second_sponsor,
            monthly_amount=Decimal("30.00"),
            currency="USD",
            start_date=datetime.date.today(),
        )
        self.assertEqual(new.status, 'pending')

    def test_unique_child_sponsor_pair(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Sponsorship.objects.create(
                child=self.child,
                sponsor=self.sponsor,
                monthly_amount=Decimal("60.00"),
                currency="USD",
                start_date=datetime.date.today(),
            )


class SponsorshipInterestModelTest(TestCase):

    def setUp(self):
        self.interest = SponsorshipInterest.objects.create(
            name="Jane Wanjiku",
            email="jane@example.com",
            phone="0712345678",
            preferred_level="Basic",
        )

    def test_str_representation(self):
        self.assertIn("Jane Wanjiku", str(self.interest))
        self.assertIn("Basic", str(self.interest))


class SponsorshipAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        self.children_url = reverse('child-list')
        self.interest_url = reverse('register-interest')
        self.child = Child.objects.create(
            first_name="Test", last_name="Child",
            date_of_birth=datetime.date(2014, 1, 1),
            gender="M", bio="Test bio.",
            needs_sponsor=True,
        )

    # ------------------------------------------------------------------ #
    # Children — public read only                                          #
    # ------------------------------------------------------------------ #

    def test_public_can_list_children(self):
        response = self.client.get(self.children_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_child_detail_includes_photo_url(self):
        child = Child.objects.create(
            first_name="Photo",
            last_name="Child",
            date_of_birth=datetime.date(2014, 1, 1),
            gender="F",
            bio="Child with photo.",
            photo=SimpleUploadedFile("child.jpg", b"x", content_type="image/jpeg"),
        )
        response = self.client.get(reverse('child-detail', args=[child.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('photo_url', response.data)
        self.assertTrue(response.data['photo_url'].startswith('http'))

    def test_children_list_only_needs_sponsor(self):
        # Child that doesn't need sponsor should not appear
        Child.objects.create(
            first_name="Sponsored", last_name="Child",
            date_of_birth=datetime.date(2012, 5, 10),
            gender="F", bio="Already sponsored.",
            needs_sponsor=False,
        )
        response = self.client.get(self.children_url)
        results = response.data.get('results', response.data)
        names = [c['first_name'] for c in results]
        self.assertNotIn("Sponsored", names)

    def test_children_list_is_read_only(self):
        response = self.client.post(self.children_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ------------------------------------------------------------------ #
    # Sponsors — admin only                                                #
    # ------------------------------------------------------------------ #

    def test_public_cannot_list_sponsors(self):
        url = reverse('sponsor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_sponsors(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('sponsor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    # Register interest — public POST                                      #
    # ------------------------------------------------------------------ #

    def test_public_can_register_interest(self):
        payload = {
            "name": "Jane Wanjiku",
            "email": "jane@example.com",
            "phone": "0712345678",
            "preferred_level": "Basic",
        }
        response = self.client.post(self.interest_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertTrue(SponsorshipInterest.objects.filter(email='jane@example.com').exists())

    def test_register_interest_missing_name_returns_400(self):
        payload = {
            "email": "jane@example.com",
            "phone": "0712345678",
        }
        response = self.client.post(self.interest_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_interest_invalid_email_returns_400(self):
        payload = {
            "name": "Jane",
            "email": "not-an-email",
            "phone": "0712345678",
        }
        response = self.client.post(self.interest_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SponsorshipCacheInvalidationSignalTest(TestCase):

    def test_child_write_clears_cache(self):
        with patch('sponsorships.signals.cache.clear') as clear_cache:
            Child.objects.create(
                first_name="Signal",
                last_name="Child",
                date_of_birth=datetime.date(2015, 5, 1),
                gender="M",
                bio="Signal bio",
            )
        clear_cache.assert_called_once()