"""
Analytics middleware: tracks devices, sessions and page views.

Design rules (kept deliberately boring so tracking can never hurt the app):

* Never raises — analytics failures are logged, not surfaced.
* Workspace-scoped — every tracked session records the workspace it belongs
  to (resolved without side effects: no workspaces are auto-created here),
  so dashboards can filter to the active tenant.
* AJAX polls are not page views — "live" endpoints (which send the standard
  ``X-Requested-With`` header) update liveness only, so the dashboard's own
  polling cannot inflate its statistics.
* Sessions close on idle — after ``SESSION_IDLE_MINUTES`` without activity a
  new tracked session starts and the old one is finalised with a real
  duration, instead of one session row growing forever.
* Cookies are HttpOnly (server-side only) and honour the deployment's secure
  cookie policy.
"""
import logging
import re
import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from stockT.models import DeviceTracker, PageView, SessionTracker, Workspace, WorkspaceMember

logger = logging.getLogger('stockT')

DEVICE_COOKIE = 'device_id'
SESSION_IDLE_MINUTES = 30
SKIP_PATHS = re.compile(
    r'^/(static|admin|django-admin|health|sw\.js|manifest\.json|favicon|__debug__|media)(/|$)'
)


def _client_ip(request):
    """Return the client IP, trusting X-Forwarded-For only behind a proxy."""
    if getattr(settings, 'TRUST_X_FORWARDED_FOR', False):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _is_xhr(request):
    """True for AJAX/polling requests (fetch with the conventional header)."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _resolve_workspace(request, user):
    """Workspace for this request without creating anything as a side effect.

    Resolution mirrors ``workspace.current_workspace`` minus the
    auto-provisioning step: the session's active workspace when it is valid,
    otherwise the user's earliest membership.
    """
    if user is None:
        return None
    ws_id = request.session.get('workspace_id')
    if ws_id:
        workspace = Workspace.objects.filter(
            id=ws_id, is_active=True, memberships__user=user,
        ).first()
        if workspace:
            return workspace
    membership = WorkspaceMember.objects.filter(
        user=user, workspace__is_active=True,
    ).order_by('joined_at', 'id').first()
    return membership.workspace if membership else None


class AnalyticsMiddleware(MiddlewareMixin):
    """Record page views, sessions and device information."""

    def process_request(self, request):
        try:
            self._track(request)
        except Exception:
            logger.exception('Analytics tracking failed')
        return None

    def _track(self, request):
        path = request.path
        if SKIP_PATHS.match(path):
            return

        # --- Device -------------------------------------------------------
        device_id = request.COOKIES.get(DEVICE_COOKIE)
        if not device_id or len(device_id) != 32:
            device_id = uuid.uuid4().hex
        request._analytics_device_id = device_id

        ua_string = request.META.get('HTTP_USER_AGENT', '')
        device_type = browser = os_name = 'Unknown'
        try:
            from user_agents import parse as parse_ua
            ua = parse_ua(ua_string)
            device_type = 'Mobile' if ua.is_mobile else 'Tablet' if ua.is_tablet else 'Desktop' if ua.is_pc else 'Other'
            browser = f'{ua.browser.family} {ua.browser.version_string}'.strip()
            os_name = f'{ua.os.family} {ua.os.version_string}'.strip()
        except Exception:
            pass

        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        now = timezone.now()

        device, created = DeviceTracker.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_type': device_type,
                'browser': browser,
                'os': os_name,
                'ip_address': _client_ip(request),
                'user_agent': ua_string,
                'last_seen': now,
                'user': user,
            },
        )
        if not created:
            updates = ['last_seen', 'user']
            device.last_seen = now
            if user is not None and device.user_id != user.id:
                device.user = user
            if ua_string and device.user_agent != ua_string:
                device.user_agent = ua_string
                updates.append('user_agent')
            device.save(update_fields=updates)

        # --- Session -----------------------------------------------------
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        session_key = session_key or uuid.uuid4().hex
        if len(session_key) > 32:
            session_key = session_key[:32]

        workspace = _resolve_workspace(request, user)
        idle_cutoff = now - timedelta(minutes=SESSION_IDLE_MINUTES)
        track_session = SessionTracker.objects.filter(session_id=session_key).first()

        if track_session and track_session.last_activity < idle_cutoff:
            # Idle gap exceeded: finalise the old visit and start a fresh
            # session row under the same Django session key.
            self._close_session(track_session, session_key)
            track_session = None

        if track_session is None:
            track_session, _ = SessionTracker.objects.get_or_create(
                session_id=session_key,
                defaults={
                    'device': device,
                    'user': user,
                    'workspace': workspace,
                    'last_activity': now,
                    'entry_page': path,
                    'duration': 0,
                },
            )
        else:
            updates = ['last_activity', 'duration']
            track_session.last_activity = now
            track_session.duration = max(int((now - track_session.started_at).total_seconds()), 0)
            if user is not None and track_session.user_id != user.id:
                track_session.user = user
                updates.append('user')
            # Sessions often start before login; adopt the workspace as soon
            # as the member is known so their activity is scoped correctly.
            if user is not None and not track_session.workspace_id and workspace is not None:
                track_session.workspace = workspace
                updates.append('workspace')
            if not _is_xhr(request):
                track_session.exit_page = path
                updates.append('exit_page')
            track_session.save(update_fields=updates)

        # --- Page view / action -------------------------------------------
        # AJAX polls update liveness (handled above) but are never counted as
        # page views or actions — otherwise the live dashboard inflates its
        # own numbers once a minute.
        if _is_xhr(request):
            return
        if request.method == 'GET':
            PageView.objects.create(
                page_url=path[:500],
                page_title='',
                session=track_session,
            )
            track_session.pages_visited += 1
            track_session.save(update_fields=['pages_visited'])
            if track_session.entry_page in (None, ''):
                track_session.entry_page = path
                track_session.save(update_fields=['entry_page'])
        else:
            track_session.actions_performed += 1
            track_session.save(update_fields=['actions_performed'])

    @staticmethod
    def _close_session(session, session_key):
        """Finalise an idle session: real end time, real duration.

        The row's ``session_id`` gets a unique suffix so the base Django
        session key is free for the next visit's row (unique constraint).
        """
        ended = session.last_activity or timezone.now()
        session.duration = max(int((ended - session.started_at).total_seconds()), 0)
        session.ended_at = ended
        suffix = uuid.uuid4().hex[:8]
        candidate = f'{session_key}-{suffix}'
        while SessionTracker.objects.filter(session_id=candidate).exists():
            suffix = uuid.uuid4().hex[:8]
            candidate = f'{session_key}-{suffix}'
        session.session_id = candidate
        session.save(update_fields=['session_id', 'ended_at', 'duration'])
        logger.info(
            'Closed idle session for workspace %s (duration %ss)',
            session.workspace_id, session.duration,
        )

    def process_response(self, request, response):
        device_id = getattr(request, '_analytics_device_id', None)
        if device_id and DEVICE_COOKIE not in response.cookies:
            response.set_cookie(
                DEVICE_COOKIE, device_id,
                max_age=60 * 60 * 24 * 365,
                samesite='Lax',
                httponly=True,
                secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
            )
        return response
