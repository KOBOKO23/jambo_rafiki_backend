"""
Donation URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationViewSet, mpesa_callback, stripe_webhook

router = DefaultRouter()
router.register(r'', DonationViewSet, basename='donation')

urlpatterns = [
    path('', include(router.urls)),
    path('mpesa-callback/', mpesa_callback, name='mpesa-callback'),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
]