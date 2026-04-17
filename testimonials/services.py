"""Testimonial domain services."""

from __future__ import annotations

from django.db import transaction

from core.audit import log_audit_event
from .models import Testimonial


class TestimonialService:
    """Service helpers for testimonial moderation transitions."""

    @staticmethod
    def approve(*, testimonial: Testimonial, actor=None) -> Testimonial:
        old_status = testimonial.status
        with transaction.atomic():
            testimonial.approve()
            log_audit_event(
                'testimonial.approved',
                actor=actor,
                target=testimonial,
                source='testimonials.service.approve',
                metadata={
                    'old_status': old_status,
                    'new_status': testimonial.status,
                },
            )
        return testimonial

    @staticmethod
    def reject(*, testimonial: Testimonial, notes: str = '', actor=None) -> Testimonial:
        old_status = testimonial.status
        with transaction.atomic():
            if notes:
                testimonial.notes = notes
            testimonial.reject()
            log_audit_event(
                'testimonial.rejected',
                actor=actor,
                target=testimonial,
                source='testimonials.service.reject',
                metadata={
                    'old_status': old_status,
                    'new_status': testimonial.status,
                    'notes': testimonial.notes,
                },
            )
        return testimonial
