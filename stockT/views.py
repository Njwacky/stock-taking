"""
Views for the stockT application.

Reconstructed from the project's documentation, test scripts and client-side
JavaScript contracts (static/js/*.js).
"""
import csv
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .analytics_service import AnalyticsService
from .forms import (
    AddUserForm,
    ContactInfoForm,
    EditUserForm,
    LimitedEditUserForm,
    ProfileForm,
    RegisterForm,
    StockUsageForm,
    UserCommentForm,
    WorkspaceForm,
    WorkspaceMemberAddForm,
)
from .models import (
    ContactInfo,
    DailyStats,
    DeviceTracker,
    Kit,
    KitType,
    NotificationLog,
    PageView,
    PasswordResetRequest,
    SessionTracker,
    StockUsage,
    User,
    UserComment,
    Workspace,
    WorkspaceMember,
)
from .workspace import (
    create_workspace,
    current_workspace,
    ensure_user_workspace,
    get_membership,
    is_workspace_manager,
    registration_open,
    set_current_workspace,
    workspace_member_users,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_manager(user):
    return user.is_authenticated and user.is_manager


def _ws(request):
    """The workspace this request acts in (see workspace.current_workspace)."""
    return current_workspace(request)


def _ws_kit_types(workspace):
    """Kit types visible inside a workspace (legacy unassigned rows included)."""
    return KitType.objects.filter(Q(workspace=workspace) | Q(workspace__isnull=True))


def _ws_rows(qs, workspace):
    """Scope any workspace-owned queryset (kits, usages) to the workspace."""
    return qs.filter(Q(workspace=workspace) | Q(workspace__isnull=True))


def _kit_stats(workspace=None):
    """Aggregated kit statistics used by the dashboard pie chart."""
    kits = Kit.objects.filter(is_active=True)
    if workspace is not None:
        kits = _ws_rows(kits, workspace)
    rows = list(
        kits
        .values('kit_type_fk__name')
        .annotate(
            kit_type=F('kit_type_fk__name'),
            total_quantity=Sum('quantity'),
            user_count=Count('user', distinct=True),
        )
        .order_by('-total_quantity')
    )
    peak = max((row['total_quantity'] or 0) for row in rows) if rows else 0
    for row in rows:
        row['kit_type'] = row['kit_type'] or 'Unassigned'
        row['bar_width'] = round((row['total_quantity'] or 0) / peak * 100) if peak else 0
    return rows


def _kits_queryset(request):
    workspace = _ws(request)
    kits = _ws_rows(Kit.objects.filter(is_active=True), workspace)
    if is_workspace_manager(request.user, workspace):
        return kits.select_related('user', 'kit_type_fk', 'created_by')
    return kits.filter(user=request.user).select_related('user', 'kit_type_fk', 'created_by')


SORT_FIELDS = {
    'timestamp': 'timestamp',
    'quantity': 'quantity',
    'kit_type': 'kit_type_fk__name',
    'condition': 'condition',
    'user': 'user__username',
    'location': 'location',
}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _filtered_kits(request):
    """Apply the dashboard's user/search/sort/order filters.

    Shared by the dashboard table and the CSV export so an export always
    matches exactly what the table shows.
    """
    kits = _kits_queryset(request)

    user_filter = request.GET.get('user', '')
    search = request.GET.get('search', '').strip()
    sort = SORT_FIELDS.get(request.GET.get('sort', 'timestamp'), 'timestamp')
    order = 'asc' if request.GET.get('order', 'desc') == 'asc' else 'desc'

    if user_filter:
        if user_filter.isdigit():
            kits = kits.filter(user__id=user_filter)
        else:
            kits = kits.filter(user__username=user_filter)
    if search:
        kits = kits.filter(
            Q(kit_type_fk__name__icontains=search)
            | Q(kit_type_string__icontains=search)
            | Q(location__icontains=search)
            | Q(notes__icontains=search)
            | Q(user__username__icontains=search)
        )

    kits = kits.order_by(('-' if order == 'desc' else '') + sort)
    filters = {'user': user_filter, 'search': search, 'sort': request.GET.get('sort', 'timestamp'), 'order': request.GET.get('order', 'desc')}
    return kits, filters


@login_required
def export_kits_csv(request):
    """Download the kit table as CSV (same filters and scope as the dashboard)."""
    import csv

    from django.http import HttpResponse

    kits, filters = _filtered_kits(request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f'stock_export_{timezone.localtime().date().isoformat()}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # BOM so Excel opens UTF-8 correctly.
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Kit Type', 'Code', 'Quantity', 'Condition', 'User',
        'Location', 'Expiration Date', 'Added By', 'Added At', 'Last Updated', 'Notes',
    ])
    for kit in kits.select_related('user', 'kit_type_fk', 'created_by'):
        writer.writerow([
            kit.id,
            kit.kit_type_name,
            kit.kit_type_fk.code if kit.kit_type_fk else '',
            kit.quantity,
            kit.get_condition_display(),
            kit.user.username,
            kit.location or '',
            kit.expiration_date.isoformat() if kit.expiration_date else '',
            kit.created_by.username if kit.created_by else '',
            timezone.localtime(kit.timestamp).strftime('%Y-%m-%d %H:%M'),
            timezone.localtime(kit.last_updated).strftime('%Y-%m-%d %H:%M'),
            kit.notes or '',
        ])
    return response


