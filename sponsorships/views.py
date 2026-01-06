from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest
from .serializers import (
    ChildSerializer, SponsorSerializer, SponsorshipSerializer,
    SponsorshipInterestSerializer
)

# -------------------------
# Public Views
# -------------------------
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


class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.all()
    serializer_class = SponsorshipSerializer
    permission_classes = [IsAdminUser]


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
            send_mail(
                subject="New Sponsorship Interest",
                message=f"""
Name: {interest.name}
Email: {interest.email}
Phone: {interest.phone}
Preferred Level: {interest.preferred_level or 'Not specified'}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")

        return Response({'message': 'Interest registered successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
