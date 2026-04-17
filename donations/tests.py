"""
Tests for the donations app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from decimal import Decimal
import hmac
import hashlib
from .models import Donation, DonationCallback


class DonationModelTest(TestCase):

    def setUp(self):
        self.donation = Donation.objects.create(
            donor_name="Jane Wanjiku",
            donor_email="jane@example.com",
            donor_phone="0712345678",
            amount=Decimal("1000.00"),
            currency="KES",
            payment_method="mpesa",
            transaction_id="MPESA-TEST-001",
            status="pending",
        )

    def test_str_representation(self):
        self.assertIn("Jane Wanjiku", str(self.donation))
        self.assertIn("pending", str(self.donation))

    def test_receipt_number_generated_on_completion(self):
        self.donation.status = 'completed'
        self.donation.save()
        self.donation.refresh_from_db()
        self.assertTrue(self.donation.receipt_number.startswith("JR-"))

    def test_receipt_number_not_overwritten_if_already_set(self):
        self.donation.status = 'completed'
        self.donation.save()
        original = self.donation.receipt_number
        self.donation.save()
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.receipt_number, original)

    def test_receipt_number_not_set_for_pending(self):
        self.assertIsNone(self.donation.receipt_number)

    def test_ordering_latest_first(self):
        second = Donation.objects.create(
            donor_name="Peter Otieno",
            donor_email="peter@example.com",
            amount=Decimal("500.00"),
            currency="KES",
            payment_method="cash",
            transaction_id="CASH-TEST-002",
            status="failed",       # failed = never generate receipt number, but should still be ordered by created_at
        )
        donations = Donation.objects.all()
        self.assertEqual(donations[0], second)

    def test_anonymous_donation_flag(self):
        self.donation.is_anonymous = True
        self.donation.save()
        self.assertTrue(self.donation.is_anonymous)


class DonationAPITest(APITestCase):

    def setUp(self):
        # enforce_csrf_checks=False bypasses CSRF from SessionAuthentication
        self.client = APIClient(enforce_csrf_checks=False)
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass', email='admin@example.com'
        )
        self.list_url = reverse('donation-list')
        self.mpesa_url = reverse('donation-mpesa')
        self.mpesa_async_url = reverse('donation-mpesa-async')
        self.mpesa_sync_url = reverse('donation-mpesa-sync')
        self.stripe_url = reverse('donation-stripe')
        self.callback_url = reverse('mpesa-callback')

    def test_public_cannot_list_donations(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_donations(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    # M-Pesa                                                               #
    # ------------------------------------------------------------------ #

    @patch('donations.services.DonationService.mpesa_gateway.initiate')
    def test_mpesa_donation_success(self, mock_mpesa_initiate):
        mock_mpesa_initiate.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'ws_CO_123',
            'MerchantRequestID': 'mr_123',
        }
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_sync_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('checkout_request_id', response.data)

    @patch('donations.services.DonationService.mpesa_gateway.initiate')
    def test_mpesa_donation_failure_from_safaricom(self, mock_mpesa_initiate):
        mock_mpesa_initiate.return_value = {
            'ResponseCode': '1',
            'errorMessage': 'Insufficient funds',
        }
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_sync_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('donations.services.DonationService.mpesa_gateway.initiate')
    def test_mpesa_donation_exception_handled(self, mock_mpesa_initiate):
        mock_mpesa_initiate.side_effect = Exception("Network timeout")
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_sync_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_mpesa_donation_invalid_amount(self):
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "0.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_sync_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mpesa_donation_missing_phone(self):
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_sync_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('donations.views.enqueue_mpesa_initiation')
    def test_mpesa_default_is_queue_backed(self, mock_enqueue):
        mock_job = MagicMock()
        mock_job.id = 321
        mock_enqueue.return_value = mock_job

        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['job_id'], 321)
        self.assertEqual(response.data['message'], 'Please check your phone for M-Pesa prompt')
        self.assertIn('checkout_request_id', response.data)
        self.assertIn('merchant_request_id', response.data)

    @patch('donations.views.enqueue_mpesa_initiation')
    def test_mpesa_async_queues_background_job(self, mock_enqueue):
        mock_job = MagicMock()
        mock_job.id = 123
        mock_enqueue.return_value = mock_job

        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_async_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('job_id', response.data)
        self.assertEqual(response.data['job_id'], 123)
        self.assertEqual(response.data['message'], 'Please check your phone for M-Pesa prompt')
        mock_enqueue.assert_called_once()

    @patch('donations.views.enqueue_mpesa_initiation')
    def test_mpesa_rejects_invalid_phone_format(self, mock_enqueue):
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "123",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('donor_phone', response.data)
        mock_enqueue.assert_not_called()

    @patch('donations.views.enqueue_mpesa_initiation')
    def test_mpesa_normalizes_phone_to_254_format(self, mock_enqueue):
        mock_job = MagicMock()
        mock_job.id = 901
        mock_enqueue.return_value = mock_job
        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "donor_phone": "0712345678",
            "amount": "500.00",
            "currency": "KES",
        }
        response = self.client.post(self.mpesa_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        donation = Donation.objects.get(id=response.data['donation_id'])
        self.assertEqual(donation.donor_phone, '254712345678')
        self.assertEqual(donation.mpesa_phone, '254712345678')

    # ------------------------------------------------------------------ #
    # Stripe                                                               #
    # stripe is imported inside the view function so patch at module level #
    # ------------------------------------------------------------------ #

    @patch('stripe.PaymentIntent')
    def test_stripe_donation_initiation(self, mock_payment_intent):
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test_123'
        mock_intent.client_secret = 'cs_test_123'
        mock_intent.status = 'requires_payment_method'
        mock_payment_intent.create.return_value = mock_intent

        payload = {
            "donor_name": "Jane Wanjiku",
            "donor_email": "jane@example.com",
            "amount": "50.00",
            "currency": "USD",
        }
        with self.settings(STRIPE_SECRET_KEY='sk_test_dummy'):
            response = self.client.post(self.stripe_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('client_secret', response.data)
        self.assertEqual(response.data['status'], 'requires_payment_method')

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_marks_donation_completed(self, mock_construct_event):
        donation = Donation.objects.create(
            donor_name="Jane Wanjiku",
            donor_email="jane@example.com",
            amount=Decimal("50.00"),
            currency="USD",
            payment_method="stripe",
            transaction_id="STRIPE-TEST-001",
            stripe_payment_intent='pi_test_123',
            status='processing',
        )
        mock_construct_event.return_value = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'latest_charge': 'ch_test_123',
                }
            }
        }

        with self.settings(STRIPE_SECRET_KEY='sk_test_dummy', STRIPE_WEBHOOK_SECRET='whsec_test_dummy'):
            from rest_framework.test import APIRequestFactory
            from donations.views import stripe_webhook

            factory = APIRequestFactory(enforce_csrf_checks=False)
            request = factory.post('/api/donations/stripe-webhook/', {}, format='json')
            request.META['HTTP_STRIPE_SIGNATURE'] = 'sig_test_123'
            response = stripe_webhook(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'completed')
        self.assertEqual(donation.stripe_charge_id, 'ch_test_123')

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_replay_is_ignored(self, mock_construct_event):
        donation = Donation.objects.create(
            donor_name="Replay Donor",
            donor_email="replay@example.com",
            amount=Decimal("75.00"),
            currency="USD",
            payment_method="stripe",
            transaction_id="STRIPE-REPLAY-001",
            stripe_payment_intent='pi_replay_123',
            status='processing',
        )
        mock_construct_event.return_value = {
            'id': 'evt_replay_123',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_replay_123',
                    'latest_charge': 'ch_replay_123',
                }
            }
        }

        with self.settings(STRIPE_SECRET_KEY='sk_test_dummy', STRIPE_WEBHOOK_SECRET='whsec_test_dummy'):
            from rest_framework.test import APIRequestFactory
            from donations.views import stripe_webhook

            factory = APIRequestFactory(enforce_csrf_checks=False)
            request1 = factory.post('/api/donations/stripe-webhook/', {}, format='json')
            request1.META['HTTP_STRIPE_SIGNATURE'] = 'sig_test_123'
            response1 = stripe_webhook(request1)

            request2 = factory.post('/api/donations/stripe-webhook/', {}, format='json')
            request2.META['HTTP_STRIPE_SIGNATURE'] = 'sig_test_123'
            response2 = stripe_webhook(request2)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'completed')
        self.assertEqual(DonationCallback.objects.filter(provider='stripe', external_id='evt_replay_123').count(), 1)

    # ------------------------------------------------------------------ #
    # M-Pesa callback                                                      #
    # ------------------------------------------------------------------ #

    def test_mpesa_callback_always_returns_200(self):
        """M-Pesa expects 200 even on bad/empty payloads.
        Call view directly to bypass Django CSRF middleware stack."""
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback
        factory = APIRequestFactory(enforce_csrf_checks=False)
        request = factory.post('/api/donations/mpesa-callback/', {}, format='json')
        response = mpesa_callback(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mpesa_callback_success_payload(self):
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback
        donation = Donation.objects.create(
            donor_name="Jane Wanjiku",
            donor_email="jane@example.com",
            donor_phone="254712345678",
            amount=Decimal("500.00"),
            currency="KES",
            payment_method="mpesa",
            transaction_id="MPESA-PENDING-001",
            mpesa_phone="254712345678",
            status="processing",
        )
        payload = {
            "Body": {
                "stkCallback": {
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 500},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    }
                }
            }
        }
        factory = APIRequestFactory(enforce_csrf_checks=False)
        request = factory.post('/api/donations/mpesa-callback/', payload, format='json')
        response = mpesa_callback(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ResultCode'], 0)
        donation.refresh_from_db()
        self.assertEqual(donation.transaction_id, 'MPESA-PENDING-001')

    def test_mpesa_callback_unmatched_marks_reconciliation_needed(self):
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback

        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_unknown_001",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 999},
                            {"Name": "MpesaReceiptNumber", "Value": "UNMATCHED001"},
                            {"Name": "PhoneNumber", "Value": 254700000001},
                        ]
                    }
                }
            }
        }
        factory = APIRequestFactory(enforce_csrf_checks=False)
        request = factory.post('/api/donations/mpesa-callback/', payload, format='json')
        response = mpesa_callback(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        callback = DonationCallback.objects.filter(provider='mpesa', external_id='ws_CO_unknown_001').first()
        self.assertIsNotNone(callback)
        self.assertFalse(callback.processed)
        self.assertTrue(callback.requires_reconciliation)

    def test_mpesa_callback_failure_marks_donation_failed(self):
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback

        donation = Donation.objects.create(
            donor_name="Failure Donor",
            donor_email="failure@example.com",
            donor_phone="254712345678",
            amount=Decimal("500.00"),
            currency="KES",
            payment_method="mpesa",
            transaction_id="MPESA-PENDING-FAILED-001",
            mpesa_phone="254712345678",
            status="processing",
            mpesa_checkout_request_id='ws_CO_failed_001',
        )

        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_failed_001",
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 500},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    }
                }
            }
        }

        factory = APIRequestFactory(enforce_csrf_checks=False)
        request = factory.post('/api/donations/mpesa-callback/', payload, format='json')
        response = mpesa_callback(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'failed')

    def test_mpesa_callback_replay_is_ignored(self):
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback
        Donation.objects.create(
            donor_name="Jane Wanjiku",
            donor_email="jane@example.com",
            donor_phone="254712345678",
            amount=Decimal("500.00"),
            currency="KES",
            payment_method="mpesa",
            transaction_id="MPESA-PENDING-REPLAY-001",
            mpesa_phone="254712345678",
            status="processing",
            mpesa_checkout_request_id='ws_CO_replay_001',
        )
        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_replay_001",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 500},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    }
                }
            }
        }

        factory = APIRequestFactory(enforce_csrf_checks=False)
        request1 = factory.post('/api/donations/mpesa-callback/', payload, format='json')
        response1 = mpesa_callback(request1)
        request2 = factory.post('/api/donations/mpesa-callback/', payload, format='json')
        response2 = mpesa_callback(request2)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['ResultCode'], 0)
        self.assertIn('replay', response2.data['ResultDesc'].lower())
        self.assertEqual(
            DonationCallback.objects.filter(provider='mpesa', external_id='ws_CO_replay_001').count(),
            1,
        )

    def test_mpesa_callback_signature_required_and_validated(self):
        from rest_framework.test import APIRequestFactory
        from donations.views import mpesa_callback

        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_sig_001",
                    "ResultCode": 0,
                    "ResultDesc": "ok",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 500},
                            {"Name": "MpesaReceiptNumber", "Value": "SIG001"},
                            {"Name": "PhoneNumber", "Value": 254700000001},
                        ]
                    }
                }
            }
        }

        secret = 'callback-signature-secret'

        factory = APIRequestFactory(enforce_csrf_checks=False)
        with self.settings(MPESA_CALLBACK_SIGNATURE_SECRET=secret):
            invalid_request = factory.post('/api/donations/mpesa-callback/', payload, format='json')
            invalid_request.META['HTTP_X_MPESA_SIGNATURE'] = 'bad-signature'
            invalid_response = mpesa_callback(invalid_request)
            self.assertEqual(invalid_response.status_code, status.HTTP_403_FORBIDDEN)

            valid_request = factory.post('/api/donations/mpesa-callback/', payload, format='json')
            signature = hmac.new(secret.encode('utf-8'), valid_request.body, hashlib.sha256).hexdigest()
            valid_request.META['HTTP_X_MPESA_SIGNATURE'] = signature
            valid_response = mpesa_callback(valid_request)
            self.assertEqual(valid_response.status_code, status.HTTP_200_OK)


class DonationCallbackModelTest(TestCase):

    def test_callback_str(self):
        callback = DonationCallback.objects.create(
            provider='mpesa',
            raw_data={'test': 'data'},
        )
        self.assertIn('mpesa', str(callback))