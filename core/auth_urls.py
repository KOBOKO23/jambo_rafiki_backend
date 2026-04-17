"""CMS session auth URL routes."""

from django.urls import path

from core.auth_views import AdminAuthLoginView, AdminAuthLogoutView, CurrentAdminUserView, CsrfTokenView


urlpatterns = [
    path('csrf/', CsrfTokenView.as_view(), name='admin-auth-csrf'),
    path('login/', AdminAuthLoginView.as_view(), name='admin-auth-login'),
    path('logout/', AdminAuthLogoutView.as_view(), name='admin-auth-logout'),
    path('me/', CurrentAdminUserView.as_view(), name='admin-auth-me'),
]
