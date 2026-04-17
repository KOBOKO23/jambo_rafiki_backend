"""Serializers for CMS session authentication endpoints."""

from __future__ import annotations

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class AdminAuthLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    identifier = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = (attrs.get('identifier') or attrs.get('email') or attrs.get('username') or '').strip()
        password = attrs.get('password')

        if not identifier:
            raise serializers.ValidationError({'identifier': ['Username or email is required.']})

        user = None
        if attrs.get('email'):
            user = User.objects.filter(email__iexact=attrs['email'].strip()).first()
        if user is None and attrs.get('username'):
            user = User.objects.filter(username__iexact=attrs['username'].strip()).first()
        if user is None and attrs.get('identifier'):
            user = User.objects.filter(username__iexact=identifier).first() or User.objects.filter(email__iexact=identifier).first()

        if user is not None:
            authenticated = authenticate(username=user.get_username(), password=password)
            if authenticated is None and user.email:
                authenticated = authenticate(username=user.email, password=password)
        else:
            authenticated = authenticate(username=identifier, password=password)
            if authenticated is None:
                matched_user = User.objects.filter(email__iexact=identifier).first()
                if matched_user is not None:
                    authenticated = authenticate(username=matched_user.get_username(), password=password)

        if authenticated is None:
            raise serializers.ValidationError({'non_field_errors': ['Invalid credentials.']})

        if not authenticated.is_active:
            raise serializers.ValidationError({'non_field_errors': ['This account is disabled.']})

        attrs['user'] = authenticated
        return attrs


class AdminUserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'display_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'role',
            'permissions',
        ]
        read_only_fields = fields

    def get_display_name(self, obj):
        full_name = obj.get_full_name().strip()
        return full_name or obj.get_username()

    def get_role(self, obj):
        if obj.is_superuser:
            return 'super_admin'
        if obj.is_staff:
            return 'admin'
        return 'user'

    def get_permissions(self, obj):
        if obj.is_superuser:
            return {
                'can_access_admin': True,
                'can_manage_pages': True,
                'can_manage_navigation': True,
                'can_manage_media': True,
                'can_manage_donations': True,
                'can_manage_contacts': True,
                'can_manage_volunteers': True,
                'can_manage_newsletter': True,
                'can_manage_sponsorships': True,
                'can_manage_testimonials': True,
                'can_manage_gallery': True,
                'can_manage_settings': True,
            }
        if obj.is_staff:
            return {
                'can_access_admin': True,
                'can_manage_pages': True,
                'can_manage_navigation': True,
                'can_manage_media': True,
                'can_manage_donations': True,
                'can_manage_contacts': True,
                'can_manage_volunteers': True,
                'can_manage_newsletter': True,
                'can_manage_sponsorships': True,
                'can_manage_testimonials': True,
                'can_manage_gallery': True,
                'can_manage_settings': True,
            }
        return {
            'can_access_admin': False,
        }
