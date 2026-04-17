"""Admin API URLs for the CMS and operational dashboard."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.auth_views import AdminAuthLoginView, AdminAuthLogoutView, CurrentAdminUserView, CsrfTokenView
from core.admin_views import AdminOverviewView, AuditEventViewSet, BackgroundJobViewSet
from core.image_placement_views import AdminImagePlacementView
from core.cms_views import (
    BannerViewSet,
    ContentRevisionViewSet,
    MediaAssetViewSet,
    NavigationMenuItemViewSet,
    NavigationMenuViewSet,
    PageSectionViewSet,
    PageViewSet,
    RedirectRuleViewSet,
    SiteSettingView,
)


router = DefaultRouter()
router.register(r'audit-events', AuditEventViewSet, basename='admin-audit-event')
router.register(r'background-jobs', BackgroundJobViewSet, basename='admin-background-job')
router.register(r'pages', PageViewSet, basename='admin-page')
router.register(r'page-sections', PageSectionViewSet, basename='admin-page-section')
router.register(r'navigation-menus', NavigationMenuViewSet, basename='admin-navigation-menu')
router.register(r'navigation-items', NavigationMenuItemViewSet, basename='admin-navigation-item')
router.register(r'banners', BannerViewSet, basename='admin-banner')
router.register(r'redirect-rules', RedirectRuleViewSet, basename='admin-redirect-rule')
router.register(r'media-assets', MediaAssetViewSet, basename='admin-media-asset')
router.register(r'content-revisions', ContentRevisionViewSet, basename='admin-content-revision')

urlpatterns = [
    path('auth/csrf/', CsrfTokenView.as_view(), name='admin-auth-csrf'),
    path('auth/login/', AdminAuthLoginView.as_view(), name='admin-auth-login'),
    path('auth/logout/', AdminAuthLogoutView.as_view(), name='admin-auth-logout'),
    path('auth/me/', CurrentAdminUserView.as_view(), name='admin-auth-me'),
    path('overview/', AdminOverviewView.as_view(), name='admin-overview'),
    path('image-placements/', AdminImagePlacementView.as_view(), name='admin-image-placements'),
    path('site-settings/', SiteSettingView.as_view(), name='admin-site-settings'),
    path('', include(router.urls)),
    path('gallery/', include('gallery.admin_urls')),
]