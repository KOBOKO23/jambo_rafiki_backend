"""
Newsletter URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsletterSubscriberViewSet

router = DefaultRouter()
router.register(r'', NewsletterSubscriberViewSet, basename='newsletter')

urlpatterns = [
    path('', include(router.urls)),
]