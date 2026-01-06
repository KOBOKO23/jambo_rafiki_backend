"""
Volunteer URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VolunteerApplicationViewSet

router = DefaultRouter()
router.register(r'', VolunteerApplicationViewSet, basename='volunteer')

urlpatterns = [
    path('', include(router.urls)),
]
