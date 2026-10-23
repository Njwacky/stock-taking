"""Authentication backends and trusted client-address helpers."""
import ipaddress

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from axes.backends import AxesStandaloneBackend

User = get_user_model()


def axes_client_ip(request):
    """Resolve the login client IP without trusting arbitrary forwarded headers.

    The production nginx configuration overwrites ``X-Real-IP`` with its
    immediate peer address. Only trust that header when deployment settings
    explicitly enable trusted proxy headers; local/direct requests use
    ``REMOTE_ADDR`` so a client cannot spoof its lockout identity.
    """
    remote_addr = request.META.get('REMOTE_ADDR', '')
    candidate = remote_addr
    if settings.TRUST_X_FORWARDED_FOR:
        candidate = request.META.get('HTTP_X_REAL_IP', '') or remote_addr
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        try:
            return str(ipaddress.ip_address(remote_addr))
        except ValueError:
            return None


class RequestOptionalAxesBackend(AxesStandaloneBackend):
    """Apply Axes to HTTP logins while preserving non-request auth utilities.

    Django's test client and command-line code may call ``authenticate`` with
    no request context. Such calls have no reliable client IP to throttle, so
    let the regular authentication backend handle them instead of raising.
    Browser requests always provide a request and remain rate-limited.
    """

    def authenticate(self, request=None, **credentials):
        if request is None:
            return None
        return super().authenticate(request, **credentials)


class CaseInsensitiveModelBackend(ModelBackend):
    """Authenticate users regardless of username letter casing."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            # Run the default password hasher to reduce timing differences.
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
