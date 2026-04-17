"""Serializers for admin-only core API views."""

from __future__ import annotations

from rest_framework import serializers

from core.models import AuditEvent, BackgroundJob


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'event_type',
            'actor',
            'actor_name',
            'source',
            'target_model',
            'target_id',
            'metadata',
            'created_at',
        ]

    def get_actor_name(self, obj):
        if obj.actor is None:
            return None
        full_name = obj.actor.get_full_name().strip()
        return full_name or obj.actor.get_username()


class BackgroundJobSerializer(serializers.ModelSerializer):
    is_retryable = serializers.SerializerMethodField()

    class Meta:
        model = BackgroundJob
        fields = [
            'id',
            'job_type',
            'payload',
            'status',
            'attempts',
            'max_attempts',
            'available_at',
            'last_error',
            'created_at',
            'updated_at',
            'is_retryable',
        ]

    def get_is_retryable(self, obj):
        return obj.status == BackgroundJob.STATUS_FAILED