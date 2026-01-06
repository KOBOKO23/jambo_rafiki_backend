"""
Volunteer views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from .models import VolunteerApplication
from .serializers import VolunteerApplicationSerializer, VolunteerApplicationDetailSerializer


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
        
        if new_status in dict(VolunteerApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()
            
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def send_applicant_confirmation(self, application):
        """Send confirmation email to applicant"""
        try:
            subject = "Volunteer Application Received - Jambo Rafiki"
            message = f"""
Dear {application.name},

Thank you for your interest in volunteering with Jambo Rafiki Children Orphanage and Church Centre!

We have received your application and will review it carefully. Our team will contact you within 5-7 business days.

Your Application Details:
- Skills: {application.skills[:100]}...
- Availability: {application.availability}
- Duration: {application.duration}

If you have any questions, please feel free to reach out to us.

Blessings,
Jambo Rafiki Team

P.O Box 311 – 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send applicant confirmation: {e}")
    
    def send_admin_notification(self, application):
        """Send notification to admin about new application"""
        try:
            subject = f"New Volunteer Application: {application.name}"
            message = f"""
New volunteer application received:

Name: {application.name}
Email: {application.email}
Phone: {application.phone}
Location: {application.location}

Skills: {application.skills}

Availability: {application.availability}
Duration: {application.duration}

Motivation:
{application.motivation}

Experience:
{application.experience}

Areas of Interest:
{application.areas_of_interest}

---
Submitted at: {application.created_at.strftime('%Y-%m-%d %H:%M:%S')}

View in admin: {settings.FRONTEND_URL}/admin/volunteers/volunteerapplication/{application.id}/
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
