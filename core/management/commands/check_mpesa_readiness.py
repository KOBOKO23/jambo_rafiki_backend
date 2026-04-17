from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check whether M-Pesa configuration is ready for real-phone testing"

    def handle(self, *args, **options):
        keys = [
            'MPESA_ENVIRONMENT',
            'MPESA_CONSUMER_KEY',
            'MPESA_CONSUMER_SECRET',
            'MPESA_SHORTCODE',
            'MPESA_PASSKEY',
            'MPESA_CALLBACK_URL',
            'MPESA_CALLBACK_TOKEN',
        ]

        missing = []
        self.stdout.write('M-Pesa readiness check')
        self.stdout.write('-' * 40)

        for key in keys:
            value = getattr(settings, key, '')
            state = 'set' if bool(value) else 'missing'
            self.stdout.write(f'{key}: {state}')
            if not value and key not in ('MPESA_CALLBACK_TOKEN',):
                missing.append(key)

        callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        if callback_url:
            parsed = urlparse(callback_url)
            if parsed.scheme != 'https':
                self.stdout.write(self.style.WARNING('Callback URL is not https. Production Daraja callbacks should use https.'))
            if not parsed.netloc:
                self.stdout.write(self.style.ERROR('Callback URL host is missing.'))
            if '/donations/mpesa-callback/' not in parsed.path:
                self.stdout.write(self.style.WARNING('Callback URL path should target /donations/mpesa-callback/.'))

        env = getattr(settings, 'MPESA_ENVIRONMENT', '').strip().lower()
        if env == 'sandbox':
            self.stdout.write(self.style.WARNING('Environment is sandbox; real subscriber phones usually will not receive a production STK push.'))
        elif env == 'production':
            self.stdout.write(self.style.SUCCESS('Environment is production.'))

        self.stdout.write('-' * 40)
        if missing:
            self.stdout.write(self.style.ERROR('NOT READY: missing required settings: ' + ', '.join(missing)))
        else:
            self.stdout.write(self.style.SUCCESS('READY: core configuration is present. Ensure your worker is running and callback URL is publicly reachable.'))
