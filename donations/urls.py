"""
Donation URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationViewSet, mpesa_callback
from .views import DonationViewSet, mpesa_callback, mpesa_donation


router = DefaultRouter()
router.register(r'', DonationViewSet, basename='donation')

urlpatterns = [
    path('', include(router.urls)),
    path('mpesa/', mpesa_donation, name='mpesa-donation'),
    path('mpesa-callback/', mpesa_callback, name='mpesa-callback'),
]
