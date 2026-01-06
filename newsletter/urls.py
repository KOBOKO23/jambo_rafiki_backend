"""
Newsletter URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsletterViewSet

router = DefaultRouter()
router.register(r'', NewsletterViewSet, basename='newsletter')

urlpatterns = [
    path('', include(router.urls)),
]
