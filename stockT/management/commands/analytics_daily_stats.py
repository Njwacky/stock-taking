"""Generate daily analytics statistics and check usage milestones.

Intended to run from cron (or any scheduler), e.g. nightly:

    0 1 * * * cd /app && python manage.py analytics_daily_stats
"""
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from stockT.analytics_service import AnalyticsService


class Command(BaseCommand):
    help = (
        'Aggregate daily analytics (DailyStats) for a date and check for new '
        'usage milestones. Defaults to today; run it nightly from cron.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            help='ISO date to aggregate (YYYY-MM-DD). Defaults to today.',
        )

    def handle(self, *args, **options):
        date = timezone.now().date()
        if options.get('date'):
            try:
                date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('--date must be in YYYY-MM-DD format.')
            if date > timezone.now().date():
                raise CommandError('--date cannot be in the future.')

        stats = AnalyticsService.generate_daily_stats(date)
        self.stdout.write(self.style.SUCCESS(
            f'Stats for {stats.date}: {stats.total_sessions} sessions, '
            f'{stats.total_page_views} page views, {stats.active_users} active users.'
        ))

        milestones = AnalyticsService.check_and_notify_milestones()
        if milestones:
            for notification in milestones:
                self.stdout.write(self.style.SUCCESS(f'  Milestone: {notification.message}'))
        else:
            self.stdout.write('No new milestones.')

        # Safety net for sessions that were never explicitly closed.
        closed = AnalyticsService.close_stale_sessions()
        if closed:
            self.stdout.write(f'Closed {closed} stale session(s).')
