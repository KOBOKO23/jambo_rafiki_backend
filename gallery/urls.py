# gallery/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryCategoryViewSet, GalleryPhotoViewSet

router = DefaultRouter()
router.register(r'categories', GalleryCategoryViewSet, basename='gallery-category')
router.register(r'photos', GalleryPhotoViewSet, basename='gallery-photo')

urlpatterns = [
    path('', include(router.urls)),
]

# Add to main urls.py:
