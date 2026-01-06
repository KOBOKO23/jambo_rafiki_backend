"""
Contact views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactSubmission
from .serializers import ContactSubmissionSerializer, ContactSubmissionDetailSerializer


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
        
        serializer = self.get_serializer(submission)
        return Response(serializer.data)
    
    def send_admin_notification(self, submission):
        """Send email notification to admin about new submission"""
        try:
            subject = f"New Contact Form: {submission.subject}"
            message = f"""
New contact form submission received:

From: {submission.name}
Email: {submission.email}
Subject: {submission.subject}

Message:
{submission.message}

---
Submitted at: {submission.created_at.strftime('%Y-%m-%d %H:%M:%S')}

View in admin: {settings.FRONTEND_URL}/admin/contacts/contactsubmission/{submission.id}/
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send admin notification: {e}")
    
    def send_auto_reply(self, submission):
        """Send auto-reply to the submitter"""
        try:
            subject = "Thank you for contacting Jambo Rafiki"
            message = f"""
Dear {submission.name},

Thank you for reaching out to Jambo Rafiki Children Orphanage and Church Centre.

We have received your message and will respond as soon as possible.

Your message:
Subject: {submission.subject}
{submission.message}

---
Blessings,
Jambo Rafiki Team

P.O Box 311 – 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send auto-reply: {e}")
