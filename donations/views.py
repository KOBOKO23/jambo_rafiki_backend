"""
Donation views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Donation, DonationCallback
from .serializers import (
    DonationSerializer,
    DonationDetailSerializer,
    MPesaDonationSerializer,
    StripeDonationSerializer,
    DonationReceiptSerializer
)
from .mpesa import MPesaClient, process_mpesa_callback
import uuid


class DonationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for donations
    """
    queryset = Donation.objects.all()
    
    def get_serializer_class(self):
        """Use detailed serializer for admin, simple for public"""
        if self.action in ['list', 'retrieve']:
            return DonationDetailSerializer
        return DonationSerializer
    
    def get_permissions(self):
        """Allow anyone to create, require admin for other actions"""
        if self.action in ['create', 'mpesa_donation', 'stripe_donation']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def mpesa(self, request):
        """
        Initiate M-Pesa STK Push donation
        
        POST /api/donations/mpesa/
        {
            "donor_name": "John Doe",
            "donor_email": "john@example.com",
            "donor_phone": "0712345678",
            "amount": 1000,
            "purpose": "Education support"
        }
        """
        serializer = MPesaDonationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create donation record
        transaction_id = f"MPESA-{uuid.uuid4().hex[:12].upper()}"
        
        donation = Donation.objects.create(
            donor_name=data['donor_name'],
            donor_email=data['donor_email'],
            donor_phone=data['donor_phone'],
            is_anonymous=data.get('is_anonymous', False),
            amount=data['amount'],
            currency=data.get('currency', 'KES'),
            donation_type=data.get('donation_type', 'one_time'),
            purpose=data.get('purpose', ''),
            message=data.get('message', ''),
            payment_method='mpesa',
            transaction_id=transaction_id,
            mpesa_phone=data['donor_phone'],
            status='pending'
        )
        
        # Initiate M-Pesa STK Push
        try:
            mpesa_client = MPesaClient()
            mpesa_response = mpesa_client.stk_push(
                phone_number=data['donor_phone'],
                amount=data['amount'],
                account_reference=f"DON-{donation.id}",
                transaction_desc=f"Donation: {data.get('purpose', 'General')}".strip()
            )
            
            # Check if STK push was successful
            if mpesa_response.get('ResponseCode') == '0':
                # Update donation with M-Pesa details
                donation.status = 'processing'
                donation.save()
                
                return Response({
                    'message': 'Please check your phone for M-Pesa prompt',
                    'donation_id': donation.id,
                    'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                    'merchant_request_id': mpesa_response.get('MerchantRequestID'),
                }, status=status.HTTP_200_OK)
            else:
                donation.status = 'failed'
                donation.notes = f"M-Pesa error: {mpesa_response.get('errorMessage', 'Unknown error')}"
                donation.save()
                
                return Response({
                    'error': 'Failed to initiate M-Pesa payment',
                    'message': mpesa_response.get('errorMessage', 'Please try again'),
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            donation.status = 'failed'
            donation.notes = f"Exception: {str(e)}"
            donation.save()
            
            return Response({
                'error': 'Failed to process M-Pesa payment',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def stripe(self, request):
        """
        Process Stripe donation
        
        POST /api/donations/stripe/
        {
            "donor_name": "John Doe",
            "donor_email": "john@example.com",
            "amount": 50,
            "currency": "USD",
            "payment_method_id": "pm_xxxxx"
        }
        """
        serializer = StripeDonationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create donation record
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
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(data['amount'] * 100),  # Convert to cents
                currency=data['currency'].lower(),
                payment_method=data['payment_method_id'],
                confirm=True,
                description=f"Donation: {data.get('purpose', 'General')}",
                receipt_email=data['donor_email'],
                metadata={
                    'donation_id': donation.id,
                    'donor_name': data['donor_name'],
                }
            )
            
            if payment_intent.status == 'succeeded':
                donation.status = 'completed'
                donation.completed_at = timezone.now()
                donation.stripe_payment_intent = payment_intent.id
                donation.stripe_charge_id = payment_intent.latest_charge
                donation.save()
                
                # Send receipt
                self.send_donation_receipt(donation)
                
                return Response({
                    'message': 'Donation successful! Thank you for your support.',
                    'donation_id': donation.id,
                    'receipt_number': donation.receipt_number,
                }, status=status.HTTP_200_OK)
            else:
                donation.status = 'failed'
                donation.notes = f"Payment status: {payment_intent.status}"
                donation.save()
                
                return Response({
                    'error': 'Payment not completed',
                    'status': payment_intent.status
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except stripe.error.StripeError as e:
            donation.status = 'failed'
            donation.notes = f"Stripe error: {str(e)}"
            donation.save()
            
            return Response({
                'error': 'Payment failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            donation.status = 'failed'
            donation.notes = f"Exception: {str(e)}"
            donation.save()
            
            return Response({
                'error': 'Failed to process payment',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def send_donation_receipt(self, donation):
        """Send donation receipt email"""
        try:
            subject = f"Donation Receipt - {donation.receipt_number}"
            message = f"""
Dear {donation.donor_name},

Thank you for your generous donation to Jambo Rafiki Children Orphanage and Church Centre!

Donation Details:
Receipt Number: {donation.receipt_number}
Amount: {donation.currency} {donation.amount}
Date: {donation.completed_at.strftime('%Y-%m-%d %H:%M')}
Purpose: {donation.purpose or 'General Support'}
Payment Method: {donation.get_payment_method_display()}

Your contribution helps us provide care, education, and hope to orphaned and vulnerable children in Kenya.

May God bless you abundantly for your generosity!

---
Jambo Rafiki Children Orphanage and Church Centre
P.O Box 311 – 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[donation.donor_email],
                fail_silently=True,
            )
            
            donation.receipt_sent = True
            donation.save()
        
        except Exception as e:
            print(f"Failed to send receipt: {e}")


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    M-Pesa callback endpoint
    
    This endpoint receives payment confirmation from M-Pesa
    """
    try:
        callback_data = request.data
        
        # Store raw callback
        callback_record = DonationCallback.objects.create(
            provider='mpesa',
            raw_data=callback_data
        )
        
        # Process callback
        result = process_mpesa_callback(callback_data)
        
        if result['success']:
            # Find donation by transaction_id or create new one
            try:
                # Try to find existing donation
                donation = Donation.objects.filter(
                    mpesa_phone=result['phone_number'],
                    amount=result['amount'],
                    status__in=['pending', 'processing']
                ).first()
                
                if donation:
                    donation.status = 'completed'
                    donation.completed_at = timezone.now()
                    donation.mpesa_receipt = result['receipt']
                    donation.transaction_id = result['receipt']
                    donation.save()
                    
                    # Link callback to donation
                    callback_record.donation = donation
                    callback_record.processed = True
                    callback_record.save()
                    
                    # Send receipt
                    DonationViewSet().send_donation_receipt(donation)
            
            except Exception as e:
                print(f"Error processing M-Pesa callback: {e}")
        
        # Always return success to M-Pesa
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"M-Pesa callback error: {e}")
        return Response({
            'ResultCode': 1,
            'ResultDesc': 'Failed'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def mpesa_donation(request):
    """
    Handle M-Pesa donation request from frontend
    """
    data = request.data
    # Here you would validate and initiate the M-Pesa STK push
    # For now, just return a dummy response
    return Response({
        "message": "M-Pesa donation request received",
        "donation_id": 1,
        "checkout_request_id": "dummy123",
        "merchant_request_id": "dummy456"
    }, status=status.HTTP_200_OK)
