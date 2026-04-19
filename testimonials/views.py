"""
Testimonial views
"""
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.conf import settings
from core.notification_service import queue_template_email
from .models import Testimonial
from .services import TestimonialService
from .serializers import (
    TestimonialSubmitSerializer,
    TestimonialPublicSerializer,
    TestimonialDetailSerializer,
)


logger = logging.getLogger(__name__)


class TestimonialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for testimonials.

    Public endpoints:
    - GET  /api/testimonials/           List approved testimonials only
    - POST /api/testimonials/           Submit a new testimonial (goes to pending)

    Admin endpoints:
    - GET  /api/testimonials/pending/       List pending testimonials
    - PATCH /api/testimonials/{id}/approve/ Approve a testimonial
    - PATCH /api/testimonials/{id}/reject/  Reject a testimonial
    - GET  /api/testimonials/{id}/          Full detail (any status)
    """

    def get_queryset(self):
        """Public gets approved only; admin gets all"""
        if self.request.user and self.request.user.is_staff:
            return Testimonial.objects.all()
        return Testimonial.objects.filter(status='approved').only(
            'id',
            'name',
            'role',
            'role_custom',
            'text',
            'approved_at',
            'created_at',
        ).order_by('-approved_at', '-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return TestimonialSubmitSerializer
        if self.request.user and self.request.user.is_staff:
            return TestimonialDetailSerializer
        return TestimonialPublicSerializer

    def get_permissions(self):
        if self.action in ['list', 'create']:
            return [AllowAny()]
        return [IsAdminUser()]

    def create(self, request):
        """Submit a testimonial — goes to pending, admin must approve"""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            testimonial = serializer.save()
            self._send_admin_notification(testimonial)
            self._send_submitter_confirmation(testimonial)

            return Response(
                {
                    'message': (
                        'Thank you for sharing your story! '
                        'Your testimonial will appear on the site once reviewed.'
                    )
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """List all pending testimonials"""
        queryset = Testimonial.objects.filter(status='pending').order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TestimonialDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TestimonialDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a testimonial — makes it publicly visible"""
        testimonial = self.get_object()
        testimonial = TestimonialService.approve(
            testimonial=testimonial,
            actor=request.user,
        )

        self._send_approval_notification(testimonial)
        serializer = TestimonialDetailSerializer(testimonial)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a testimonial"""
        testimonial = self.get_object()
        testimonial = TestimonialService.reject(
            testimonial=testimonial,
            notes=request.data.get('notes', ''),
            actor=request.user,
        )

        serializer = TestimonialDetailSerializer(testimonial)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    #  Email helpers                                                        #
    # ------------------------------------------------------------------ #

    def _send_admin_notification(self, testimonial):
        """Notify admin that a new testimonial is waiting for review"""
        try:
            queue_template_email(
                'testimonial_admin_pending',
                context={
                    'name': testimonial.name,
                    'role': testimonial.display_role,
                    'email': testimonial.email,
                    'text': testimonial.text,
                    'submitted_at': testimonial.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'admin_url': f"{settings.FRONTEND_URL}/admin/testimonials/testimonial/{testimonial.id}/change/",
                },
                recipient_list=settings.ADMIN_NOTIFICATION_EMAILS,
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send testimonial admin notification for testimonial_id=%s", testimonial.id)

    def _send_submitter_confirmation(self, testimonial):
        """Thank the person for submitting"""
        try:
            queue_template_email(
                'testimonial_submitter_confirmation',
                context={
                    'name': testimonial.name,
                },
                recipient_list=[testimonial.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send testimonial confirmation for testimonial_id=%s", testimonial.id)

    def _send_approval_notification(self, testimonial):
        """Let the person know their testimonial is now live"""
        try:
            queue_template_email(
                'testimonial_approved',
                context={
                    'name': testimonial.name,
                    'frontend_url': settings.FRONTEND_URL,
                },
                recipient_list=[testimonial.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send testimonial approval notification for testimonial_id=%s", testimonial.id)