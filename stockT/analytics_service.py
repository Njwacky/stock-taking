"""Analytics aggregation service used by setup_analytics.py and the dashboard."""
from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
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
        """Aggregate app-wide analytics for the given date (defaults to today)."""
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
        """Create notifications for newly achieved usage milestones.

        Milestones are app-wide totals, so they are sent to the people who
        administer the app (global managers/admins) — not broadcast to every
        member of every workspace.
        """
        notifications = []
        totals = {
            'total_users': User.objects.count(),
            'total_sessions': SessionTracker.objects.count(),
            'total_page_views': PageView.objects.count(),
            'total_devices': DeviceTracker.objects.count(),
        }
        audience = User.objects.filter(
            Q(is_superuser=True) | Q(role__in=[User.ROLE_ADMIN, User.ROLE_MANAGER])
        )
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
                    title='Usage milestone reached',
                    message=message,
                )
                notification.sent_to.set(audience)
                notifications.append(notification)
                milestone.save(update_fields=['notified'])
        return notifications

    @classmethod
    def get_live_stats(cls, workspace=None):
        """Return a snapshot of live statistics, scoped to a workspace.

        ``workspace=None`` keeps the historical app-wide view (used by the
        global daily report); dashboards always pass the active workspace.
        """
        now = timezone.now()
        today = now.date()
        sessions = SessionTracker.objects.all()
        page_views = PageView.objects.all()
        if workspace is not None:
            sessions = sessions.filter(workspace=workspace)
            page_views = page_views.filter(session__workspace=workspace)
        return {
            'online_sessions': sessions.filter(
                last_activity__gte=now - timedelta(minutes=5),
                ended_at__isnull=True,
            ).count(),
            'today_sessions': sessions.filter(started_at__date=today).count(),
            'today_page_views': page_views.filter(viewed_at__date=today).count(),
            'total_users': User.objects.count(),
            'total_devices': cls.scoped_devices(workspace).count(),
            'total_sessions': sessions.count(),
            'total_page_views': page_views.count(),
        }

    @classmethod
    def scoped_devices(cls, workspace=None):
        """Devices belonging to the workspace's members (global when None)."""
        devices = DeviceTracker.objects.all()
        if workspace is not None:
            devices = devices.filter(user__workspace_memberships__workspace=workspace)
        return devices

    @classmethod
    def get_chart_data(cls, days=14, workspace=None):
        """Return daily stats for the last N days for charting."""
        start = timezone.now().date() - timedelta(days=days - 1)
        sessions = SessionTracker.objects.all()
        page_views = PageView.objects.all()
        if workspace is not None:
            sessions = sessions.filter(workspace=workspace)
            page_views = page_views.filter(session__workspace=workspace)
        session_map = cls._sessions_by_day(sessions)
        view_map = cls._counts_by_day(page_views, 'viewed_at')
        stats = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            sess = session_map.get(day) or {}
            stats.append({
                'date': day.isoformat(),
                'total_sessions': sess.get('total_sessions', 0),
                'total_page_views': view_map.get(day, 0),
                'active_users': sess.get('active_users', 0),
                'unique_devices': sess.get('unique_devices', 0),
            })
        return stats

    @classmethod
    def _sessions_by_day(cls, sessions):
        """Session/user/device counts keyed by start date."""
        from django.db.models.functions import TruncDate
        return {
            row['day']: row
            for row in sessions.annotate(day=TruncDate('started_at')).values('day').annotate(
                total_sessions=Count('id'),
                active_users=Count('user', distinct=True),
                unique_devices=Count('device', distinct=True),
            )
        }

    @classmethod
    def _counts_by_day(cls, queryset, date_field):
        """Row counts keyed by the given date field."""
        from django.db.models.functions import TruncDate
        return {
            row['day']: row['total']
            for row in queryset.annotate(day=TruncDate(date_field)).values('day').annotate(
                total=Count('id'),
            )
        }

    @classmethod
    def close_stale_sessions(cls, older_than_hours=24):
        """Finalise sessions that ended long ago but were never closed.

        Backstops the middleware's idle-close logic (and repairs rows created
        before session closing existed). Returns the number of rows closed.
        """
        cutoff = timezone.now() - timedelta(hours=older_than_hours)
        stale = SessionTracker.objects.filter(ended_at__isnull=True, last_activity__lt=cutoff)
        closed = 0
        for session in stale.iterator():
            ended = session.last_activity or timezone.now()
            SessionTracker.objects.filter(pk=session.pk).update(
                ended_at=ended,
                duration=max(int((ended - session.started_at).total_seconds()), 0),
            )
            closed += 1
        return closed

    @classmethod
    def cleanup_old_data(cls, retention_days=None, ip_retention_days=None):
        """Purge analytics data beyond the configured retention windows.

        Returns a dict with per-table counts so management commands can
        report what they removed.
        """
        retention_days = retention_days if retention_days is not None else settings.ANALYTICS_RETENTION_DAYS
        ip_retention_days = ip_retention_days if ip_retention_days is not None else settings.ANALYTICS_IP_RETENTION_DAYS
        now = timezone.now()
        pageview_cutoff = now - timedelta(days=retention_days)
        session_cutoff = now - timedelta(days=retention_days)
        device_cutoff = now - timedelta(days=retention_days)
        ip_cutoff = now - timedelta(days=ip_retention_days)

        # Close stragglers first so nothing "active" is judged by stale data.
        closed = cls.close_stale_sessions()

        deleted_page_views, _ = PageView.objects.filter(viewed_at__lt=pageview_cutoff).delete()
        deleted_sessions, _ = SessionTracker.objects.filter(
            started_at__lt=session_cutoff,
        ).delete()
        deleted_devices, _ = DeviceTracker.objects.filter(last_seen__lt=device_cutoff).delete()

        # Privacy: keep behaviour data, redact personal data sooner.
        redacted_ips = DeviceTracker.objects.filter(
            last_seen__lt=ip_cutoff,
        ).exclude(ip_address__isnull=True).update(ip_address=None)

        return {
            'sessions_closed': closed,
            'page_views_deleted': deleted_page_views,
            'sessions_deleted': deleted_sessions,
            'devices_deleted': deleted_devices,
            'ip_addresses_redacted': redacted_ips,
        }
