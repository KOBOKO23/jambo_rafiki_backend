"""Admin-only API views for the CMS and operational dashboard."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from contacts.models import ContactSubmission
from donations.models import Donation
from gallery.models import GalleryCategory, GalleryPhoto
from newsletter.models import NewsletterSubscriber
from sponsorships.models import Child, Sponsorship, SponsorshipInterest
from testimonials.models import Testimonial
from volunteers.models import VolunteerApplication

from core.audit import log_audit_event
from core.models import AuditEvent, BackgroundJob, Banner, MediaAsset, NavigationMenu, Page, PageSection
from core.admin_serializers import AuditEventSerializer, BackgroundJobSerializer


class AdminOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        stale_processing_cutoff = now - timedelta(minutes=20)

        donation_status_counts = {
            row['status']: row['count']
            for row in Donation.objects.values('status').annotate(count=Count('id'))
        }
        background_job_counts = {
            row['status']: row['count']
            for row in BackgroundJob.objects.values('status').annotate(count=Count('id'))
        }

        recent_donations = [
            {
                'id': donation.id,
                'donor_name': donation.donor_name,
                'amount': str(donation.amount),
                'currency': donation.currency,
                'status': donation.status,
                'payment_method': donation.payment_method,
                'created_at': donation.created_at,
            }
            for donation in Donation.objects.order_by('-created_at')[:5]
        ]

        recent_testimonials = [
            {
                'id': testimonial.id,
                'name': testimonial.name,
                'display_role': testimonial.display_role,
                'status': testimonial.status,
                'created_at': testimonial.created_at,
            }
            for testimonial in Testimonial.objects.order_by('-created_at')[:5]
        ]

        recent_contacts = [
            {
                'id': contact.id,
                'name': contact.name,
                'subject': contact.subject,
                'is_read': contact.is_read,
                'created_at': contact.created_at,
            }
            for contact in ContactSubmission.objects.order_by('-created_at')[:5]
        ]

        recent_volunteers = [
            {
                'id': application.id,
                'name': application.name,
                'status': application.status,
                'created_at': application.created_at,
            }
            for application in VolunteerApplication.objects.order_by('-created_at')[:5]
        ]

        recent_audit_events = AuditEventSerializer(
            AuditEvent.objects.select_related('actor').order_by('-created_at')[:10],
            many=True,
            context={'request': request},
        ).data

        stale_processing = Donation.objects.filter(
            status='processing',
            updated_at__lt=stale_processing_cutoff,
        ).count()

        return Response({
            'generated_at': now,
            'counts': {
                'donations': {
                    'total': Donation.objects.count(),
                    'pending': donation_status_counts.get('pending', 0),
                    'processing': donation_status_counts.get('processing', 0),
                    'completed': donation_status_counts.get('completed', 0),
                    'failed': donation_status_counts.get('failed', 0),
                    'refunded': donation_status_counts.get('refunded', 0),
                    'cancelled': donation_status_counts.get('cancelled', 0),
                    'stale_processing': stale_processing,
                },
                'contacts': {
                    'total': ContactSubmission.objects.count(),
                    'unread': ContactSubmission.objects.filter(is_read=False).count(),
                },
                'testimonials': {
                    'total': Testimonial.objects.count(),
                    'pending': Testimonial.objects.filter(status='pending').count(),
                    'approved': Testimonial.objects.filter(status='approved').count(),
                    'rejected': Testimonial.objects.filter(status='rejected').count(),
                },
                'volunteers': {
                    'total': VolunteerApplication.objects.count(),
                    'pending': VolunteerApplication.objects.filter(status='pending').count(),
                    'reviewing': VolunteerApplication.objects.filter(status='reviewing').count(),
                    'approved': VolunteerApplication.objects.filter(status='approved').count(),
                    'rejected': VolunteerApplication.objects.filter(status='rejected').count(),
                },
                'newsletter': {
                    'total': NewsletterSubscriber.objects.count(),
                    'active': NewsletterSubscriber.objects.filter(is_active=True).count(),
                    'inactive': NewsletterSubscriber.objects.filter(is_active=False).count(),
                },
                'sponsorships': {
                    'children': Child.objects.count(),
                    'needs_sponsor': Child.objects.filter(needs_sponsor=True).count(),
                    'sponsorships': Sponsorship.objects.count(),
                    'active_sponsorships': Sponsorship.objects.filter(status='active').count(),
                    'interests': SponsorshipInterest.objects.count(),
                },
                'gallery': {
                    'categories': GalleryCategory.objects.filter(is_active=True).count(),
                    'photos': GalleryPhoto.objects.filter(is_active=True).count(),
                    'featured_photos': GalleryPhoto.objects.filter(is_active=True, is_featured=True).count(),
                },
                'cms': {
                    'pages': Page.objects.count(),
                    'published_pages': Page.objects.filter(status=Page.STATUS_PUBLISHED).count(),
                    'draft_pages': Page.objects.filter(status=Page.STATUS_DRAFT).count(),
                    'scheduled_pages': Page.objects.filter(status=Page.STATUS_SCHEDULED).count(),
                    'page_sections': PageSection.objects.count(),
                    'navigation_menus': NavigationMenu.objects.filter(is_active=True).count(),
                    'banners': Banner.objects.filter(is_active=True).count(),
                    'media_assets': MediaAsset.objects.count(),
                },
                'jobs': background_job_counts,
                'audit_events_last_24h': AuditEvent.objects.filter(created_at__gte=now - timedelta(hours=24)).count(),
            },
            'recent': {
                'donations': recent_donations,
                'testimonials': recent_testimonials,
                'contacts': recent_contacts,
                'volunteers': recent_volunteers,
                'audit_events': recent_audit_events,
            },
        })


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related('actor').all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['event_type', 'source', 'target_model', 'target_id', 'metadata']
    ordering_fields = ['created_at', 'event_type']
    ordering = ['-created_at']


class BackgroundJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BackgroundJob.objects.all()
    serializer_class = BackgroundJobSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['job_type', 'status', 'last_error']
    ordering_fields = ['created_at', 'available_at', 'status', 'job_type']
    ordering = ['-created_at']

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        job = self.get_object()
        if job.status != BackgroundJob.STATUS_FAILED:
            return Response({'error': 'Only failed jobs can be retried.'}, status=status.HTTP_400_BAD_REQUEST)

        job.status = BackgroundJob.STATUS_PENDING
        job.attempts = 0
        job.available_at = timezone.now()
        job.last_error = ''
        job.save(update_fields=['status', 'attempts', 'available_at', 'last_error', 'updated_at'])

        log_audit_event(
            'background_job.retried',
            actor=request.user,
            target=job,
            source='core.admin.retry_background_job',
            metadata={'job_type': job.job_type},
        )

        serializer = self.get_serializer(job)
        return Response(serializer.data)