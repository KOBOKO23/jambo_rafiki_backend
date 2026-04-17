from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.utils import timezone


def check_database_ready() -> tuple[bool, str]:
    """Return readiness state for the primary database connection."""
    try:
        connections['default'].ensure_connection()
        return True, 'ok'
    except Exception as exc:
        return False, str(exc)


def health_view(request):
    """Liveness endpoint for load balancers and probes."""
    return JsonResponse(
        {
            'status': 'ok',
            'service': 'jambo-rafiki-backend',
            'timestamp': timezone.now().isoformat(),
        },
        status=200,
    )


def ready_view(request):
    """Readiness endpoint that verifies dependencies required to serve traffic."""
    db_ok, db_message = check_database_ready()
    checks = {
        'database': 'ok' if db_ok else 'error',
    }

    response = {
        'status': 'ready' if db_ok else 'not_ready',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }

    if not db_ok:
        response['errors'] = {'database': db_message}

    return JsonResponse(response, status=200 if db_ok else 503)


def organization_config_view(request):
    """Public organization details consumed by frontend contact and donation flows."""
    return JsonResponse(
        {
            'website': {
                'domain': settings.ORGANIZATION_DOMAIN,
                'url': settings.ORGANIZATION_WEBSITE_URL,
            },
            'contact': {
                'email': settings.ORGANIZATION_PUBLIC_EMAIL,
                'call_redirect_number': settings.ORGANIZATION_CALL_REDIRECT_NUMBER,
                'call_redirect_url': f"tel:{settings.ORGANIZATION_CALL_REDIRECT_NUMBER}",
            },
            'bank_account': {
                'bank_code': settings.ORGANIZATION_BANK_CODE,
                'branch_code': settings.ORGANIZATION_BANK_BRANCH_CODE,
                'swift_code': settings.ORGANIZATION_BANK_SWIFT_CODE,
                'account_name': settings.ORGANIZATION_BANK_ACCOUNT_NAME,
                'account_number': settings.ORGANIZATION_BANK_ACCOUNT_NUMBER,
            },
            'timestamp': timezone.now().isoformat(),
        },
        status=200,
    )
