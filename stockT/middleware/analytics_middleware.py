"""
Analytics middleware: tracks devices, sessions and page views.

Never raises - analytics must not break request handling.
"""
import logging
import re
import uuid

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from stockT.models import DeviceTracker, PageView, SessionTracker

logger = logging.getLogger('stockT')

DEVICE_COOKIE = 'device_id'
SKIP_PATHS = re.compile(
    r'^/(static|admin|django-admin|health|sw\.js|manifest\.json|favicon|__debug__|media)(/|$)'
)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


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

        track_session, s_created = SessionTracker.objects.get_or_create(
            session_id=session_key,
            defaults={
                'device': device,
                'user': user,
                'last_activity': now,
                'entry_page': path,
            },
        )
        if not s_created:
            track_session.last_activity = now
            track_session.exit_page = path
            if user is not None and track_session.user_id != user.id:
                track_session.user = user
            track_session.save(update_fields=['last_activity', 'exit_page', 'user'])

        # --- Page view ---------------------------------------------------
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

    def process_response(self, request, response):
        device_id = getattr(request, '_analytics_device_id', None)
        if device_id and DEVICE_COOKIE not in response.cookies:
            response.set_cookie(
                DEVICE_COOKIE, device_id,
                max_age=60 * 60 * 24 * 365,
                samesite='Lax',
            )
        return response