def dashboard(request):
    """Main dashboard: kit table with filtering/sorting for staff, landing page otherwise."""
    if not request.user.is_authenticated:
        return render(request, 'dashboard.html', {'public_view': True})

    kits, filters = _filtered_kits(request)
    page_number = request.GET.get('page', '1')

    workspace = _ws(request)
    if request.method == 'POST' and request.POST.get('action') == 'bulk_delete' and is_workspace_manager(request.user, workspace):
        ids = request.POST.getlist('kit_ids')
        _ws_rows(Kit.objects.filter(id__in=ids, is_active=True), workspace).delete()
        messages.success(request, f'{len(ids)} kit(s) deleted.')
        return redirect('dashboard')

    paginator = Paginator(kits, 15)
    page_obj = paginator.get_page(page_number)

    summary_scope = _kits_queryset(request)
    summary = summary_scope.aggregate(
        total_quantity=Sum('quantity'),
        items=Count('id'),
        locations=Count('location', distinct=True),
    )
    summary['total_quantity'] = summary['total_quantity'] or 0
    summary['kit_types'] = summary_scope.values('kit_type_fk').distinct().count()

    context = {
        'public_view': False,
        'kits': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'kit_stats': _kit_stats(workspace),
        'summary': summary,
        'users': workspace_member_users(workspace) if is_workspace_manager(request.user, workspace) else [],
        'filters': filters,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'table_html': render_to_string('partials/kit_table.html', context, request),
            'pagination_html': render_to_string('partials/pagination.html', context, request),
            'kit_stats': _kit_stats(workspace),
        })

    return render(request, 'dashboard.html', context)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def register(request):
    """
    Open registration — everyone can sign up.

    Each new account is provisioned with its own personal workspace (the
    user is its Owner) and can start using the app immediately. There is no
    one-time setup and registration never closes.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save(commit=False)
            user.save()
            workspace = ensure_user_workspace(user)
        set_current_workspace(request, workspace)
        # Multiple auth backends are configured, so the backend must be explicit.
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(
            request,
            f'Welcome, {user.username}! Your workspace “{workspace.name}” is ready — '
            'and it comes pre-loaded with the standard kit types.',
        )
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form})


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------

@login_required
def workspace_create(request):
    """Create an additional workspace; the creator becomes its Owner."""
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            workspace = create_workspace(form.cleaned_data['name'], request.user)
            set_current_workspace(request, workspace)
            messages.success(
                request,
                f'Workspace “{workspace.name}” created and selected. '
                'It already has the standard kit types ready to use.',
            )
            return redirect('dashboard')
    else:
        form = WorkspaceForm()
    return render(request, 'workspace_create.html', {'form': form})


@login_required
@require_POST
def workspace_switch(request):
    """Switch the session's active workspace (must be a member)."""
    workspace = Workspace.objects.filter(
        id=request.POST.get('workspace_id'), is_active=True, memberships__user=request.user,
    ).first()
    if not workspace:
        messages.error(request, 'You can only switch to a workspace you belong to.')
    else:
        set_current_workspace(request, workspace)
        messages.success(request, f'Switched to “{workspace.name}”.')
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
def workspace_settings(request):
    """Workspace settings: rename, members, leave."""
    workspace = _ws(request)
    membership = get_membership(request.user, workspace)
    can_manage = is_workspace_manager(request.user, workspace)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rename' and can_manage:
            form = WorkspaceForm(request.POST, instance=workspace)
            if form.is_valid():
                form.save()
                messages.success(request, 'Workspace renamed.')
                return redirect('workspace_settings')
        else:
            form = WorkspaceForm(instance=workspace)
        return render(request, 'workspace_settings.html', {
            'form': form,
            'workspace': workspace,
            'membership': membership,
            'can_manage': can_manage,
            'members': workspace.memberships.select_related('user').order_by('joined_at'),
            'add_member_form': WorkspaceMemberAddForm(),
        })

    form = WorkspaceForm(instance=workspace)
    return render(request, 'workspace_settings.html', {
        'form': form,
        'workspace': workspace,
        'membership': membership,
        'can_manage': can_manage,
        'members': workspace.memberships.select_related('user').order_by('joined_at'),
        'add_member_form': WorkspaceMemberAddForm(),
    })


