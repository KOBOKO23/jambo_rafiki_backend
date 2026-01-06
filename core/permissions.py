"""
Custom permissions for API endpoints
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to everyone, write access to admin only
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access to object owner or admin
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user and request.user.is_staff:
            return True
        
        # Check if object has owner attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsAuthenticatedOrCreateOnly(permissions.BasePermission):
    """
    Allow unauthenticated users to create, but require authentication for other actions
    """
    
    def has_permission(self, request, view):
        # Allow POST (create) for everyone
        if request.method == 'POST':
            return True
        
        # Require authentication for other methods
        return request.user and request.user.is_authenticated


class ReadOnly(permissions.BasePermission):
    """
    Allow read-only access
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
