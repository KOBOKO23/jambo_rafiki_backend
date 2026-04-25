"""
Contact URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactSubmissionViewSet, ContactSubmission, contact_call_redirect

router = DefaultRouter()
router.register(r'', ContactSubmissionViewSet, basename='contact')

urlpatterns = [
    path('call/', contact_call_redirect, name='contact-call-redirect'),
    path('', include(router.urls)),
]
