"""
URL configuration for jambo_rafiki project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

# Create a router for API endpoints
router = routers.DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include([
        path('contacts/', include('contacts.urls')),
        path('donations/', include('donations.urls')),
        path('volunteers/', include('volunteers.urls')),
        path('newsletter/', include('newsletter.urls')),
        path('sponsorships/', include('sponsorships.urls')),
        path('gallery/', include('gallery.urls')),
    ])),
    
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