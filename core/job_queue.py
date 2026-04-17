import logging
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from core.models import BackgroundJob
from core.email_service import EmailService


logger = logging.getLogger(__name__)

JOB_SEND_EMAIL = 'send_email'
JOB_INITIATE_MPESA = 'initiate_mpesa'


def enqueue_job(job_type: str, payload: dict, *, max_attempts: int = 3) -> BackgroundJob:
    return BackgroundJob.objects.create(
        job_type=job_type,
        payload=payload,
        max_attempts=max_attempts,
    )


def enqueue_email(subject: str, message: str, recipient_list: list[str], from_email: str | None = None) -> BackgroundJob:
    payload = {
        'subject': subject,
        'message': message,
        'recipient_list': recipient_list,
        'from_email': from_email,
    }
    return enqueue_job(JOB_SEND_EMAIL, payload)


def enqueue_mpesa_initiation(*, donation_id: int, donor_phone: str, amount, purpose: str) -> BackgroundJob:
    payload = {
        'donation_id': donation_id,
        'donor_phone': donor_phone,
        'amount': str(amount),
        'purpose': purpose,
    }
    return enqueue_job(JOB_INITIATE_MPESA, payload)


def _execute_job(job: BackgroundJob) -> None:
    if job.job_type == JOB_SEND_EMAIL:
        payload = job.payload
        sent = EmailService.send_simple_email(
            subject=payload.get('subject', ''),
            message=payload.get('message', ''),
            recipient_list=payload.get('recipient_list', []),
            from_email=payload.get('from_email'),
            fail_silently=False,
        )
        if sent <= 0:
            raise RuntimeError('Email send returned 0 successful sends')
        return

    if job.job_type == JOB_INITIATE_MPESA:
        # Local import avoids import cycles between core and donations apps.
        from donations.services import DonationService

        DonationService.process_mpesa_initiation_job(job.payload)
        return

    raise ValueError(f'Unsupported job type: {job.job_type}')


def process_pending_jobs(limit: int = 50) -> dict:
    processed = 0
    completed = 0
    failed = 0

    now = timezone.now()
    jobs = list(
        BackgroundJob.objects.filter(
            status=BackgroundJob.STATUS_PENDING,
            available_at__lte=now,
        )[:limit]
    )

    for job in jobs:
        processed += 1
        try:
            with transaction.atomic():
                locked = BackgroundJob.objects.select_for_update().get(pk=job.pk)
                if locked.status != BackgroundJob.STATUS_PENDING:
                    continue
                locked.status = BackgroundJob.STATUS_PROCESSING
                locked.attempts += 1
                locked.save(update_fields=['status', 'attempts', 'updated_at'])

            _execute_job(job)

            BackgroundJob.objects.filter(pk=job.pk).update(
                status=BackgroundJob.STATUS_COMPLETED,
                last_error='',
                updated_at=timezone.now(),
            )
            completed += 1
        except Exception as exc:
            logger.exception('Background job failed job_id=%s type=%s', job.id, job.job_type)
            failed += 1
            next_status = BackgroundJob.STATUS_PENDING
            available_at = timezone.now() + timedelta(minutes=min(job.attempts, 5))
            if job.attempts >= job.max_attempts:
                next_status = BackgroundJob.STATUS_FAILED
                available_at = timezone.now()

            BackgroundJob.objects.filter(pk=job.pk).update(
                status=next_status,
                available_at=available_at,
                last_error=str(exc),
                updated_at=timezone.now(),
            )

    return {
        'processed': processed,
        'completed': completed,
        'failed': failed,
    }
