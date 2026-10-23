"""Analytics tracking: middleware, tenant scoping, endpoints and retention.

Covers the defects fixed in the tracking overhaul: unvalidated chart params
used to 500, AJAX polling inflated page views, sessions never recorded a
duration, and dashboards leaked activity across workspaces.
"""
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from stockT.analytics_service import AnalyticsService
from stockT.models import (
    DailyStats,
    DeviceTracker,
    NotificationLog,
    PageView,
    SessionTracker,
    UsageMilestone,
    WorkspaceMember,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def make_device(user=None, device_id=None, **extra):
    extra.setdefault('device_type', 'Desktop')
    extra.setdefault('ip_address', '9.9.9.9')
    extra.setdefault('last_seen', timezone.now())
    return DeviceTracker.objects.create(
        device_id=device_id or uuid.uuid4().hex,
        user=user,
        **extra,
    )


def make_session(user=None, workspace=None, device=None, **extra):
    extra.setdefault('last_activity', timezone.now())
    return SessionTracker.objects.create(
        session_id=extra.pop('session_id', uuid.uuid4().hex),
        device=device or make_device(user=user),
        user=user,
        workspace=workspace,
        **extra,
    )


@pytest.fixture
def workspace_admin(db, workspace):
    """A workspace admin who holds NO global manager/admin role."""
    user = User.objects.create_user(
        'wsadmin', 'wsadmin@example.com', 'Pass!1234',
        role='user', clock_number='9901',
    )
    WorkspaceMember.objects.create(
        workspace=workspace, user=user, role=WorkspaceMember.ROLE_ADMIN,
    )
    return user


@pytest.fixture
def as_ws_admin(workspace_admin):
    client = Client()
    client.force_login(workspace_admin)
    return client


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class TestMiddleware:
    def test_anonymous_visit_is_tracked(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert DeviceTracker.objects.count() == 1
        assert SessionTracker.objects.count() == 1
        assert PageView.objects.count() == 1

    def test_device_cookie_is_httponly(self, client):
        response = client.get('/')
        assert 'device_id' in response.cookies
        assert response.cookies['device_id'].get('httponly')

    def test_member_session_scoped_to_their_workspace(self, as_member, workspace, member):
        as_member.get('/')
        session = SessionTracker.objects.get()
        assert session.workspace_id == workspace.id
        assert session.user_id == member.id

    def test_ajax_polls_are_not_recorded_as_page_views(self, as_member):
        """The live-stats poll used to add a fake page view every minute."""
        as_member.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert SessionTracker.objects.count() == 1
        assert PageView.objects.count() == 0

    def test_post_counts_as_action_not_page_view(self, as_member):
        as_member.post('/')
        session = SessionTracker.objects.get()
        assert session.actions_performed >= 1
        assert PageView.objects.count() == 0

    def test_static_and_service_worker_paths_skipped(self, client):
        client.get('/sw.js')
        client.get('/manifest.json')
        assert DeviceTracker.objects.count() == 0
        assert SessionTracker.objects.count() == 0

    def test_idle_session_is_closed_with_a_real_duration(self, as_member):
        as_member.get('/')
        session = SessionTracker.objects.get()
        original_id = session.session_id
        # Age the session past the idle window (started 40 min ago, last
        # activity 31 min ago).
        now = timezone.now()
        SessionTracker.objects.filter(pk=session.pk).update(
            started_at=now - timedelta(minutes=40),
            last_activity=now - timedelta(minutes=31),
        )

        as_member.get('/')

        old = SessionTracker.objects.get(pk=session.pk)
        fresh = SessionTracker.objects.filter(session_id=original_id).exclude(pk=session.pk)
        assert old.ended_at is not None
        assert old.session_id != original_id  # freed the key for the new visit
        assert 500 <= old.duration <= 620  # 9 minutes between start and close
        assert fresh.exists()
        assert fresh.get().ended_at is None

    def test_live_session_duration_keeps_counting(self, as_member):
        as_member.get('/')
        session = SessionTracker.objects.get()
        SessionTracker.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(minutes=5),
        )
        as_member.get('/')
        session.refresh_from_db()
        assert session.duration is not None
        assert session.duration >= 300

    def test_xff_header_ignored_without_proxy_trust(self, client, settings):
        settings.TRUST_X_FORWARDED_FOR = False
        client.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4')
        assert DeviceTracker.objects.get().ip_address != '1.2.3.4'

    def test_xff_header_trusted_when_behind_proxy(self, client, settings):
        settings.TRUST_X_FORWARDED_FOR = True
        client.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4, 10.0.0.1')
        assert DeviceTracker.objects.get().ip_address == '1.2.3.4'


# ---------------------------------------------------------------------------
# Endpoint permissions and parameter hardening
# ---------------------------------------------------------------------------

class TestEndpoints:
    def test_member_is_redirected_from_analytics(self, as_member):
        assert as_member.get('/analytics/').status_code == 302

    def test_member_forbidden_from_live_stats(self, as_member):
        assert as_member.get('/analytics/live-stats/').status_code == 403

    def test_workspace_admin_without_global_role_can_view(self, as_ws_admin):
        """Access follows workspace membership, not only the global role."""
        response = as_ws_admin.get('/analytics/')
        assert response.status_code == 200

    def test_chart_data_survives_garbage_days_param(self, as_owner):
        """Regression: days=abc / days=999999 used to raise a 500."""
        for value in ('abc', '', '999999', '-5'):
            response = as_owner.get('/analytics/chart-data/', {'days': value})
            assert response.status_code == 200
            payload = response.json()
            assert payload['success'] is True
            assert len(payload['data']) == 14  # falls back to the default

    def test_dashboard_survives_garbage_range_param(self, as_owner):
        response = as_owner.get('/analytics/', {'range': 'soon'})
        assert response.status_code == 200
        assert response.context['range_days'] == 14

    def test_chart_data_accepts_valid_windows(self, as_owner):
        payload = as_owner.get('/analytics/chart-data/', {'days': '7'}).json()
        assert len(payload['data']) == 7

    def test_devices_page_member_denied(self, as_member):
        assert as_member.get('/analytics/devices/').status_code == 302

    def test_daily_report_requires_global_manager(self, as_ws_admin):
        response = as_ws_admin.get('/analytics/report/')
        assert response.status_code == 403

    def test_daily_report_allowed_for_global_admin(self, as_owner):
        response = as_owner.get('/analytics/report/')
        assert response.status_code == 200
        assert response.json()['success'] is True


# ---------------------------------------------------------------------------
# Tenant scoping
# ---------------------------------------------------------------------------

class TestWorkspaceScoping:
    def test_live_stats_only_count_this_workspace(self, as_owner, workspace, member, db):
        other = User.objects.create_user(
            'outsider', 'out@example.com', 'Pass!1234', clock_number='9902',
        )
        make_session(user=member, workspace=workspace)
        make_session(user=member, workspace=workspace)
        make_session(user=other, workspace=None)  # another tenant / anonymous

        stats = as_owner.get('/analytics/live-stats/').json()['stats']
        # The owner's own session for this request is created too — three
        # in-workspace sessions, and the outsider's must not be included.
        assert stats['total_sessions'] == 3

    def test_dashboard_totals_exclude_other_tenants(self, as_owner, workspace, member, db):
        make_session(user=member, workspace=workspace)
        make_session(user=None, workspace=None)
        response = as_owner.get('/analytics/')
        assert response.status_code == 200
        # Member + the owner's own request-session; the unscoped row is out.
        assert response.context['total_periods']['sessions'] == 2

    def test_devices_page_scopes_to_members(self, as_owner, workspace, member, db):
        make_device(user=member)
        make_device(user=None)               # anonymous device: out of scope
        stranger = User.objects.create_user(
            'solo', 'solo@example.com', 'Pass!1234', clock_number='9903',
        )
        make_device(user=stranger)           # no membership: out of scope

        response = as_owner.get('/analytics/devices/')
        # Member's device + the owner's own request-device.
        assert response.context['summary']['total'] == 2

    def test_chart_data_scoped(self, as_owner, workspace, member, db):
        make_session(user=member, workspace=workspace)
        make_session(user=None, workspace=None)
        payload = as_owner.get('/analytics/chart-data/').json()
        assert sum(row['total_sessions'] for row in payload['data']) == 2

    def test_export_csv_scoped(self, as_owner, workspace, member, db):
        make_session(user=member, workspace=workspace)
        make_session(user=None, workspace=None)
        response = as_owner.get('/analytics/export.csv')
        assert response.status_code == 200
        body = response.content.decode()
        data_rows = [line for line in body.splitlines()[1:] if line]
        todays = [line for line in data_rows if str(timezone.localdate()) in line]
        # Member + owner (this request); the unscoped row is excluded.
        assert todays and todays[0].split(',')[1] == '2'


# ---------------------------------------------------------------------------
# Aggregation service
# ---------------------------------------------------------------------------

class TestAnalyticsService:
    def test_daily_stats_generated(self, workspace, member):
        session = make_session(user=member, workspace=workspace)
        PageView.objects.create(page_url='/', session=session)

        stats = AnalyticsService.generate_daily_stats()

        stored = DailyStats.objects.get(date=timezone.now().date())
        assert stored == stats
        assert stored.total_sessions == 1
        assert stored.total_page_views == 1
        assert stored.active_users == 1

    def test_live_stats_counts_recent_sessions_only(self, workspace, member):
        make_session(user=member, workspace=workspace)  # last_activity=now
        stale = make_session(user=member, workspace=workspace)
        SessionTracker.objects.filter(pk=stale.pk).update(
            last_activity=timezone.now() - timedelta(minutes=30),
        )
        stats = AnalyticsService.get_live_stats(workspace=workspace)
        assert stats['online_sessions'] == 1

    def test_milestones_reach_managers_not_every_member(self, db, workspace, member, manager):
        for index in range(9):
            User.objects.create_user(
                f'extra{index}', f'extra{index}@example.com', 'Pass!1234',
                role='user', clock_number=f'91{index:02d}',
            )

        created = AnalyticsService.check_and_notify_milestones()

        assert created, 'reaching the10-user threshold must notify'
        notification = NotificationLog.objects.filter(notification_type='milestone').first()
        recipients = set(notification.sent_to.values_list('role', flat=True))
        assert recipients  # only privileged roles
        assert set(recipients) <= {'admin', 'manager'}
        assert not notification.sent_to.filter(id=member.id).exists()
        # Idempotent: a second run adds nothing.
        assert AnalyticsService.check_and_notify_milestones() == []
        assert UsageMilestone.objects.filter(threshold=10).exists()

    def test_close_stale_sessions_finalises_duration(self):
        session = make_session()
        now = timezone.now()
        SessionTracker.objects.filter(pk=session.pk).update(
            started_at=now - timedelta(hours=27),
            last_activity=now - timedelta(hours=25),  # beyond the 24h cutoff
        )
        closed = AnalyticsService.close_stale_sessions()
        session.refresh_from_db()
        assert closed == 1
        assert session.ended_at is not None
        assert 7100 <= session.duration <= 7300  # two hours of wall time


# ---------------------------------------------------------------------------
# Retention / management commands
# ---------------------------------------------------------------------------

class TestRetentionCommands:
    def test_cleanup_purges_old_rows_and_redacts_ips(self):
        session = make_session()
        old_view = PageView.objects.create(page_url='/old', session=session)
        PageView.objects.filter(pk=old_view.pk).update(
            viewed_at=timezone.now() - timedelta(days=200),
        )
        keep_view = PageView.objects.create(page_url='/keep', session=session)

        fresh_device = make_device()  # seen now, ip kept
        aged_device = make_device()   # seen 60 days ago: ip redacted
        DeviceTracker.objects.filter(pk=aged_device.pk).update(
            last_seen=timezone.now() - timedelta(days=60),
        )
        dead_device = make_device()   # seen 200 days ago: removed
        DeviceTracker.objects.filter(pk=dead_device.pk).update(
            last_seen=timezone.now() - timedelta(days=200),
        )

        call_command('analytics_cleanup')

        assert not PageView.objects.filter(pk=old_view.pk).exists()
        assert PageView.objects.filter(pk=keep_view.pk).exists()
        aged_device.refresh_from_db()
        assert aged_device.ip_address is None
        fresh_device.refresh_from_db()
        assert fresh_device.ip_address == '9.9.9.9'  # recent device keeps its IP
        assert not DeviceTracker.objects.filter(pk=dead_device.pk).exists()

    def test_cleanup_dry_run_changes_nothing(self):
        session = make_session()
        old_view = PageView.objects.create(page_url='/old', session=session)
        PageView.objects.filter(pk=old_view.pk).update(
            viewed_at=timezone.now() - timedelta(days=400),
        )
        call_command('analytics_cleanup', '--dry-run')
        assert PageView.objects.filter(pk=old_view.pk).exists()

    def test_cleanup_rejects_bad_retention(self):
        from django.core.management.base import CommandError
        with pytest.raises(CommandError):
            call_command('analytics_cleanup', '--retention-days', '0')

    def test_daily_stats_command(self):
        call_command('analytics_daily_stats')
        assert DailyStats.objects.filter(date=timezone.now().date()).exists()

    def test_daily_stats_command_rejects_bad_date(self):
        from django.core.management.base import CommandError
        with pytest.raises(CommandError):
            call_command('analytics_daily_stats', '--date', 'not-a-date')
        with pytest.raises(CommandError):
            call_command(
                'analytics_daily_stats',
                '--date', str(timezone.now().date() + timedelta(days=1)),
            )
