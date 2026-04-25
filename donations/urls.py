"""
Donation URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationViewSet, mpesa_callback, stripe_webhook, bank_transfer_request

router = DefaultRouter()
router.register(r'', DonationViewSet, basename='donation')

urlpatterns = [
    # Standalone views MUST come before router.urls to avoid being shadowed
    path('mpesa-callback/', mpesa_callback, name='mpesa-callback'),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
    path('bank-transfer-request/', bank_transfer_request, name='bank-transfer-request'),
    # Router URLs last
    path('', include(router.urls)),
]