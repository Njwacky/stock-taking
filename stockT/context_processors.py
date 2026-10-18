"""Template context processors for the stockT application."""
from .models import ContactInfo, PasswordResetRequest, StockUsage
from .workspace import registration_open


def workspace_context(request):
    """Expose single-workspace state (e.g. whether signup is still open)."""
    return {'registration_open': registration_open()}


def pending_reset_requests(request):
    """Expose the number of pending password reset requests to staff."""
    user = getattr(request, 'user', None)
    count = 0
    if user is not None and user.is_authenticated and user.is_manager:
        count = PasswordResetRequest.objects.filter(status=PasswordResetRequest.STATUS_PENDING).count()
    return {'pending_reset_requests_count': count}


def footer_contacts(request):
    """Expose active footer contacts to every template."""
    return {'footer_contacts': ContactInfo.objects.filter(is_active=True).order_by('order', 'id')}


def pending_stock_usage_count(request):
    """Expose the number of pending stock usage requests to staff."""
    user = getattr(request, 'user', None)
    count = 0
    if user is not None and user.is_authenticated and user.is_manager:
        count = StockUsage.objects.filter(status=StockUsage.STATUS_PENDING).count()
    return {'pending_stock_usage_count': count}
