"""
Newsletter views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from .models import NewsletterSubscriber
from .serializers import (
    NewsletterSubscribeSerializer,
    NewsletterUnsubscribeSerializer,
    NewsletterSubscriberSerializer
)


class NewsletterViewSet(viewsets.ModelViewSet):
    """ViewSet for newsletter management"""
    
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def subscribe(self, request):
        """
        Subscribe to newsletter
        
        POST /api/newsletter/subscribe/
        {
            "email": "user@example.com",
            "name": "John Doe" (optional)
        }
        """
        serializer = NewsletterSubscribeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        name = serializer.validated_data.get('name', '')
        source = serializer.validated_data.get('source', 'website')
        
        # Check if already subscribed
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'source': source,
                'is_active': True
            }
        )
        
        if not created:
            if subscriber.is_active:
                return Response({
                    'message': 'You are already subscribed to our newsletter!'
                }, status=status.HTTP_200_OK)
            else:
                # Reactivate subscription
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                message = 'Welcome back! Your subscription has been reactivated.'
        else:
            message = 'Thank you for subscribing to our newsletter!'
        
        # Send welcome email
        self.send_welcome_email(subscriber)
        
        return Response({
            'message': message
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def unsubscribe(self, request):
        """
        Unsubscribe from newsletter
        
        POST /api/newsletter/unsubscribe/
        {
            "email": "user@example.com"
        }
        """
        serializer = NewsletterUnsubscribeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            
            if not subscriber.is_active:
                return Response({
                    'message': 'You are not currently subscribed.'
                }, status=status.HTTP_200_OK)
            
            subscriber.unsubscribe()
            
            # Send goodbye email
            self.send_unsubscribe_confirmation(subscriber)
            
            return Response({
                'message': 'You have been unsubscribed. We\'re sorry to see you go!'
            }, status=status.HTTP_200_OK)
        
        except NewsletterSubscriber.DoesNotExist:
            return Response({
                'message': 'Email not found in our subscriber list.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def active_subscribers(self, request):
        """Get count of active subscribers"""
        count = NewsletterSubscriber.objects.filter(is_active=True).count()
        return Response({
            'active_subscribers': count
        })
    
    def send_welcome_email(self, subscriber):
        """Send welcome email to new subscriber"""
        try:
            subject = "Welcome to Jambo Rafiki Newsletter!"
            message = f"""
Dear {subscriber.name or 'Friend'},

Thank you for subscribing to the Jambo Rafiki Children Orphanage and Church Centre newsletter!

You'll receive updates about:
- Our children's progress and success stories
- Upcoming events and programs
- Ways to get involved and make a difference
- Prayer requests and blessings

We're grateful to have you as part of our community!

If you ever wish to unsubscribe, you can do so at any time through our website.

Blessings,
Jambo Rafiki Team

P.O Box 311 – 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
    
    def send_unsubscribe_confirmation(self, subscriber):
        """Send confirmation email for unsubscribe"""
        try:
            subject = "Unsubscribed from Jambo Rafiki Newsletter"
            message = f"""
Dear {subscriber.name or 'Friend'},

You have been unsubscribed from the Jambo Rafiki newsletter.

We're sorry to see you go, but we understand. You will no longer receive our updates.

If this was a mistake, you can always resubscribe through our website.

Thank you for your past support!

Blessings,
Jambo Rafiki Team

P.O Box 311 – 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send unsubscribe confirmation: {e}")
