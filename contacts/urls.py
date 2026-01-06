"""
Contact URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactSubmissionViewSet

router = DefaultRouter()
router.register(r'', ContactSubmissionViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