@login_required
@require_POST
def workspace_member_add(request):
    """Add an existing registered user to the current workspace."""
    workspace = _ws(request)
    if not is_workspace_manager(request.user, workspace):
        messages.error(request, 'Only workspace owners and admins can add members.')
        return redirect('workspace_settings')

    form = WorkspaceMemberAddForm(request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        role = form.cleaned_data['role']
        if get_membership(user, workspace):
            messages.info(request, f'{user.username} is already a member of this workspace.')
        else:
            WorkspaceMember.objects.create(workspace=workspace, user=user, role=role)
            messages.success(request, f'{user.username} added to “{workspace.name}” as {role}.')
    else:
        for field, errs in form.errors.items():
            messages.error(request, f'{" ".join(errs)}')
    return redirect('workspace_settings')


@login_required
@require_POST
def workspace_member_remove(request):
    """Remove a member (or leave the workspace yourself)."""
    workspace = _ws(request)
    target_id = request.POST.get('user_id')
    membership = get_membership(request.user, workspace)
    can_manage = is_workspace_manager(request.user, workspace)

    target_membership = WorkspaceMember.objects.filter(
        workspace=workspace, user_id=target_id,
    ).first()
    if not target_membership:
        messages.error(request, 'That user is not a member of this workspace.')
        return redirect('workspace_settings')

    leaving_self = str(target_id) == str(request.user.id)
    if not (can_manage or leaving_self):
        messages.error(request, 'Only workspace owners and admins can remove members.')
        return redirect('workspace_settings')
    if target_membership.role == WorkspaceMember.ROLE_OWNER:
        messages.error(request, 'The workspace owner cannot be removed.')
        return redirect('workspace_settings')

    username = target_membership.user.username
    target_membership.delete()
    if leaving_self:
        messages.success(request, f'You left “{workspace.name}”.')
        return redirect('dashboard')
    messages.success(request, f'{username} removed from “{workspace.name}”.')
    return redirect('workspace_settings')


def logout_confirm(request):
    """Confirm-and-logout: POST actually logs the user out (this was broken —
    the view used to just re-render the page and never called auth.logout)."""
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')
    return render(request, 'logout_confirm.html')


def password_reset_request(request):
    """Allow users to request a password reset from an administrator."""
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        clock_number = (request.POST.get('clock_number') or '').strip()
        user = User.objects.filter(username__iexact=username, clock_number=clock_number).first()
        if user:
            PasswordResetRequest.objects.create(
                username=user.username,
                clock_number=clock_number,
                user=user,
            )
            messages.success(request, 'Your reset request has been submitted to an administrator.')
            return redirect('login')
        messages.error(request, 'No account matches that username and clock number.')
    return render(request, 'password_reset_request.html')


@login_required
def manage_reset_requests(request):
    """Managers process password reset requests here (approve sets a new
    password; reject closes the request)."""
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to manage password resets.')
        return redirect('dashboard')
    requests_qs = PasswordResetRequest.objects.select_related('user', 'processed_by')
    return render(request, 'manage_reset_requests.html', {'requests': requests_qs})


@login_required
@require_POST
def process_reset_request(request, reset_id):
    """Approve (set new password) or reject a password reset request."""
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to manage password resets.')
        return redirect('dashboard')
    reset = get_object_or_404(PasswordResetRequest, id=reset_id)
    if reset.status != PasswordResetRequest.STATUS_PENDING:
        messages.info(request, 'That request has already been processed.')
        return redirect('manage_reset_requests')

    action = request.POST.get('action')
    if action == 'reject':
        reset.status = PasswordResetRequest.STATUS_REJECTED
        reset.processed_at = timezone.now()
        reset.processed_by = request.user
        reset.save()
        messages.success(request, f'Reset request for {reset.username} rejected.')
        return redirect('manage_reset_requests')

    if action == 'approve':
        password = request.POST.get('new_password') or ''
        confirm = request.POST.get('confirm_password') or ''
        if not password or password != confirm:
            messages.error(request, 'Passwords do not match (or are empty).')
            return redirect('manage_reset_requests')
        try:
            validate_password(password, user=reset.user)
        except ValidationError as exc:
            messages.error(request, 'Password not accepted: ' + ' '.join(exc.messages))
            return redirect('manage_reset_requests')
        reset.user.set_password(password)
        reset.user.save(update_fields=['password'])
        reset.status = PasswordResetRequest.STATUS_APPROVED
        reset.processed_at = timezone.now()
        reset.processed_by = request.user
        reset.save()
        messages.success(
            request,
            f'Password updated for {reset.username}. Share it with them securely.',
        )
        return redirect('manage_reset_requests')

    messages.error(request, 'Unknown action.')
    return redirect('manage_reset_requests')


@login_required
@require_POST
def set_user_password(request, user_id):
    """Admins set a member's password directly (e.g. new starter on the phone)."""
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can set passwords.')
        return redirect('manage_users')
    target = get_object_or_404(User, id=user_id)
    password = request.POST.get('new_password') or ''
    confirm = request.POST.get('confirm_password') or ''
    if not password or password != confirm:
        messages.error(request, 'Passwords do not match (or are empty).')
        return redirect('edit_user', user_id=target.id)
    try:
        validate_password(password, user=target)
    except ValidationError as exc:
        messages.error(request, 'Password not accepted: ' + ' '.join(exc.messages))
        return redirect('edit_user', user_id=target.id)
    target.set_password(password)
    target.save(update_fields=['password'])
    messages.success(request, f'Password updated for {target.username}.')
    return redirect('edit_user', user_id=target.id)


@login_required
def change_password(request):
    """Let any user change their own password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the session alive across the password change.
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Your password has been changed.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


# ---------------------------------------------------------------------------
# Kit types
# ---------------------------------------------------------------------------

@login_required
def manage_kit_types(request):
    """Manage the current workspace's kit types (Add Stock / Track Usage / Distribute)."""
    workspace = _ws(request)
    if not is_workspace_manager(request.user, workspace):
        messages.error(request, 'You do not have permission to manage kit types.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = (request.POST.get('name') or '').strip()
            code = (request.POST.get('code') or '').strip()
            description = (request.POST.get('description') or '').strip()
            unit = (request.POST.get('unit_of_measure') or 'pieces').strip() or 'pieces'
            existing = _ws_kit_types(workspace).filter(Q(name__iexact=name) | Q(code__iexact=code))
            if not name or not code:
                messages.error(request, 'Name and code are required.')
            elif existing.exists():
                messages.error(request, 'A kit type with that name or code already exists in this workspace.')
            else:
                KitType.objects.create(
                    name=name, code=code, description=description or None,
                    unit_of_measure=unit, created_by=request.user, workspace=workspace,
                )
                messages.success(request, f'Kit type “{name}” added.')
        elif action == 'toggle':
            kit_type = get_object_or_404(_ws_kit_types(workspace), id=request.POST.get('kit_type_id'))
            kit_type.is_active = not kit_type.is_active
            kit_type.save(update_fields=['is_active'])
            messages.success(request, f'Kit type “{kit_type.name}” {"activated" if kit_type.is_active else "deactivated"}.')
        return redirect('manage_kit_types')

    kit_types = _ws_kit_types(workspace).order_by('name')
    return render(request, 'manage_kit_types.html', {'kit_types': kit_types})


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def offline(request):
    return render(request, 'offline.html')


def service_worker(request):
    from django.http import FileResponse, Http404
    from django.conf import settings
    import os
    path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    if not os.path.exists(path):
        raise Http404('Service worker not found')
    response = FileResponse(open(path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def manifest(request):
    from django.http import FileResponse, Http404
    from django.conf import settings
    import os
    path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if not os.path.exists(path):
        raise Http404('Manifest not found')
    return FileResponse(open(path, 'rb'), content_type='application/manifest+json')


# ---------------------------------------------------------------------------
# Add stock items
# ---------------------------------------------------------------------------

@login_required
def add_items(request):
    """Add stock items for yourself (or another workspace member when permitted)."""
    workspace = _ws(request)
    kit_types = _ws_kit_types(workspace).filter(is_active=True).order_by('name')
    can_select_user = is_workspace_manager(request.user, workspace)
    target_users = workspace_member_users(workspace) if can_select_user else [request.user]

    if request.method == 'POST':
        target_id = request.POST.get('user', str(request.user.id))
        target = get_object_or_404(User, id=target_id)
        if not can_select_user and target.id != request.user.id:
            messages.error(request, 'You can only add stock for yourself.')
            return redirect('add_items')
        if can_select_user and not workspace_member_users(workspace).filter(id=target.id).exists():
            messages.error(request, f'{target.username} is not a member of this workspace.')
            return redirect('add_items')

        created = 0
        for kit_type in kit_types:
            qty_raw = request.POST.get(f'quantity_{kit_type.id}', '0')
            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue
            Kit.objects.create(
                user=target,
                kit_type_fk=kit_type,
                kit_type_string=kit_type.name[:20],
                quantity=qty,
                condition=request.POST.get(f'condition_{kit_type.id}', Kit.CONDITION_NEW),
                location=request.POST.get(f'location_{kit_type.id}', '') or None,
                notes=request.POST.get(f'notes_{kit_type.id}', '') or None,
                expiration_date=request.POST.get(f'expiration_{kit_type.id}') or None,
                created_by=request.user,
                workspace=workspace,
            )
            created += 1
        if created:
            messages.success(request, f'{created} kit type(s) added for {target.username}.')
        else:
            messages.warning(request, 'No quantities were entered, nothing was added.')
        return redirect('add_items')

    return render(request, 'add_items.html', {
        'kit_types': kit_types,
        'can_select_user': can_select_user,
        'target_users': target_users,
    })


def _kit_to_dict(kit):
    return {
        'id': kit.id,
        'kit_type': kit.kit_type_name,
        'kit_type_code': kit.kit_type_fk.code if kit.kit_type_fk else '',
        'quantity': kit.quantity,
        'condition': kit.condition,
        'is_active': kit.is_active,
        'location': kit.location or '',
        'notes': kit.notes or '',
        'expiration_date': kit.expiration_date.isoformat() if kit.expiration_date else None,
        'timestamp': kit.timestamp.isoformat(),
        'last_updated': kit.last_updated.isoformat(),
    }


@login_required
def get_user_kits(request, user_id):
    workspace = _ws(request)
    if not is_workspace_manager(request.user, workspace) and request.user.id != user_id:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    user = get_object_or_404(User, id=user_id)
    kits = _ws_rows(Kit.objects.filter(user=user, is_active=True), workspace).select_related('kit_type_fk')
    return JsonResponse({'success': True, 'kits': [_kit_to_dict(k) for k in kits]})


@login_required
def get_kit_types_for_edit(request):
    types = _ws_kit_types(_ws(request)).filter(is_active=True).order_by('name')
    return JsonResponse({
        'success': True,
        'kit_types': [{'id': t.id, 'name': t.name, 'code': t.code} for t in types],
    })


@login_required
@require_POST
def update_kit(request, kit_id):
    workspace = _ws(request)
    kit = get_object_or_404(_ws_rows(Kit.objects.filter(is_active=True), workspace), id=kit_id)
    if not is_workspace_manager(request.user, workspace) and kit.user_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    errors = {}
    qty_raw = request.POST.get('quantity')
    if qty_raw is not None:
        try:
            qty = int(qty_raw)
            if qty < 0:
                raise ValueError
            kit.quantity = qty
        except (TypeError, ValueError):
            errors['quantity'] = 'Enter a valid quantity.'

    if 'kit_type' in request.POST:
        kit_type = _ws_kit_types(workspace).filter(id=request.POST.get('kit_type')).first()
        if kit_type:
            kit.kit_type_fk = kit_type
            kit.kit_type_string = kit_type.name[:20]
        else:
            errors['kit_type'] = 'Unknown kit type.'

    for field in ('location', 'notes'):
        if field in request.POST:
            setattr(kit, field, request.POST.get(field) or None)
    if 'condition' in request.POST:
        condition = request.POST.get('condition')
        valid_conditions = [c[0] for c in Kit.CONDITION_CHOICES]
        if condition in valid_conditions:
            kit.condition = condition
        else:
            errors['condition'] = 'Invalid condition value.'
    if 'is_active' in request.POST:
        kit.is_active = request.POST.get('is_active') in ('on', 'true', 'True', '1')
    if 'expiration_date' in request.POST:
        value = request.POST.get('expiration_date') or None
        kit.expiration_date = value

    if errors:
        return JsonResponse({'success': False, 'error': 'Validation failed', 'errors': errors}, status=400)

    kit.save()
    return JsonResponse({'success': True, 'kit': _kit_to_dict(kit)})


@login_required
@require_POST
def delete_kit(request, kit_id):
    workspace = _ws(request)
    kit = get_object_or_404(_ws_rows(Kit.objects.filter(is_active=True), workspace), id=kit_id)
    if not is_workspace_manager(request.user, workspace) and kit.user_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    kit.delete()
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@login_required
def manage_users(request):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('dashboard')

    search = request.GET.get('search', '').strip()
    users = User.objects.all().order_by('username')
    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(clock_number__icontains=search)
            | Q(department__icontains=search)
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        ids = request.POST.getlist('user_ids')
        if action == 'activate' and _is_manager(request.user):
            User.objects.filter(id__in=ids).update(is_active=True)
            messages.success(request, f'{len(ids)} user(s) activated.')
        elif action == 'deactivate' and request.user.is_admin:
            User.objects.filter(id__in=ids).exclude(id=request.user.id).update(is_active=False)
            messages.success(request, f'{len(ids)} user(s) deactivated.')
        return redirect('manage_users')

    return render(request, 'manage_users.html', {'users': users, 'search': search})


@login_required
def add_user(request):
    """
    Add a person to the workspace.

    Only the workspace Superadmin and administrators can add people —
    there is no public self-registration after the workspace is set up.
    """
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can add people to the workspace.')
        return redirect('manage_users')
    form = AddUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        workspace = _ws(request)
        with transaction.atomic():
            user = form.save(commit=False)
            user.save()
            # Account roles are system-wide; membership role is scoped to this
            # workspace. A newly added person starts as a workspace member.
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=user,
                role=WorkspaceMember.ROLE_MEMBER,
            )
        messages.success(
            request,
            f'{user.username} has been added to “{workspace.name}” as a '
            f'workspace member (account role: {user.get_role_display()}).',
        )
        return redirect('manage_users')
    return render(request, 'add_user.html', {'form': form})


@login_required
def edit_user(request, user_id):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('dashboard')
    target = get_object_or_404(User, id=user_id)

    # Only admins can change roles or staff status. Managers use a restricted
    # form WITHOUT role/is_staff fields so they cannot escalate privileges.
    if not request.user.is_admin:
        restricted = LimitedEditUserForm(request.POST or None, instance=target)
        if request.method == 'POST':
            if restricted.is_valid():
                restricted.save()
                messages.success(request, f'User {target.username} updated.')
                return redirect('manage_users')
        return render(request, 'edit_user.html', {'form': restricted, 'target': target, 'restricted': True})

    if request.user.id == target.id and request.method == 'POST':
        # Guard against self-demotion.
        role = request.POST.get('role')
        if role and role != target.role:
            messages.error(request, 'You cannot change your own role.')
            return redirect('edit_user', user_id=target.id)

    form = EditUserForm(request.POST or None, instance=target)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'User {target.username} updated.')
        return redirect('manage_users')
    return render(request, 'edit_user.html', {'form': form, 'target': target, 'restricted': False})


@login_required
@require_POST
def delete_user(request, user_id):
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can delete users.')
        return redirect('manage_users')
    target = get_object_or_404(User, id=user_id)
    if target.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('manage_users')
    target.delete()
    messages.success(request, f'User {target.username} deleted.')
    return redirect('manage_users')


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def _qr_data_uri(profile_user):
    """Generate a QR code data URI pointing at the user's profile page."""
    try:
        import base64
        from io import BytesIO

        import qrcode

        url = f'/profile/{profile_user.id}/'
        img = qrcode.make(url)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None


@login_required
def profile(request):
    return render(request, 'profile.html', {
        'profile_user': request.user,
        'own_profile': True,
        'qr_data_uri': _qr_data_uri(request.user),
    })


@login_required
def user_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'own_profile': profile_user.id == request.user.id,
        'qr_data_uri': _qr_data_uri(profile_user),
    })


