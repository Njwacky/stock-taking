"""
Views for the stockT application.

Reconstructed from the project's documentation, test scripts and client-side
JavaScript contracts (static/js/*.js).
"""
import json

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .analytics_service import AnalyticsService
from .forms import (
    ContactInfoForm,
    EditUserForm,
    ProfileForm,
    RegisterForm,
    StockUsageForm,
    UserCommentForm,
)
from .models import (
    ContactInfo,
    DeviceTracker,
    Kit,
    KitType,
    NotificationLog,
    PasswordResetRequest,
    StockUsage,
    User,
    UserComment,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_manager(user):
    return user.is_authenticated and user.is_manager


def _kit_stats():
    """Aggregated kit statistics used by the dashboard pie chart."""
    return list(
        Kit.objects.filter(is_active=True)
        .values('kit_type_fk__name')
        .annotate(
            kit_type=F('kit_type_fk__name'),
            total_quantity=Sum('quantity'),
            user_count=Count('user', distinct=True),
        )
        .order_by('-total_quantity')
    )


def _kits_queryset(request):
    if _is_manager(request.user):
        return Kit.objects.filter(is_active=True).select_related('user', 'kit_type_fk', 'created_by')
    return Kit.objects.filter(user=request.user, is_active=True).select_related('user', 'kit_type_fk', 'created_by')


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

def dashboard(request):
    """Main dashboard: kit table with filtering/sorting for staff, landing page otherwise."""
    if not request.user.is_authenticated:
        return render(request, 'dashboard.html', {'public_view': True})

    kits = _kits_queryset(request)

    user_filter = request.GET.get('user', '')
    search = request.GET.get('search', '').strip()
    sort = SORT_FIELDS.get(request.GET.get('sort', 'timestamp'), 'timestamp')
    order = 'asc' if request.GET.get('order', 'desc') == 'asc' else 'desc'
    page_number = request.GET.get('page', '1')

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

    if request.method == 'POST' and request.POST.get('action') == 'bulk_delete' and _is_manager(request.user):
        ids = request.POST.getlist('kit_ids')
        Kit.objects.filter(id__in=ids, is_active=True).delete()
        messages.success(request, f'{len(ids)} kit(s) deleted.')
        return redirect('dashboard')

    paginator = Paginator(kits, 15)
    page_obj = paginator.get_page(page_number)

    context = {
        'public_view': False,
        'kits': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'kit_stats': _kit_stats(),
        'users': User.objects.filter(is_active=True).order_by('username') if _is_manager(request.user) else [],
        'filters': {'user': user_filter, 'search': search, 'sort': request.GET.get('sort', 'timestamp'), 'order': request.GET.get('order', 'desc')},
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'table_html': render_to_string('partials/kit_table.html', context, request),
            'pagination_html': render_to_string('partials/pagination.html', context, request),
            'kit_stats': _kit_stats(),
        })

    return render(request, 'dashboard.html', context)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect('workspace_list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Your account has been created.')
        return redirect('workspace_list')
    return render(request, 'register.html', {'form': form})


def logout_confirm(request):
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


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def offline(request):
    return render(request, 'offline.html')


