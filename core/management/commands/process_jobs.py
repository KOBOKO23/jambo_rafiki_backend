from django.core.management.base import BaseCommand
import time

from core.job_queue import process_pending_jobs


class Command(BaseCommand):
    help = 'Process pending durable background jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--loop', action='store_true', help='Run continuously and poll for jobs')
        parser.add_argument('--sleep-seconds', type=int, default=5, help='Polling interval while in --loop mode')

    def handle(self, *args, **options):
        limit = options['limit']
        if not options['loop']:
            result = process_pending_jobs(limit=limit)
            self.stdout.write(
                self.style.SUCCESS(
                    f"processed={result['processed']} completed={result['completed']} failed={result['failed']}"
                )
            )
            return

        sleep_seconds = max(1, options['sleep_seconds'])
        self.stdout.write(self.style.SUCCESS(f'Worker running in loop mode (poll={sleep_seconds}s, limit={limit})'))
        while True:
            result = process_pending_jobs(limit=limit)
            self.stdout.write(
                f"processed={result['processed']} completed={result['completed']} failed={result['failed']}"
            )
            time.sleep(sleep_seconds)