# ---------------------------------------------------------------------------
# Stock usage tracking
# ---------------------------------------------------------------------------

@login_required
def stock_usage_tracking(request):
    """Log stock usage at /tracking/."""
    workspace = _ws(request)
    kit_types = _ws_kit_types(workspace).filter(is_active=True).order_by('name')
    recent = _ws_rows(StockUsage.objects.filter(user=request.user), workspace)[:8]
    form = StockUsageForm(request.POST or None)
    form.fields['kit_type'].queryset = kit_types

    if request.method == 'POST':
        if form.is_valid():
            usage = form.save(commit=False)
            usage.user = request.user
            usage.clock_number = request.user.clock_number or ''
            usage.kit_type_name = usage.kit_type.name if usage.kit_type else ''
            usage.status = StockUsage.STATUS_PENDING
            usage.workspace = workspace
            usage.save()
            messages.success(request, 'Usage submitted for review.')
            return redirect('stock_usage_tracking')

    return render(request, 'stock_usage_tracking.html', {
        'form': form,
        'kit_types': kit_types,
        'recent': recent,
    })


@login_required
def stock_usage_history(request):
    workspace = _ws(request)
    status_filter = request.GET.get('status', '')
    if is_workspace_manager(request.user, workspace):
        usages = _ws_rows(StockUsage.objects.all(), workspace).select_related('user', 'kit_type', 'reviewed_by')
    else:
        usages = _ws_rows(StockUsage.objects.filter(user=request.user), workspace).select_related('user', 'kit_type', 'reviewed_by')
    if status_filter:
        usages = usages.filter(status=status_filter)
    return render(request, 'stock_usage_history.html', {
        'usages': usages,
        'status_filter': status_filter,
    })


