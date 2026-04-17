"""Public CMS content URLs."""

from django.urls import path

from core.image_placement_views import PublicImagePlacementView


urlpatterns = [
    path('image-placements/', PublicImagePlacementView.as_view(), name='content-image-placements'),
]
