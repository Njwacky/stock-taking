"""Template context processors for the stockT application."""
from .models import ContactInfo, PasswordResetRequest, StockUsage
from .workspace import (
    current_workspace,
    is_workspace_manager,
    registration_open,
    user_workspaces,
)


def workspace_context(request):
    """Expose workspace state and active-workspace permissions to templates."""
    user = getattr(request, 'user', None)
    active = None
    workspaces = []
    can_manage_workspace = False
    if user is not None and user.is_authenticated:
        active = current_workspace(request)
        workspaces = list(user_workspaces(user))
        can_manage_workspace = is_workspace_manager(user, active)
    return {
        'registration_open': registration_open(),
        'current_workspace': active,
        'user_workspaces': workspaces,
        'can_manage_workspace': can_manage_workspace,
    }


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
    """Expose pending usage requests in the active workspace to its managers."""
    user = getattr(request, 'user', None)
    count = 0
    if user is not None and user.is_authenticated:
        workspace = current_workspace(request)
        if workspace is not None and is_workspace_manager(user, workspace):
            count = StockUsage.objects.filter(
                workspace=workspace,
                status=StockUsage.STATUS_PENDING,
            ).count()
    return {'pending_stock_usage_count': count}
