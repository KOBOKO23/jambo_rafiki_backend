"""
Donation views
"""
import stripe
import uuid
import logging
import hashlib
import json
import hmac
from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Min, Max
from django.views.decorators.csrf import csrf_exempt
from .models import Donation, DonationCallback
from .serializers import (
    DonationSerializer,
    DonationDetailSerializer,
    MPesaDonationSerializer,
    StripeDonationSerializer,
    DonationReceiptSerializer
)
from core.job_queue import enqueue_mpesa_initiation
from .gateways import StripeGatewayAdapter
from .services import DonationService
from core.throttles import DonationInitiationRateThrottle, PaymentCallbackRateThrottle
from core.notification_service import queue_template_email


logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security.events')


class DonationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for donations
    """
    queryset = Donation.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return DonationDetailSerializer
        return DonationSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'mpesa', 'mpesa_async', 'mpesa_sync', 'stripe']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action in ['create', 'mpesa', 'mpesa_async', 'mpesa_sync', 'stripe']:
            return [DonationInitiationRateThrottle()]
        return super().get_throttles()

    def _normalize_mpesa_phone(self, donor_phone: str) -> str:
        return DonationService.mpesa_gateway.client.format_phone_number(donor_phone)

    def _create_mpesa_donation(self, data: dict, *, notes: str = '') -> Donation:
        normalized_phone = self._normalize_mpesa_phone(data['donor_phone'])
        transaction_id = f"MPESA-{uuid.uuid4().hex[:12].upper()}"
        donation = Donation.objects.create(
            donor_name=data['donor_name'],
            donor_email=data['donor_email'],
            donor_phone=normalized_phone,
            is_anonymous=data.get('is_anonymous', False),
            amount=data['amount'],
            currency=data.get('currency', 'KES'),
            donation_type=data.get('donation_type', 'one_time'),
            purpose=data.get('purpose', ''),
            message=data.get('message', ''),
            payment_method='mpesa',
            transaction_id=transaction_id,
            mpesa_phone=normalized_phone,
            status='pending',
            notes=notes,
        )
        logger.info('M-Pesa donation created donation_id=%s amount=%s phone=%s', donation.id, donation.amount, normalized_phone)
        return donation

    def _queue_mpesa_initiation(self, donation: Donation, data: dict) -> Response:
        job = enqueue_mpesa_initiation(
            donation_id=donation.id,
            donor_phone=donation.mpesa_phone,
            amount=data['amount'],
            purpose=data.get('purpose', ''),
        )
        return Response({
            'message': 'Please check your phone for M-Pesa prompt',
            'donation_id': donation.id,
            'job_id': job.id,
            'status': donation.status,
            'checkout_request_id': donation.mpesa_checkout_request_id,
            'merchant_request_id': donation.mpesa_merchant_request_id,
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def mpesa(self, request):
        serializer = MPesaDonationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        try:
            donation = self._create_mpesa_donation(data, notes='Queued for asynchronous M-Pesa initiation')
        except ValueError as exc:
            return Response({'donor_phone': [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return self._queue_mpesa_initiation(donation, data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='mpesa-async')
    def mpesa_async(self, request):
        serializer = MPesaDonationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        try:
            donation = self._create_mpesa_donation(data, notes='Queued for asynchronous M-Pesa initiation')
        except ValueError as exc:
            return Response({'donor_phone': [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return self._queue_mpesa_initiation(donation, data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='mpesa-sync')
    def mpesa_sync(self, request):
        serializer = MPesaDonationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        try:
            donation = self._create_mpesa_donation(data)
        except ValueError as exc:
            return Response({'donor_phone': [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        result = DonationService.initiate_mpesa_payment(
            donation,
            donor_phone=data['donor_phone'],
            amount=data['amount'],
            purpose=data.get('purpose', ''),
        )
        if result.get('success'):
            return Response({
                'message': result.get('message', 'Please check your phone for M-Pesa prompt'),
                'donation_id': donation.id,
                'status': donation.status,
                'checkout_request_id': result.get('checkout_request_id'),
                'merchant_request_id': result.get('merchant_request_id'),
            }, status=result.get('status_code', status.HTTP_200_OK))
        return Response({
            'error': result.get('error', 'Failed to initiate M-Pesa payment'),
            'message': result.get('message', 'Please try again'),
        }, status=result.get('status_code', status.HTTP_400_BAD_REQUEST))
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def stripe(self, request):
        serializer = StripeDonationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        transaction_id = f"STRIPE-{uuid.uuid4().hex[:12].upper()}"
        donation = Donation.objects.create(
            donor_name=data['donor_name'],
            donor_email=data['donor_email'],
            is_anonymous=data.get('is_anonymous', False),
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            donation_type=data.get('donation_type', 'one_time'),
            purpose=data.get('purpose', ''),
            message=data.get('message', ''),
            payment_method='stripe',
            transaction_id=transaction_id,
            status='pending'
        )
        try:
            stripe_gateway = StripeGatewayAdapter()
            payment_intent = stripe_gateway.initiate({
                'amount': int(data['amount'] * 100),
                'currency': data['currency'].lower(),
                'description': f"Donation: {data.get('purpose', 'General')}",
                'receipt_email': data['donor_email'],
                'metadata': {
                    'donation_id': donation.id,
                    'donor_name': data['donor_name'],
                },
            })
            donation.status = 'processing'
            donation.stripe_payment_intent = payment_intent['id']
            donation.notes = 'Awaiting Stripe webhook confirmation'
            donation.save()
            return Response({
                'message': 'Payment initiated. Complete the payment in the frontend and wait for webhook confirmation.',
                'donation_id': donation.id,
                'payment_intent_id': payment_intent['id'],
                'client_secret': payment_intent['client_secret'],
                'status': payment_intent['status'],
            }, status=status.HTTP_202_ACCEPTED)
        except stripe.error.StripeError as e:
            donation.status = 'failed'
            donation.notes = f"Stripe error: {str(e)}"
            donation.save()
            return Response({'error': 'Payment failed', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            donation.status = 'failed'
            donation.notes = f"Exception: {str(e)}"
            donation.save()
            return Response({'error': 'Failed to process payment', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def reconciliation(self, request):
        status_counts = {
            row['status']: row['count']
            for row in Donation.objects.values('status').annotate(count=Count('id'))
        }
        processing_threshold = timezone.now() - timedelta(minutes=20)
        stale_processing_qs = Donation.objects.filter(
            status='processing',
            updated_at__lt=processing_threshold,
        ).order_by('updated_at')[:50]
        recent_callbacks = DonationCallback.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        orphan_callbacks_24h = recent_callbacks.filter(donation__isnull=True).count()
        unprocessed_callbacks_24h = recent_callbacks.filter(processed=False).count()
        stale_processing = [
            {
                'id': donation.id,
                'payment_method': donation.payment_method,
                'status': donation.status,
                'created_at': donation.created_at,
                'updated_at': donation.updated_at,
                'transaction_id': donation.transaction_id,
            }
            for donation in stale_processing_qs
        ]
        return Response({
            'generated_at': timezone.now(),
            'donation_status_counts': status_counts,
            'stale_processing_count': len(stale_processing),
            'stale_processing': stale_processing,
            'callbacks_last_24h': {
                'total': recent_callbacks.count(),
                'unprocessed': unprocessed_callbacks_24h,
                'orphans': orphan_callbacks_24h,
            },
        })
    
    def send_donation_receipt(self, donation):
        DonationService.send_donation_receipt(donation)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([PaymentCallbackRateThrottle])
def stripe_webhook(request):
    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    try:
        stripe_gateway = StripeGatewayAdapter()
        event = stripe_gateway.verify_callback(payload, signature)
    except Exception:
        return Response({'error': 'Invalid Stripe webhook signature'}, status=status.HTTP_400_BAD_REQUEST)

    event_id = event.get('id', '')
    payload_hash = hashlib.sha256(payload).hexdigest()
    callback_lookup = {'provider': 'stripe'}
    if event_id:
        callback_lookup['external_id'] = event_id
    else:
        callback_lookup['payload_hash'] = payload_hash

    callback_record, created = DonationCallback.objects.get_or_create(
        **callback_lookup,
        defaults={
            'external_id': event_id,
            'payload_hash': payload_hash,
            'raw_data': event,
            'processed': False,
        },
    )
    if not created and callback_record.processed:
        return Response({'received': True, 'replayed': True}, status=status.HTTP_200_OK)

    if callback_record.raw_data != event:
        callback_record.raw_data = event
    callback_record.payload_hash = payload_hash
    callback_record.save(update_fields=['raw_data', 'payload_hash'])

    DonationService.process_stripe_event(event)
    linked_donation = DonationService.link_donation_to_callback('stripe', event)
    callback_record.donation = linked_donation
    callback_record.processed = True
    callback_record.requires_reconciliation = linked_donation is None
    callback_record.resolved_at = timezone.now()
    callback_record.processing_notes = (
        'Processed Stripe webhook event and linked donation'
        if linked_donation is not None
        else 'Processed Stripe webhook event but donation link is missing'
    )
    callback_record.save(update_fields=[
        'donation', 'processed', 'requires_reconciliation', 'resolved_at', 'processing_notes',
    ])
    return Response({'received': True}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([PaymentCallbackRateThrottle])
def mpesa_callback(request):
    try:
        signature_secret = getattr(settings, 'MPESA_CALLBACK_SIGNATURE_SECRET', '')
        if signature_secret:
            signature_header = getattr(settings, 'MPESA_CALLBACK_SIGNATURE_HEADER', 'X-MPESA-SIGNATURE')
            signature_meta_key = f"HTTP_{signature_header.upper().replace('-', '_')}"
            provided_signature = request.META.get(signature_meta_key, '')
            expected_signature = hmac.new(
                signature_secret.encode('utf-8'),
                request.body,
                hashlib.sha256,
            ).hexdigest()
            if not provided_signature or not hmac.compare_digest(provided_signature, expected_signature):
                security_logger.warning('Rejected M-Pesa callback due to invalid signature')
                return Response({'ResultCode': 1, 'ResultDesc': 'Invalid callback signature'}, status=status.HTTP_403_FORBIDDEN)

        expected_token = settings.MPESA_CALLBACK_TOKEN
        if expected_token and request.GET.get('token') != expected_token:
            security_logger.warning('Rejected M-Pesa callback due to invalid callback token')
            return Response({'ResultCode': 1, 'ResultDesc': 'Unauthorized callback'}, status=status.HTTP_403_FORBIDDEN)

        callback_data = request.data
        canonical_payload = json.dumps(callback_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        payload_hash = hashlib.sha256(canonical_payload).hexdigest()
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        external_id = stk_callback.get('CheckoutRequestID') or ''
        callback_lookup = {'provider': 'mpesa'}
        if external_id:
            callback_lookup['external_id'] = external_id
        else:
            callback_lookup['payload_hash'] = payload_hash

        callback_record, created = DonationCallback.objects.get_or_create(
            **callback_lookup,
            defaults={
                'external_id': external_id,
                'payload_hash': payload_hash,
                'raw_data': callback_data,
                'processed': False,
            }
        )
        if not created and callback_record.processed:
            security_logger.info('Ignored replayed M-Pesa callback external_id=%s', external_id)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted (replay ignored)'}, status=status.HTTP_200_OK)

        callback_record.external_id = external_id
        callback_record.payload_hash = payload_hash
        callback_record.raw_data = callback_data
        callback_record.save(update_fields=['external_id', 'payload_hash', 'raw_data'])

        try:
            processed = DonationService.process_mpesa_callback(callback_data)
            if processed.get('success') and processed.get('donation'):
                callback_record.donation = processed['donation']
                callback_record.processed = True
                callback_record.requires_reconciliation = False
                callback_record.resolved_at = timezone.now()
                callback_record.processing_notes = 'Processed M-Pesa callback'
                callback_record.save(update_fields=['donation', 'processed', 'requires_reconciliation', 'resolved_at', 'processing_notes'])
            else:
                callback_record.processed = False
                callback_record.requires_reconciliation = True
                callback_record.processing_notes = processed.get('message', 'Callback accepted but donation could not be linked')
                callback_record.save(update_fields=['processed', 'requires_reconciliation', 'processing_notes'])
        except Exception:
            logger.exception("Error processing M-Pesa callback")

        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'}, status=status.HTTP_200_OK)

    except Exception:
        logger.exception("M-Pesa callback error")
        return Response({'ResultCode': 1, 'ResultDesc': 'Failed'}, status=status.HTTP_200_OK)


# ── The only change from the previous version: added @csrf_exempt and @authentication_classes([]) ──
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([DonationInitiationRateThrottle])
def bank_transfer_request(request):
    """
    Send bank transfer details privately to donor via email.
    No account details are exposed in the response.
    """
    donor_name = request.data.get('donor_name', '').strip()
    donor_email = request.data.get('donor_email', '').strip()
    amount = request.data.get('amount', '').strip()
    purpose = request.data.get('purpose', 'General Support').strip()

    errors = {}
    if not donor_name:
        errors['donor_name'] = 'This field is required.'
    if not donor_email:
        errors['donor_email'] = 'This field is required.'
    if not amount:
        errors['amount'] = 'This field is required.'
    else:
        try:
            amount_val = float(amount)
            if amount_val < 1:
                errors['amount'] = 'Minimum amount is 1.'
        except ValueError:
            errors['amount'] = 'Enter a valid amount.'

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    reference = f"JR-BANK-{uuid.uuid4().hex[:8].upper()}"

    try:
        queue_template_email(
            'bank_transfer_details',
            context={
                'donor_name':     donor_name,
                'amount':         amount,
                'purpose':        purpose,
                'reference':      reference,
                'account_name':   settings.ORGANIZATION_BANK_ACCOUNT_NAME,
                'account_number': settings.ORGANIZATION_BANK_ACCOUNT_NUMBER,
                'bank_code':      settings.ORGANIZATION_BANK_CODE,
                'branch_code':    settings.ORGANIZATION_BANK_BRANCH_CODE,
                'swift_code':     settings.ORGANIZATION_BANK_SWIFT_CODE,
            },
            recipient_list=[donor_email],
        )
    except Exception:
        logger.exception('Failed to queue bank transfer details email for %s', donor_email)
        return Response(
            {'error': 'Failed to send email. Please try again or contact us directly.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        'message': f'Bank transfer details have been sent to {donor_email}. Please check your inbox.',
        'reference': reference,
    }, status=status.HTTP_200_OK)