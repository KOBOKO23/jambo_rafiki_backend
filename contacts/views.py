"""
Contact views
"""
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.conf import settings
from core.audit import log_audit_event
from core.notification_service import queue_template_email
from core.throttles import PublicFormRateThrottle
from .models import ContactSubmission
from .serializers import ContactSubmissionSerializer, ContactSubmissionDetailSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import BasicAuthentication
from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes, api_view, throttle_classes



logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ContactSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for contact form submissions.
    
    Public endpoints:
    - POST: Create new submission (anyone can submit)
    
    Admin endpoints:
    - GET: List all submissions
    - GET: Retrieve specific submission
    - PATCH: Mark as read
    """
    authentication_classes = [BasicAuthentication]
    queryset = ContactSubmission.objects.all()
    
    def get_serializer_class(self):
        """Use detailed serializer for admin, simple for public"""
        if self.action in ['list', 'retrieve']:
            return ContactSubmissionDetailSerializer
        return ContactSubmissionSerializer
    
    def get_permissions(self):
        """Allow anyone to create, require admin for other actions"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action == 'create':
            return [PublicFormRateThrottle()]
        return super().get_throttles()
    
    def create(self, request):
        """Create new contact submission"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            submission = serializer.save()
            
            # Send email notification to admin
            self.send_admin_notification(submission)
            
            # Send auto-reply to submitter
            self.send_auto_reply(submission)
            
            return Response(
                {
                    'message': 'Thank you for your message! We will get back to you soon.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def mark_read(self, request, pk=None):
        """Mark a submission as read"""
        submission = self.get_object()
        submission.mark_as_read()

        log_audit_event(
            'contact.mark_read',
            actor=request.user,
            target=submission,
            source='contacts.viewset.mark_read',
            metadata={'subject': submission.subject, 'email': submission.email},
        )
        
        serializer = self.get_serializer(submission)
        return Response(serializer.data)
    
    def send_admin_notification(self, submission):
        """Send email notification to admin about new submission"""
        try:
            queue_template_email(
                'contact_admin_notification',
                context={
                    'name': submission.name,
                    'email': submission.email,
                    'subject': submission.subject,
                    'message': submission.message,
                    'submitted_at': submission.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'admin_url': f"{settings.FRONTEND_URL}/admin/contacts/contactsubmission/{submission.id}/",
                },
                recipient_list=settings.ADMIN_NOTIFICATION_EMAILS,
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send admin notification for contact_submission_id=%s", submission.id)
    
    def send_auto_reply(self, submission):
        """Send auto-reply to the submitter"""
        try:
            queue_template_email(
                'contact_auto_reply',
                context={
                    'name': submission.name,
                    'subject': submission.subject,
                    'message': submission.message,
                },
                recipient_list=[submission.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send contact auto-reply for contact_submission_id=%s", submission.id)


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([PublicFormRateThrottle])
def contact_call_redirect(request):
    """Redirect to contact page on frontend"""
    phone_number = settings.CONTACT_PHONE_NUMBER
    return HttpResponseRedirect(f"tel:{phone_number}")