@login_required
@require_POST
def review_stock_usage(request, usage_id):
    workspace = _ws(request)
    if not is_workspace_manager(request.user, workspace):
        messages.error(request, 'You do not have permission to review usage requests.')
        return redirect('stock_usage_history')

    action = request.POST.get('action')
    if action not in ('approve', 'reject'):
        messages.error(request, 'Unknown action.')
        return redirect(request.POST.get('next') or 'stock_usage_history')

    already_processed = False
    try:
        # Lock the request so two managers cannot approve the same request at
        # once. The signal's stock deduction runs inside this transaction too.
        with transaction.atomic():
            usage = get_object_or_404(
                _ws_rows(StockUsage.objects.select_for_update(), workspace),
                id=usage_id,
            )
            if usage.status != StockUsage.STATUS_PENDING:
                already_processed = True
            else:
                usage.admin_notes = request.POST.get('admin_notes', '') or None
                usage.reviewed_by = request.user
                usage.reviewed_at = timezone.now()
                if action == 'approve':
                    usage.status = StockUsage.STATUS_APPROVED
                else:
                    usage.status = StockUsage.STATUS_REJECTED
                usage.save()
    except ValidationError as exc:
        messages.error(
            request,
            'Usage was not approved: ' + ' '.join(exc.messages),
        )
        return redirect(request.POST.get('next') or 'stock_usage_history')

    if already_processed:
        messages.info(request, 'This usage request has already been reviewed or is no longer pending.')
    elif action == 'approve':
        messages.success(request, 'Usage approved and stock updated.')
    else:
        messages.success(request, 'Usage request rejected.')
    return redirect(request.POST.get('next') or 'stock_usage_history')


@login_required
@require_POST
def delete_stock_usage(request, usage_id):
    workspace = _ws(request)
    if not is_workspace_manager(request.user, workspace):
        messages.error(request, 'You do not have permission to delete usage records.')
        return redirect('stock_usage_history')
    usage = get_object_or_404(_ws_rows(StockUsage.objects.all(), workspace), id=usage_id)
    usage.delete()
    messages.success(request, 'Usage record deleted.')
    return redirect('stock_usage_history')


# ---------------------------------------------------------------------------
# Stock distribution
# ---------------------------------------------------------------------------

