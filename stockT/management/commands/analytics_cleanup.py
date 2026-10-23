"""Purge analytics data beyond the configured retention windows.

Respects ANALYTICS_RETENTION_DAYS (default 180) and
ANALYTICS_IP_RETENTION_DAYS (default 30) from settings. Run nightly, e.g.:

    30 1 * * * cd /app && python manage.py analytics_cleanup
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from stockT.analytics_service import AnalyticsService


class Command(BaseCommand):
    help = (
        'Delete page views, sessions and devices older than the retention '
        'window, close stale sessions, and redact stored client IPs that are '
        'older than the IP retention window.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-days', type=int,
            help=f'Override ANALYTICS_RETENTION_DAYS (default {settings.ANALYTICS_RETENTION_DAYS}).',
        )
        parser.add_argument(
            '--ip-retention-days', type=int,
            help=f'Override ANALYTICS_IP_RETENTION_DAYS (default {settings.ANALYTICS_IP_RETENTION_DAYS}).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Only report what would be removed (does not write).',
        )

    def handle(self, *args, **options):
        retention_days = (
            options['retention_days']
            if options.get('retention_days') is not None
            else settings.ANALYTICS_RETENTION_DAYS
        )
        ip_days = (
            options['ip_retention_days']
            if options.get('ip_retention_days') is not None
            else settings.ANALYTICS_IP_RETENTION_DAYS
        )
        dry_run = options.get('dry_run', False)

        if retention_days < 1:
            raise CommandError('--retention-days must be at least 1.')
        if ip_days < 0:
            raise CommandError('--ip-retention-days cannot be negative.')

        if dry_run:
            from stockT.models import DeviceTracker, PageView, SessionTracker
            now = timezone.now()
            cutoff = now - timedelta(days=retention_days)
            ip_cutoff = now - timedelta(days=ip_days)
            self.stdout.write('Would remove:')
            self.stdout.write(f'  {PageView.objects.filter(viewed_at__lt=cutoff).count()} page view(s)')
            self.stdout.write(f'  {SessionTracker.objects.filter(started_at__lt=cutoff).count()} session(s)')
            self.stdout.write(f'  {DeviceTracker.objects.filter(last_seen__lt=cutoff).count()} device(s)')
            self.stdout.write(
                f'  {DeviceTracker.objects.filter(last_seen__lt=ip_cutoff).exclude(ip_address__isnull=True).count()} stored IP(s)'
            )
            return

        result = AnalyticsService.cleanup_old_data(
            retention_days=retention_days,
            ip_retention_days=ip_days,
        )
        self.stdout.write(self.style.SUCCESS(
            'Analytics cleanup complete: '
            f"{result['page_views_deleted']} page view(s) deleted, "
            f"{result['sessions_deleted']} session(s) deleted, "
            f"{result['devices_deleted']} device(s) deleted, "
            f"{result['ip_addresses_redacted']} IP(s) redacted, "
            f"{result['sessions_closed']} stale session(s) closed."
        ))
