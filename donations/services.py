"""Domain services for donation workflows."""

import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Donation
from .gateways import MPesaGatewayAdapter
from core.audit import log_audit_event
from core.notification_service import queue_template_email


logger = logging.getLogger(__name__)


class DonationService:
    """Encapsulates payment-domain side effects and state transitions."""

    mpesa_gateway = MPesaGatewayAdapter()

    @staticmethod
    def _link_donation_to_stripe_callback(callback_data: dict) -> Donation | None:
        payment_intent = callback_data.get('data', {}).get('object', {})
        payment_intent_id = payment_intent.get('id')
        if not payment_intent_id:
            return None
        return Donation.objects.filter(stripe_payment_intent=payment_intent_id).first()

    @staticmethod
    def _link_donation_to_mpesa_callback(callback_data: dict) -> Donation | None:
        result = DonationService.mpesa_gateway.verify_callback(callback_data)
        donation = None
        if result.get('checkout_request_id'):
            donation = Donation.objects.filter(mpesa_checkout_request_id=result['checkout_request_id']).first()
        if donation is None and result.get('merchant_request_id'):
            donation = Donation.objects.filter(mpesa_merchant_request_id=result['merchant_request_id']).first()
        if donation is None:
            donation = Donation.objects.filter(
                mpesa_phone=result['phone_number'],
                amount=result['amount'],
                status__in=['pending', 'processing'],
            ).first()
        return donation

    @staticmethod
    def link_donation_to_callback(provider: str, callback_data: dict) -> Donation | None:
        if provider == 'stripe':
            return DonationService._link_donation_to_stripe_callback(callback_data)
        if provider == 'mpesa':
            return DonationService._link_donation_to_mpesa_callback(callback_data)
        return None

    @staticmethod
    def initiate_mpesa_payment(
        donation: Donation,
        *,
        donor_phone: str,
        amount,
        purpose: str,
    ) -> dict:
        """Initiate an M-Pesa STK push and persist resulting state."""
        try:
            mpesa_response = DonationService.mpesa_gateway.initiate(
                {
                    'phone_number': donor_phone,
                    'amount': amount,
                    'account_reference': f"DON-{donation.id}",
                    'transaction_desc': f"Donation: {purpose or 'General'}".strip(),
                }
            )

            if mpesa_response.get('ResponseCode') == '0':
                donation.status = 'processing'
                donation.mpesa_checkout_request_id = mpesa_response.get('CheckoutRequestID')
                donation.mpesa_merchant_request_id = mpesa_response.get('MerchantRequestID')
                donation.notes = 'M-Pesa prompt sent'
                donation.save(update_fields=[
                    'status',
                    'mpesa_checkout_request_id',
                    'mpesa_merchant_request_id',
                    'notes',
                    'updated_at',
                ])
                return {
                    'success': True,
                    'status_code': 200,
                    'checkout_request_id': donation.mpesa_checkout_request_id,
                    'merchant_request_id': donation.mpesa_merchant_request_id,
                    'message': 'Please check your phone for M-Pesa prompt',
                }

            donation.status = 'failed'
            donation.notes = f"M-Pesa error: {mpesa_response.get('errorMessage', 'Unknown error')}"
            donation.save(update_fields=['status', 'notes', 'updated_at'])
            return {
                'success': False,
                'status_code': 400,
                'error': 'Failed to initiate M-Pesa payment',
                'message': mpesa_response.get('errorMessage', 'Please try again'),
            }
        except Exception as exc:
            donation.status = 'failed'
            donation.notes = f"Exception: {str(exc)}"
            donation.save(update_fields=['status', 'notes', 'updated_at'])
            return {
                'success': False,
                'status_code': 500,
                'error': 'Failed to process M-Pesa payment',
                'message': str(exc),
            }

    @staticmethod
    def process_mpesa_initiation_job(payload: dict) -> None:
        """Background job handler to initiate M-Pesa outside request path."""
        donation_id = payload.get('donation_id')
        if not donation_id:
            raise ValueError('donation_id is required for M-Pesa initiation job')

        donation = Donation.objects.filter(id=donation_id).first()
        if donation is None:
            raise ValueError(f'Donation not found for M-Pesa initiation job: id={donation_id}')

        result = DonationService.initiate_mpesa_payment(
            donation,
            donor_phone=payload.get('donor_phone', donation.donor_phone),
            amount=payload.get('amount', donation.amount),
            purpose=payload.get('purpose', donation.purpose),
        )
        if not result.get('success'):
            raise RuntimeError(result.get('message', 'M-Pesa initiation failed'))

    @staticmethod
    def send_donation_receipt(donation: Donation) -> None:
        """Send donation receipt and update the sent flag."""
        try:
            queue_template_email(
                'donation_receipt',
                context={
                    'donor_name': donation.donor_name,
                    'receipt_number': donation.receipt_number,
                    'currency': donation.currency,
                    'amount': donation.amount,
                    'completed_at': donation.completed_at.strftime('%Y-%m-%d %H:%M') if donation.completed_at else '',
                    'purpose': donation.purpose or 'General Support',
                    'payment_method': donation.get_payment_method_display(),
                },
                recipient_list=[donation.donor_email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )

            donation.receipt_sent = True
            donation.save(update_fields=['receipt_sent', 'updated_at'])
        except Exception:
            logger.exception("Failed to send donation receipt for donation_id=%s", donation.id)

    @staticmethod
    def process_stripe_event(event: dict) -> None:
        """Apply Stripe webhook events to donation state."""
        event_type = event.get('type')
        payment_intent = event.get('data', {}).get('object', {})
        payment_intent_id = payment_intent.get('id')

        if not payment_intent_id:
            return

        if event_type == 'payment_intent.succeeded':
            with transaction.atomic():
                donation = Donation.objects.select_for_update().filter(
                    stripe_payment_intent=payment_intent_id
                ).first()

                if donation and donation.status != 'completed':
                    donation.status = 'completed'
                    donation.completed_at = timezone.now()
                    donation.stripe_charge_id = payment_intent.get('latest_charge', '')
                    donation.notes = 'Confirmed by Stripe webhook'
                    donation.save()

                    log_audit_event(
                        'donation.completed',
                        target=donation,
                        source='donations.stripe_webhook',
                        metadata={
                            'provider': 'stripe',
                            'payment_intent_id': payment_intent_id,
                            'charge_id': donation.stripe_charge_id,
                        },
                    )

                    DonationService.send_donation_receipt(donation)

        elif event_type == 'payment_intent.payment_failed':
            with transaction.atomic():
                donation = Donation.objects.select_for_update().filter(
                    stripe_payment_intent=payment_intent_id
                ).first()

                if donation and donation.status != 'failed':
                    donation.status = 'failed'
                    donation.notes = 'Stripe payment failed via webhook'
                    donation.save(update_fields=['status', 'notes', 'updated_at'])

    @staticmethod
    def process_mpesa_callback(callback_data: dict) -> dict:
        """Resolve M-Pesa callback to a donation and apply status transitions."""
        result = DonationService.mpesa_gateway.verify_callback(callback_data)

        with transaction.atomic():
            donation = None

            if result.get('checkout_request_id'):
                donation = Donation.objects.select_for_update().filter(
                    mpesa_checkout_request_id=result['checkout_request_id']
                ).first()

            if donation is None and result.get('merchant_request_id'):
                donation = Donation.objects.select_for_update().filter(
                    mpesa_merchant_request_id=result['merchant_request_id']
                ).first()

            if donation is None:
                donation = Donation.objects.select_for_update().filter(
                    mpesa_phone=result['phone_number'],
                    amount=result['amount'],
                    status__in=['pending', 'processing']
                ).first()

            if donation is None:
                return {
                    'success': False,
                    'donation': None,
                    'requires_reconciliation': True,
                    'message': 'Callback accepted but donation could not be linked',
                }

            # Idempotency: once completed, repeated callbacks should not mutate state.
            if donation.status == 'completed':
                return {'success': True, 'donation': donation, 'replayed': True}

            if result.get('success'):
                donation.status = 'completed'
                donation.completed_at = timezone.now()
                donation.mpesa_receipt = result.get('receipt', '') or donation.mpesa_receipt
                if result.get('phone_number'):
                    donation.mpesa_phone = str(result['phone_number'])
                donation.notes = result.get('message', 'M-Pesa payment confirmed by callback')
                donation.save(update_fields=[
                    'status',
                    'completed_at',
                    'mpesa_receipt',
                    'mpesa_phone',
                    'notes',
                    'updated_at',
                ])

                log_audit_event(
                    'donation.completed',
                    target=donation,
                    source='donations.mpesa_callback',
                    metadata={
                        'provider': 'mpesa',
                        'receipt': result.get('receipt', ''),
                        'checkout_request_id': result.get('checkout_request_id', ''),
                        'merchant_request_id': result.get('merchant_request_id', ''),
                    },
                )

                DonationService.send_donation_receipt(donation)
                return {'success': True, 'donation': donation}

            # Non-zero ResultCode means user/provider failure after prompt initiation.
            donation.status = 'failed'
            donation.notes = result.get('message', 'M-Pesa callback indicated failure')
            if result.get('phone_number'):
                donation.mpesa_phone = str(result['phone_number'])
            donation.save(update_fields=['status', 'notes', 'mpesa_phone', 'updated_at'])

            log_audit_event(
                'donation.failed',
                target=donation,
                source='donations.mpesa_callback',
                metadata={
                    'provider': 'mpesa',
                    'checkout_request_id': result.get('checkout_request_id', ''),
                    'merchant_request_id': result.get('merchant_request_id', ''),
                    'reason': result.get('message', ''),
                },
            )
            return {'success': True, 'donation': donation, 'failed': True}
