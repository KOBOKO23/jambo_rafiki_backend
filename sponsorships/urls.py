from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChildViewSet, SponsorViewSet, SponsorshipViewSet, register_interest

router = DefaultRouter()
router.register(r'children', ChildViewSet, basename='child')
router.register(r'sponsors', SponsorViewSet, basename='sponsor')
router.register(r'sponsorships', SponsorshipViewSet, basename='sponsorship')

urlpatterns = [
    path('', include(router.urls)),
    path('interest/', register_interest, name='register-interest'),
]
