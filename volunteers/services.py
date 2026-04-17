"""Volunteer domain services."""

from __future__ import annotations

from django.db import transaction

from core.audit import log_audit_event
from .models import VolunteerApplication


class VolunteerService:
    """Service helpers for volunteer state transitions."""

    @staticmethod
    def update_status(*, application: VolunteerApplication, new_status: str, actor=None) -> VolunteerApplication:
        if new_status not in dict(VolunteerApplication.STATUS_CHOICES):
            raise ValueError('Invalid status')

        old_status = application.status
        with transaction.atomic():
            application.status = new_status
            application.save(update_fields=['status', 'updated_at'])

            log_audit_event(
                'volunteer.status_changed',
                actor=actor,
                target=application,
                source='volunteers.service.update_status',
                metadata={
                    'old_status': old_status,
                    'new_status': new_status,
                },
            )

        return application
