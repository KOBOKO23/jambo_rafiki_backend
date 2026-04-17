"""
Volunteer views
"""
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.conf import settings
from core.notification_service import queue_template_email
from core.throttles import PublicFormRateThrottle
from .models import VolunteerApplication
from .serializers import VolunteerApplicationSerializer, VolunteerApplicationDetailSerializer
from .services import VolunteerService


logger = logging.getLogger(__name__)


class VolunteerApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer applications
    """
    queryset = VolunteerApplication.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return VolunteerApplicationDetailSerializer
        return VolunteerApplicationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action == 'create':
            return [PublicFormRateThrottle()]
        return super().get_throttles()
    
    def create(self, request):
        """Create new volunteer application"""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            application = serializer.save()
            
            # Send confirmation to applicant
            self.send_applicant_confirmation(application)
            
            # Notify admin
            self.send_admin_notification(application)
            
            return Response(
                {
                    'message': 'Thank you for your application! We will contact you soon.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Update application status"""
        application = self.get_object()
        new_status = request.data.get('status')

        try:
            application = VolunteerService.update_status(
                application=application,
                new_status=new_status,
                actor=request.user,
            )
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def send_applicant_confirmation(self, application):
        """Send confirmation email to applicant"""
        try:
            queue_template_email(
                'volunteer_confirmation',
                context={
                    'name': application.name,
                    'skills_preview': f"{application.skills[:100]}...",
                    'availability': application.availability,
                    'duration': application.duration,
                },
                recipient_list=[application.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send volunteer confirmation for application_id=%s", application.id)
    
    def send_admin_notification(self, application):
        """Send notification to admin about new application"""
        try:
            queue_template_email(
                'volunteer_admin_notification',
                context={
                    'name': application.name,
                    'email': application.email,
                    'phone': application.phone,
                    'location': application.location,
                    'skills': application.skills,
                    'availability': application.availability,
                    'duration': application.duration,
                    'motivation': application.motivation,
                    'experience': application.experience,
                    'areas_of_interest': application.areas_of_interest,
                    'submitted_at': application.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'admin_url': f"{settings.FRONTEND_URL}/admin/volunteers/volunteerapplication/{application.id}/",
                },
                recipient_list=[settings.ADMIN_EMAIL],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        except Exception:
            logger.exception("Failed to send volunteer admin notification for application_id=%s", application.id)
