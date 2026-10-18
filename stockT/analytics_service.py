"""Analytics aggregation service used by setup_analytics.py and the dashboard."""
from collections import Counter
from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone

from .models import (
    DailyStats,
    DeviceTracker,
    NotificationLog,
    PageView,
    SessionTracker,
    UsageMilestone,
    User,
)


class AnalyticsService:
    """Generates daily statistics and usage milestone notifications."""

    MILESTONE_THRESHOLDS = [10, 25, 50, 100, 250, 500, 1000]

    @classmethod
    def generate_daily_stats(cls, date=None):
        """Aggregate analytics for the given date (defaults to today)."""
        date = date or timezone.now().date()
        day_start = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.min.time())
        ) if timezone.is_aware(timezone.now()) else timezone.datetime.combine(date, timezone.datetime.min.time())
        day_end = day_start + timedelta(days=1)

        sessions = SessionTracker.objects.filter(started_at__gte=day_start, started_at__lt=day_end)
        page_views = PageView.objects.filter(viewed_at__gte=day_start, viewed_at__lt=day_end)
        devices = DeviceTracker.objects.filter(last_seen__gte=day_start, last_seen__lt=day_end)

        top_page = (
            page_views.values('page_url')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )

        stats, _ = DailyStats.objects.update_or_create(
            date=date,
            defaults={
                'unique_devices': devices.count(),
                'total_sessions': sessions.count(),
                'active_users': sessions.filter(user__isnull=False).values('user').distinct().count(),
                'new_users': User.objects.filter(date_joined__gte=day_start, date_joined__lt=day_end).count(),
                'new_devices': DeviceTracker.objects.filter(first_seen__gte=day_start, first_seen__lt=day_end).count(),
                'total_page_views': page_views.count(),
                'total_actions': sessions.aggregate(total=Sum('actions_performed'))['total'] or 0,
                'avg_session_duration': int(
                    sessions.filter(duration__isnull=False).aggregate(avg=Avg('duration'))['avg'] or 0
                ),
                'most_visited_page': (top_page or {}).get('page_url'),
                'most_visited_page_count': (top_page or {}).get('count', 0),
            },
        )
        return stats

    @classmethod
    def check_and_notify_milestones(cls):
        """Create notifications for newly achieved usage milestones."""
        notifications = []
        totals = {
            'total_users': User.objects.count(),
            'total_sessions': SessionTracker.objects.count(),
            'total_page_views': PageView.objects.count(),
            'total_devices': DeviceTracker.objects.count(),
        }
        for milestone_type, value in totals.items():
            for threshold in cls.MILESTONE_THRESHOLDS:
                if value < threshold:
                    continue
                if UsageMilestone.objects.filter(milestone_type=milestone_type, threshold=threshold).exists():
                    continue
                message = f'{milestone_type.replace("_", " ").title()} reached {threshold}!'
                milestone = UsageMilestone.objects.create(
                    milestone_type=milestone_type,
                    threshold=threshold,
                    message=message,
                    notified=True,
                )
                notification = NotificationLog.objects.create(
                    notification_type='milestone',
                    title='Usage milestone reached 🎉',
                    message=message,
                )
                notification.sent_to.set(User.objects.filter(is_active=True))
                notifications.append(notification)
                milestone.save(update_fields=['notified'])
        return notifications

    @classmethod
    def get_live_stats(cls):
        """Return a snapshot of live statistics for the analytics dashboard."""
        now = timezone.now()
        today = now.date()
        return {
            'online_sessions': SessionTracker.objects.filter(
                last_activity__gte=now - timedelta(minutes=5)
            ).count(),
            'today_sessions': SessionTracker.objects.filter(started_at__date=today).count(),
            'today_page_views': PageView.objects.filter(viewed_at__date=today).count(),
            'total_users': User.objects.count(),
            'total_devices': DeviceTracker.objects.count(),
            'total_sessions': SessionTracker.objects.count(),
            'total_page_views': PageView.objects.count(),
        }

    @classmethod
    def get_chart_data(cls, days=14):
        """Return daily stats for the last N days for charting."""
        start = timezone.now().date() - timedelta(days=days - 1)
        stats = DailyStats.objects.filter(date__gte=start).order_by('date')
        return [
            {
                'date': s.date.isoformat(),
                'unique_devices': s.unique_devices,
                'total_sessions': s.total_sessions,
                'total_page_views': s.total_page_views,
                'active_users': s.active_users,
            }
            for s in stats
        ]
