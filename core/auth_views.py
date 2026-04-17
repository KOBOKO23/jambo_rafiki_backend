"""Session authentication endpoints for the CMS frontend."""

from __future__ import annotations

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import log_audit_event
from core.auth_serializers import AdminAuthLoginSerializer, AdminUserSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AdminAuthLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminAuthLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        if not user.is_staff:
            return Response(
                {'detail': 'This account does not have CMS access.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        log_audit_event(
            'cms.auth.login',
            actor=user,
            target=user,
            source='core.auth.login',
            metadata={'username': user.get_username(), 'email': user.email},
        )

        response = Response({
            'user': AdminUserSerializer(user, context={'request': request}).data,
            'message': 'Signed in successfully.',
            'csrf_token': get_token(request),
        }, status=status.HTTP_200_OK)
        return response


class AdminAuthLogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        actor = request.user if request.user.is_authenticated else None
        if actor is not None:
            log_audit_event(
                'cms.auth.logout',
                actor=actor,
                target=actor,
                source='core.auth.logout',
                metadata={'username': actor.get_username(), 'email': actor.email},
            )

        logout(request)
        response = Response({'message': 'Signed out successfully.'}, status=status.HTTP_200_OK)
        return response


class CurrentAdminUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'detail': 'This account does not have CMS access.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrf_token': get_token(request)}, status=status.HTTP_200_OK)