@login_required
def stock_distribution(request):
    """Distribute stock to workspace members, verified with the distributor's password.

    Access is limited to workspace managers/supervisors and administrators;
    regular users are redirected.
    """
    workspace = _ws(request)
    if not (request.user.is_supervisor or is_workspace_manager(request.user, workspace)):
        messages.error(request, 'Access denied. This portal is for managers and supervisors only.')
        return redirect('dashboard')

    kit_types = _ws_kit_types(workspace).filter(is_active=True).order_by('name')
    recipients = workspace_member_users(workspace).exclude(
        Q(is_superuser=True) | Q(role=User.ROLE_ADMIN),
    )
    recent_distributions = (
        _ws_rows(Kit.objects.filter(created_by__isnull=False), workspace)
        .select_related('user', 'created_by', 'kit_type_fk')
        .order_by('-timestamp')[:15]
    )

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_user')
        confirm_password = request.POST.get('confirm_password', '')

        if not recipient_id or not confirm_password:
            messages.error(request, 'Please select a user and enter your password for confirmation.')
            return render(request, 'stock_distribution.html', {
                'kit_types': kit_types,
                'recipients': recipients,
                'recent_distributions': recent_distributions,
            })

        if not authenticate(request, username=request.user.username, password=confirm_password):
            messages.error(request, 'Password verification failed')
            return render(request, 'stock_distribution.html', {
                'kit_types': kit_types,
                'recipients': recipients,
                'recent_distributions': recent_distributions,
            })

        recipient = get_object_or_404(User, id=recipient_id)
        if not workspace_member_users(workspace).filter(id=recipient.id).exists():
            messages.error(request, f'{recipient.username} is not a member of this workspace.')
            return redirect('stock_distribution')
        created = 0
        for kit_type in kit_types:
            try:
                qty = int(request.POST.get(f'kit_type_{kit_type.id}_qty', '0') or 0)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue
            Kit.objects.create(
                user=recipient,
                created_by=request.user,
                kit_type_fk=kit_type,
                kit_type_string=kit_type.name[:20],
                quantity=qty,
                condition=request.POST.get(f'kit_type_{kit_type.id}_condition', Kit.CONDITION_NEW),
                workspace=workspace,
            )
            created += 1

        if not created:
            messages.error(request, 'Please select at least one kit type')
            return render(request, 'stock_distribution.html', {
                'kit_types': kit_types,
                'recipients': recipients,
                'recent_distributions': recent_distributions,
            })

        messages.success(request, f'Stock distributed to {recipient.username} ({created} kit type(s)).')
        return redirect('stock_distribution')

    return render(request, 'stock_distribution.html', {
        'kit_types': kit_types,
        'recipients': recipients,
        'recent_distributions': recent_distributions,
    })


# ---------------------------------------------------------------------------
# Inventory helpers
# ---------------------------------------------------------------------------

@login_required
def most_received_kits(request):
    stats = _kit_stats(_ws(request))
    return render(request, 'most_received_kits.html', {'kit_stats': stats})


@login_required
def inventory_calculator(request):
    return render(request, 'inventory_calculator.html')


# ---------------------------------------------------------------------------
# Comments / feedback
# ---------------------------------------------------------------------------

@login_required
def submit_comment(request):
    form = UserCommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Thank you for your feedback!'})
            messages.success(request, 'Thank you for your feedback!')
            return redirect('my_comments')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please correct the errors below.'})
    return render(request, 'submit_comment.html', {'form': form})


@login_required
def my_comments(request):
    comments = UserComment.objects.filter(user=request.user)
    return render(request, 'my_comments.html', {'comments': comments})


@login_required
def my_comments_json(request):
    comments = UserComment.objects.filter(user=request.user)[:5]
    data = [
        {
            'id': c.id,
            'category': c.category,
            'category_display': c.get_category_display(),
            'subject': c.subject,
            'content': c.message,
            'status': c.status,
            'status_display': c.get_status_display(),
            'created_at': c.created_at.isoformat(),
            'admin_response': c.admin_response or '',
        }
        for c in comments
    ]
    return JsonResponse(data, safe=False)


@login_required
def manage_comments(request):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to manage comments.')
        return redirect('dashboard')
    status_filter = request.GET.get('status', '')
    comments = UserComment.objects.all().select_related('user', 'reviewed_by')
    if status_filter:
        comments = comments.filter(status=status_filter)
    return render(request, 'manage_comments.html', {
        'comments': comments,
        'status_filter': status_filter,
    })


