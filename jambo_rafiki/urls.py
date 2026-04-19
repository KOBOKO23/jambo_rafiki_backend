"""
URL configuration for jambo_rafiki project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from core.health_views import health_view, organization_config_view, ready_view
from jambo_rafiki.views import home_view

# Create a router for API endpoints
router = routers.DefaultRouter()

api_patterns = [
    path('organization/', organization_config_view, name='organization-config'),
    path('auth/', include('core.auth_urls')),
    path('admin/', include('core.admin_urls')),
    path('content/', include('core.content_urls')),
    path('contacts/', include('contacts.urls')),
    path('donations/', include('donations.urls')),
    path('volunteers/', include('volunteers.urls')),
    path('newsletter/', include('newsletter.urls')),
    path('sponsorships/', include('sponsorships.urls')),
    path('gallery/', include('gallery.urls')),
    path('testimonials/', include('testimonials.urls')),
]

urlpatterns = [
    # Home page
    path('', home_view, name='home'),

    # Admin
    path('admin/', admin.site.urls),

    # Ops probes
    path('health/', health_view, name='health'),
    path('ready/', ready_view, name='ready'),

    # Versioned API endpoints (preferred)
    path('api/v1/', include(api_patterns)),

    # Backward-compatible unversioned endpoints
    path('api/', include(api_patterns)),

    # API root (browsable API)
    path('api/', include(router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Jambo Rafiki Administration"
admin.site.site_title = "Jambo Rafiki Admin"
admin.site.index_title = "Welcome to Jambo Rafiki Administration"