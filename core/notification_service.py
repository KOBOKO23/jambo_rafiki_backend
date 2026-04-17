"""Shared notification service for queued outbound emails."""

from __future__ import annotations

from typing import Iterable

from core.job_queue import enqueue_email
from core.notification_templates import render_email_template


def queue_template_email(
    template_name: str,
    *,
    context: dict,
    recipient_list: Iterable[str],
    from_email: str | None = None,
):
    """Render a shared template and enqueue it for async delivery."""
    subject, message = render_email_template(template_name, context)
    return enqueue_email(
        subject=subject,
        message=message,
        recipient_list=list(recipient_list),
        from_email=from_email,
    )
