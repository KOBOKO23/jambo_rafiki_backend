"""Admin gallery URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from gallery.admin_views import GalleryCategoryAdminViewSet, GalleryPhotoAdminViewSet


router = DefaultRouter()
router.register(r'categories', GalleryCategoryAdminViewSet, basename='admin-gallery-category')
router.register(r'photos', GalleryPhotoAdminViewSet, basename='admin-gallery-photo')

urlpatterns = [
    path('', include(router.urls)),
]