@login_required
@require_POST
def update_comment_status(request, comment_id):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to update comments.')
        return redirect('dashboard')
    comment = get_object_or_404(UserComment, id=comment_id)
    status = request.POST.get('status')
    if status in dict(UserComment.STATUS_CHOICES):
        comment.status = status
        comment.reviewed_by = request.user
        comment.reviewed_at = timezone.now()
        comment.admin_response = request.POST.get('admin_response', comment.admin_response) or None
        comment.save()
        messages.success(request, 'Comment updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect(request.POST.get('next') or 'manage_comments')


# ---------------------------------------------------------------------------
# Admin management
# ---------------------------------------------------------------------------

@login_required
def manage_admins(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage administrators.')
        return redirect('dashboard')
    admins = User.objects.filter(Q(is_superuser=True) | Q(role=User.ROLE_ADMIN)).order_by('username')
    return render(request, 'manage_admins.html', {'admins': admins})


@login_required
def create_admin(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can create administrators.')
        return redirect('dashboard')
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        email = (request.POST.get('email') or '').strip()
        clock_number = (request.POST.get('clock_number') or '').strip() or None
        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'That username is already taken.')
        else:
            user = User.objects.create_user(
                username=username, password=password, email=email,
                clock_number=clock_number, role=User.ROLE_ADMIN,
                is_staff=True,
            )
            messages.success(request, f'Administrator {user.username} created.')
            return redirect('manage_admins')
    return render(request, 'create_admin.html')


@login_required
@require_POST
def promote_admin(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can promote users.')
        return redirect('dashboard')
    target = get_object_or_404(User, id=user_id)
    target.role = User.ROLE_ADMIN
    target.is_staff = True
    target.save(update_fields=['role', 'is_staff'])
    messages.success(request, f'{target.username} is now an administrator.')
    return redirect('manage_admins')


@login_required
@require_POST
def demote_admin(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can demote administrators.')
        return redirect('dashboard')
    target = get_object_or_404(User, id=user_id)
    if target.id == request.user.id:
        messages.error(request, 'You cannot demote yourself.')
        return redirect('manage_admins')
    if not (target.is_superuser or target.role == User.ROLE_ADMIN):
        messages.error(request, f'{target.username} is not an administrator.')
        return redirect('manage_admins')
    target.role = User.ROLE_USER
    target.is_staff = False
    target.is_superuser = False
    target.save(update_fields=['role', 'is_staff', 'is_superuser'])
    messages.success(request, f'{target.username} demoted to regular user.')
    return redirect('manage_admins')


# ---------------------------------------------------------------------------
# Footer contacts management
# ---------------------------------------------------------------------------

@login_required
def manage_footer_contacts(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage footer contacts.')
        return redirect('dashboard')
    contacts = ContactInfo.objects.all()
    return render(request, 'manage_footer_contacts.html', {'contacts': contacts})


@login_required
def add_footer_contact(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage footer contacts.')
        return redirect('dashboard')
    form = ContactInfoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact = form.save(commit=False)
        contact.created_by = request.user
        contact.save()
        messages.success(request, 'Contact added.')
        return redirect('manage_footer_contacts')
    return render(request, 'add_footer_contact.html', {'form': form})


@login_required
def edit_footer_contact(request, contact_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage footer contacts.')
        return redirect('dashboard')
    contact = get_object_or_404(ContactInfo, id=contact_id)
    form = ContactInfoForm(request.POST or None, instance=contact)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contact updated.')
        return redirect('manage_footer_contacts')
    return render(request, 'edit_footer_contact.html', {'form': form, 'contact': contact})


@login_required
def delete_footer_contact(request, contact_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage footer contacts.')
        return redirect('dashboard')
    contact = get_object_or_404(ContactInfo, id=contact_id)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact deleted.')
        return redirect('manage_footer_contacts')
    return render(request, 'delete_footer_contact.html', {'contact': contact})


@login_required
@require_POST
def toggle_footer_contact(request, contact_id):
    if not request.user.is_superuser:
        messages.error(request, 'Only superadmins can manage footer contacts.')
        return redirect('dashboard')
    contact = get_object_or_404(ContactInfo, id=contact_id)
    contact.is_active = not contact.is_active
    contact.save(update_fields=['is_active'])
    messages.success(request, f'Contact {"activated" if contact.is_active else "deactivated"}.')
    return redirect('manage_footer_contacts')


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notifications(request):
    notes = NotificationLog.objects.filter(sent_to=request.user).prefetch_related('read_by')
    return render(request, 'notifications.html', {'notifications': notes})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(NotificationLog, id=notification_id, sent_to=request.user)
    notification.read_by.add(request.user)
    return redirect('notifications')


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def _analytics_allowed(user):
    return user.is_authenticated and user.is_manager


PAGE_LABELS = {
    '/': 'Dashboard',
    '/add-items/': 'Add stock',
    '/tracking/': 'Track usage',
    '/tracking/history/': 'Usage history',
    '/stock-distribution/': 'Distribution',
    '/most-received-kits/': 'Stock ranking',
    '/calculator/': 'Calculators',
    '/analytics/': 'Analytics',
    '/analytics/devices/': 'Tracked devices',
    '/analytics/notifications/': 'Milestones',
    '/manage-users/': 'Team',
    '/kit-types/': 'Kit types',
    '/profile/': 'Profile',
    '/notifications/': 'Notifications',
    '/comments/my/': 'My feedback',
    '/comments/manage/': 'Feedback inbox',
    '/workspace/settings/': 'Workspace settings',
}


def _page_label(path):
    """Turn a tracked URL into a readable page name."""
    if not path:
        return 'Unknown'
    label = PAGE_LABELS.get(path.rstrip('/') + '/' if path != '/' else '/')
    if label:
        return label
    cleaned = path.strip('/').replace('-', ' ').replace('_', ' ').replace('/', ' / ')
    return cleaned.title() if cleaned else 'Home'


def _sparkline(values, width=96, height=30):
    """Build SVG polyline coordinates for a compact trend line."""
    if not values:
        return ''
    values = [float(v or 0) for v in values]
    peak = max(values)
    count = len(values)
    points = []
    for index, value in enumerate(values):
        x = round((index / (count - 1) * width) if count > 1 else width / 2, 1)
        if peak <= 0:
            y = height - 4
        else:
            y = round(height - 4 - (value / peak) * (height - 8), 1)
        points.append(f'{x},{y}')
    return ' '.join(points)


def _analytics_series(days):
    """Aggregate sessions, page views, devices and users for each day."""
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)

    def daily_map(queryset, date_field, value_field=None):
        rows = (
            queryset
            .filter(**{f'{date_field}__date__gte': start, f'{date_field}__date__lte': end})
            .annotate(day=TruncDate(date_field))
            .values('day')
        )
        if value_field:
            rows = rows.annotate(total=Count(value_field, distinct=True))
        else:
            rows = rows.annotate(total=Count('id'))
        return {row['day']: row['total'] for row in rows}

    sessions = daily_map(SessionTracker.objects.all(), 'started_at')
    page_views = daily_map(PageView.objects.all(), 'viewed_at')
    devices = daily_map(SessionTracker.objects.all(), 'started_at', 'device')
    users = daily_map(SessionTracker.objects.filter(user__isnull=False), 'started_at', 'user')

    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        series.append({
            'date': day,
            'label': day.strftime('%d %b'),
            'sessions': sessions.get(day, 0),
            'page_views': page_views.get(day, 0),
            'devices': devices.get(day, 0),
            'users': users.get(day, 0),
        })
    return series


def _period_totals(start, end):
    sessions = SessionTracker.objects.filter(started_at__date__gte=start, started_at__date__lte=end)
    views = PageView.objects.filter(viewed_at__date__gte=start, viewed_at__date__lte=end)
    return {
        'sessions': sessions.count(),
        'page_views': views.count(),
        'users': sessions.filter(user__isnull=False).values('user').distinct().count(),
        'devices': sessions.values('device').distinct().count(),
    }


def _delta(current, previous):
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


@login_required
def analytics_dashboard(request):
    if not _analytics_allowed(request.user):
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('dashboard')

    try:
        days = int(request.GET.get('range', 14))
    except (TypeError, ValueError):
        days = 14
    if days not in (7, 14, 30):
        days = 14

    series = _analytics_series(days)
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)

    current = _period_totals(start, end)
    previous = _period_totals(previous_start, previous_end)

    now = timezone.now()
    online = SessionTracker.objects.filter(last_activity__gte=now - timedelta(minutes=5)).count()

    kpis = [
        {
            'key': 'sessions',
            'label': 'Sessions',
            'value': current['sessions'],
            'delta': _delta(current['sessions'], previous['sessions']),
            'spark': _sparkline([row['sessions'] for row in series]),
            'icon': 'i-trend',
        },
        {
            'key': 'page_views',
            'label': 'Page views',
            'value': current['page_views'],
            'delta': _delta(current['page_views'], previous['page_views']),
            'spark': _sparkline([row['page_views'] for row in series]),
            'icon': 'i-chart',
        },
        {
            'key': 'users',
            'label': 'Active users',
            'value': current['users'],
            'delta': _delta(current['users'], previous['users']),
            'spark': _sparkline([row['users'] for row in series]),
            'icon': 'i-users',
        },
        {
            'key': 'devices',
            'label': 'Devices',
            'value': current['devices'],
            'delta': _delta(current['devices'], previous['devices']),
            'spark': _sparkline([row['devices'] for row in series]),
            'icon': 'i-device',
        },
    ]

    top_pages = []
    top_page_rows = (
        PageView.objects
        .filter(viewed_at__date__gte=start, viewed_at__date__lte=end)
        .values('page_url')
        .annotate(views=Count('id'), sessions=Count('session', distinct=True))
        .order_by('-views')[:6]
    )
    peak_views = top_page_rows[0]['views'] if top_page_rows else 0
    for row in top_page_rows:
        top_pages.append({
            'label': _page_label(row['page_url']),
            'path': row['page_url'],
            'views': row['views'],
            'sessions': row['sessions'],
            'share': round(row['views'] / peak_views * 100) if peak_views else 0,
        })

    device_mix = []
    device_rows = (
        DeviceTracker.objects
        .filter(last_seen__date__gte=start, last_seen__date__lte=end)
        .values('device_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    device_total = sum(row['total'] for row in device_rows)
    for row in device_rows:
        device_mix.append({
            'label': (row['device_type'] or 'Unknown'),
            'total': row['total'],
            'share': round(row['total'] / device_total * 100) if device_total else 0,
        })

    active_staff = []
    staff_rows = (
        SessionTracker.objects
        .filter(started_at__date__gte=start, started_at__date__lte=end, user__isnull=False)
        .values('user__username', 'user__first_name', 'user__last_name')
        .annotate(sessions=Count('id'), views=Sum('pages_visited'))
        .order_by('-sessions')[:5]
    )
    for row in staff_rows:
        full_name = f"{row['user__first_name']} {row['user__last_name']}".strip()
        active_staff.append({
            'name': full_name or row['user__username'],
            'username': row['user__username'],
            'sessions': row['sessions'],
            'views': row['views'] or 0,
        })

    daily = []
    for row in reversed(series):
        daily.append({
            'date': row['date'],
            'sessions': row['sessions'],
            'page_views': row['page_views'],
            'active_users': row['users'],
            'unique_devices': row['devices'],
            'views_per_session': round(row['page_views'] / row['sessions'], 1) if row['sessions'] else 0,
        })

    chart_series = [
        {
            'date': row['label'],
            'sessions': row['sessions'],
            'page_views': row['page_views'],
            'devices': row['devices'],
        }
        for row in series
    ]

    period_delta_sessions = _delta(current['sessions'], previous['sessions'])

    return render(request, 'analytics.html', {
        'stats': AnalyticsService.get_live_stats(),
        'chart_data': chart_series,
        'kpis': kpis,
        'top_pages': top_pages,
        'device_mix': device_mix,
        'active_staff': active_staff,
        'daily': daily,
        'range_days': days,
        'range_options': (7, 14, 30),
        'online_now': online,
        'total_periods': current,
        'previous_periods': previous,
        'period_delta_sessions': period_delta_sessions,
        'range_start': start,
        'range_end': end,
    })


@login_required
def analytics_export_csv(request):
    """Download the analytics daily breakdown as CSV."""
    if not _analytics_allowed(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    try:
        days = int(request.GET.get('range', 14))
    except (TypeError, ValueError):
        days = 14
    if days not in (7, 14, 30):
        days = 14

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics-{days}-days.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Sessions', 'Page views', 'Active users', 'Devices', 'Views per session'])
    for row in reversed(_analytics_series(days)):
        writer.writerow([
            row['date'].isoformat(),
            row['sessions'],
            row['page_views'],
            row['users'],
            row['devices'],
            round(row['page_views'] / row['sessions'], 1) if row['sessions'] else 0,
        ])
    return response


@login_required
def analytics_live_stats(request):
    if not _analytics_allowed(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    return JsonResponse({'success': True, 'stats': AnalyticsService.get_live_stats()})


@login_required
def analytics_chart_data(request):
    if not _analytics_allowed(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    days = int(request.GET.get('days', 14) or 14)
    return JsonResponse({'success': True, 'data': AnalyticsService.get_chart_data(days=days)})


@login_required
def analytics_notifications(request):
    if not _analytics_allowed(request.user):
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('dashboard')
    from .models import UsageMilestone
    milestones = UsageMilestone.objects.all()[:50]
    return render(request, 'analytics_notifications.html', {
        'milestones': milestones,
        'milestone_count': UsageMilestone.objects.count(),
        'latest_milestone': milestones[0] if milestones else None,
    })


@login_required
def analytics_devices(request):
    if not _analytics_allowed(request.user):
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('dashboard')

    device_type = request.GET.get('type', '').strip()
    devices = DeviceTracker.objects.all().select_related('user').order_by('-last_seen')
    if device_type:
        devices = devices.filter(device_type__iexact=device_type)

    type_rows = (
        DeviceTracker.objects.values('device_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    device_types = [
        {'label': row['device_type'] or 'Unknown', 'total': row['total']}
        for row in type_rows
    ]
    week_ago = timezone.now() - timedelta(days=7)
    summary = {
        'total': DeviceTracker.objects.count(),
        'active': DeviceTracker.objects.filter(is_active=True).count(),
        'week': DeviceTracker.objects.filter(last_seen__gte=week_ago).count(),
        'sessions': SessionTracker.objects.count(),
    }

    return render(request, 'analytics_devices.html', {
        'devices': devices[:200],
        'device_types': device_types,
        'selected_type': device_type,
        'summary': summary,
    })


@login_required
def generate_daily_report(request):
    if not _analytics_allowed(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    date = AnalyticsService.generate_daily_stats()
    return JsonResponse({
        'success': True,
        'report': {
            'date': date.date.isoformat(),
            'unique_devices': date.unique_devices,
            'total_sessions': date.total_sessions,
            'active_users': date.active_users,
            'total_page_views': date.total_page_views,
            'total_actions': date.total_actions,
            'most_visited_page': date.most_visited_page,
        },
    })
