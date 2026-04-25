"""
Newsletter views — fixed to match actual model fields (is_active, not status)
"""
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.conf import settings
from core.notification_service import queue_template_email
from core.throttles import PublicFormRateThrottle
from .models import NewsletterSubscriber
from .serializers import NewsletterSubscribeSerializer, NewsletterSubscriberSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class NewsletterSubscriberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for newsletter subscribers.

    Public endpoints:
    - POST /api/newsletter/                 Subscribe
    - POST /api/newsletter/unsubscribe/     Unsubscribe by email

    Admin endpoints:
    - GET /api/newsletter/          List all subscribers
    - GET /api/newsletter/{id}/     Retrieve subscriber
    """
    queryset = NewsletterSubscriber.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return NewsletterSubscriberSerializer
        return NewsletterSubscribeSerializer

    def get_permissions(self):
        if self.action in ['create', 'unsubscribe']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action in ['create', 'unsubscribe']:
            return [PublicFormRateThrottle()]
        return super().get_throttles()

    def create(self, request):
        """Subscribe to newsletter"""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email'].lower().strip()
            name = serializer.validated_data.get('name', '')
            source = serializer.validated_data.get('source', '')

            # Handle existing subscriber
            existing = NewsletterSubscriber.objects.filter(email=email).first()
            if existing:
                if existing.is_active:
                    return Response(
                        {'message': 'You are already subscribed to our newsletter.'},
                        status=status.HTTP_200_OK
                    )
                else:
                    # Re-subscribe
                    existing.is_active = True
                    existing.unsubscribed_at = None
                    existing.save()
                    return Response(
                        {'message': 'Welcome back! You have been re-subscribed.'},
                        status=status.HTTP_200_OK
                    )

            # Create new subscriber
            subscriber = NewsletterSubscriber.objects.create(
                email=email,
                name=name,
                source=source,
            )
            self._send_welcome_email(subscriber)

            return Response(
                {'message': 'Thank you for subscribing to our newsletter!'},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def unsubscribe(self, request):
        """Unsubscribe from newsletter"""
        email = request.data.get('email', '').lower().strip()

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use is_active=True (the actual model field)
        subscriber = NewsletterSubscriber.objects.filter(
            email=email, is_active=True
        ).first()

        if subscriber:
            subscriber.unsubscribe()
            return Response({'message': 'You have been unsubscribed successfully.'})

        return Response(
            {'message': 'Email not found or already unsubscribed.'},
            status=status.HTTP_200_OK
        )

    def _send_welcome_email(self, subscriber):
        """Send welcome email to new subscriber"""
        try:
            name = subscriber.name or 'Friend'
            queue_template_email(
                'newsletter_welcome',
                context={'name': name},
                recipient_list=[subscriber.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send newsletter welcome email for subscriber_id=%s", subscriber.id)