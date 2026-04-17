"""Audit logging helpers for sensitive state transitions."""

from __future__ import annotations

import logging

from core.models import AuditEvent


logger = logging.getLogger(__name__)


def log_audit_event(
    event_type: str,
    *,
    actor=None,
    target=None,
    target_model: str = '',
    target_id: str = '',
    source: str = '',
    metadata: dict | None = None,
) -> None:
    """Persist a non-blocking audit event for operational traceability."""
    try:
        resolved_target_model = target_model
        resolved_target_id = target_id
        if target is not None:
            resolved_target_model = target._meta.label_lower
            resolved_target_id = str(target.pk)

        AuditEvent.objects.create(
            event_type=event_type,
            actor=actor if getattr(actor, 'is_authenticated', False) else None,
            source=source,
            target_model=resolved_target_model,
            target_id=resolved_target_id,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception('Failed to write audit event type=%s', event_type)
