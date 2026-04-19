import logging

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
from core.audit import log_audit_event
from core.notification_service import queue_template_email
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest
from .serializers import (
    ChildSerializer, SponsorSerializer, SponsorshipSerializer,
    SponsorshipInterestSerializer
)


logger = logging.getLogger(__name__)
PUBLIC_CACHE_TTL = 60 * 5 if not settings.DEBUG else 0

# -------------------------
# Public Views
# -------------------------
@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='list')
@method_decorator(cache_page(PUBLIC_CACHE_TTL), name='retrieve')
class ChildViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Child.objects.filter(needs_sponsor=True)
    serializer_class = ChildSerializer
    permission_classes = [AllowAny]

# -------------------------
# Admin Views
# -------------------------
class SponsorViewSet(viewsets.ModelViewSet):
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        sponsor = serializer.save()
        log_audit_event(
            'sponsor.created',
            actor=self.request.user,
            target=sponsor,
            source='sponsorships.viewset.create_sponsor',
            metadata={'name': sponsor.name, 'email': sponsor.email},
        )

    def perform_update(self, serializer):
        sponsor = serializer.save()
        log_audit_event(
            'sponsor.updated',
            actor=self.request.user,
            target=sponsor,
            source='sponsorships.viewset.update_sponsor',
            metadata={'name': sponsor.name, 'email': sponsor.email},
        )

    def perform_destroy(self, instance):
        log_audit_event(
            'sponsor.deleted',
            actor=self.request.user,
            target=instance,
            source='sponsorships.viewset.delete_sponsor',
            metadata={'name': instance.name, 'email': instance.email},
        )
        return super().perform_destroy(instance)


class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.select_related('child', 'sponsor').all()
    serializer_class = SponsorshipSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        sponsorship = serializer.save()
        log_audit_event(
            'sponsorship.created',
            actor=self.request.user,
            target=sponsorship,
            source='sponsorships.viewset.create_sponsorship',
            metadata={
                'child_id': sponsorship.child_id,
                'sponsor_id': sponsorship.sponsor_id,
                'monthly_amount': str(sponsorship.monthly_amount),
                'currency': sponsorship.currency,
            },
        )

    def perform_update(self, serializer):
        sponsorship = serializer.save()
        log_audit_event(
            'sponsorship.updated',
            actor=self.request.user,
            target=sponsorship,
            source='sponsorships.viewset.update_sponsorship',
            metadata={
                'child_id': sponsorship.child_id,
                'sponsor_id': sponsorship.sponsor_id,
                'status': sponsorship.status,
            },
        )

    def perform_destroy(self, instance):
        log_audit_event(
            'sponsorship.deleted',
            actor=self.request.user,
            target=instance,
            source='sponsorships.viewset.delete_sponsorship',
            metadata={
                'child_id': instance.child_id,
                'sponsor_id': instance.sponsor_id,
                'status': instance.status,
            },
        )
        return super().perform_destroy(instance)


# -------------------------
# Public POST endpoint for interest
# -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register_interest(request):
    serializer = SponsorshipInterestSerializer(data=request.data)
    if serializer.is_valid():
        interest = serializer.save()

        # Send email notification
        try:
            queue_template_email(
                'sponsorship_interest_admin',
                context={
                    'name': interest.name,
                    'email': interest.email,
                    'phone': interest.phone,
                    'preferred_level': interest.preferred_level or 'Not specified',
                },
                recipient_list=settings.ADMIN_NOTIFICATION_EMAILS,
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send sponsorship interest notification for interest_id=%s", interest.id)

        return Response({'message': 'Interest registered successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