def service_worker(request):
    from django.http import FileResponse
    from django.conf import settings
    import os
    path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    response = FileResponse(open(path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def manifest(request):
    from django.http import FileResponse
    from django.conf import settings
    import os
    path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    return FileResponse(open(path, 'rb'), content_type='application/manifest+json')


# ---------------------------------------------------------------------------
# Add stock items
# ---------------------------------------------------------------------------

@login_required
def add_items(request):
    """Add stock items for yourself (or another user when permitted)."""
    kit_types = KitType.objects.filter(is_active=True).order_by('name')
    can_select_user = _is_manager(request.user)
    target_users = User.objects.filter(is_active=True).order_by('username') if can_select_user else [request.user]

    if request.method == 'POST':
        target_id = request.POST.get('user', str(request.user.id))
        target = get_object_or_404(User, id=target_id)
        if not can_select_user and target.id != request.user.id:
            messages.error(request, 'You can only add stock for yourself.')
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
    if not _is_manager(request.user) and request.user.id != user_id:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    user = get_object_or_404(User, id=user_id)
    kits = Kit.objects.filter(user=user, is_active=True).select_related('kit_type_fk')
    return JsonResponse({'success': True, 'kits': [_kit_to_dict(k) for k in kits]})


@login_required
def get_kit_types_for_edit(request):
    types = KitType.objects.filter(is_active=True).order_by('name')
    return JsonResponse({
        'success': True,
        'kit_types': [{'id': t.id, 'name': t.name, 'code': t.code} for t in types],
    })


@login_required
@require_POST
def update_kit(request, kit_id):
    kit = get_object_or_404(Kit, id=kit_id, is_active=True)
    if not _is_manager(request.user) and kit.user_id != request.user.id:
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
        kit_type = KitType.objects.filter(id=request.POST.get('kit_type')).first()
        if kit_type:
            kit.kit_type_fk = kit_type
            kit.kit_type_string = kit_type.name[:20]
        else:
            errors['kit_type'] = 'Unknown kit type.'

    for field in ('condition', 'location', 'notes'):
        if field in request.POST:
            setattr(kit, field, request.POST.get(field) or None)
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
    kit = get_object_or_404(Kit, id=kit_id, is_active=True)
    if not _is_manager(request.user) and kit.user_id != request.user.id:
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
def edit_user(request, user_id):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('dashboard')
    target = get_object_or_404(User, id=user_id)

    # Only admins can change roles or staff status.
    if not request.user.is_admin:
        restricted = EditUserForm(request.POST or None, instance=target)
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
    kit_types = KitType.objects.filter(is_active=True).order_by('name')
    recent = StockUsage.objects.filter(user=request.user)[:8]
    form = StockUsageForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            usage = form.save(commit=False)
            usage.user = request.user
            usage.clock_number = request.user.clock_number or ''
            usage.kit_type_name = usage.kit_type.name if usage.kit_type else ''
            usage.status = StockUsage.STATUS_PENDING
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
    status_filter = request.GET.get('status', '')
    if _is_manager(request.user):
        usages = StockUsage.objects.all().select_related('user', 'kit_type', 'reviewed_by')
    else:
        usages = StockUsage.objects.filter(user=request.user).select_related('user', 'kit_type', 'reviewed_by')
    if status_filter:
        usages = usages.filter(status=status_filter)
    return render(request, 'stock_usage_history.html', {
        'usages': usages,
        'status_filter': status_filter,
    })


@login_required
@require_POST
def review_stock_usage(request, usage_id):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to review usage requests.')
        return redirect('stock_usage_history')
    usage = get_object_or_404(StockUsage, id=usage_id)
    action = request.POST.get('action')
    usage.admin_notes = request.POST.get('admin_notes', '') or None
    usage.reviewed_by = request.user
    usage.reviewed_at = timezone.now()
    if action == 'approve':
        usage.status = StockUsage.STATUS_APPROVED
        usage.save()
        messages.success(request, 'Usage approved and stock updated.')
    elif action == 'reject':
        usage.status = StockUsage.STATUS_REJECTED
        usage.save()
        messages.success(request, 'Usage request rejected.')
    else:
        messages.error(request, 'Unknown action.')
    return redirect(request.POST.get('next') or 'stock_usage_history')


@login_required
@require_POST
def delete_stock_usage(request, usage_id):
    if not _is_manager(request.user):
        messages.error(request, 'You do not have permission to delete usage records.')
        return redirect('stock_usage_history')
    usage = get_object_or_404(StockUsage, id=usage_id)
    usage.delete()
    messages.success(request, 'Usage record deleted.')
    return redirect('stock_usage_history')


# ---------------------------------------------------------------------------
# Stock distribution
# ---------------------------------------------------------------------------

@login_required
def stock_distribution(request):
    """Distribute stock to users, verified with the distributor's password.

    Access is limited to managers and supervisors (the "Manager & Supervisor
    Stock Assignment Portal"); admins and regular users are redirected.
    """
    if request.user.role not in (User.ROLE_MANAGER, User.ROLE_SUPERVISOR):
        messages.error(request, 'Access denied. This portal is for managers and supervisors only.')
        return redirect('dashboard')

    kit_types = KitType.objects.filter(is_active=True).order_by('name')
    recipients = User.objects.filter(
        is_active=True, is_superuser=False,
    ).exclude(role=User.ROLE_ADMIN).order_by('username')
    recent_distributions = (
        Kit.objects.filter(created_by__isnull=False)
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
    stats = _kit_stats()
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
    target.role = User.ROLE_USER
    target.is_staff = False
    target.save(update_fields=['role', 'is_staff'])
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


@login_required
def analytics_dashboard(request):
    if not _analytics_allowed(request.user):
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('dashboard')
    stats = AnalyticsService.get_live_stats()
    chart_data = AnalyticsService.get_chart_data()
    from .models import DailyStats
    daily = DailyStats.objects.all()[:14]
    return render(request, 'analytics.html', {
        'stats': stats,
        'chart_data': chart_data,
        'daily': daily,
    })


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
    return render(request, 'analytics_notifications.html', {'milestones': milestones})


@login_required
def analytics_devices(request):
    if not _analytics_allowed(request.user):
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('dashboard')
    devices = DeviceTracker.objects.all().select_related('user')[:200]
    return render(request, 'analytics_devices.html', {'devices': devices})


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
