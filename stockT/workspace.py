"""
Multi-workspace helpers for the stockT application.

This app uses the standard multi-tenant workspace pattern (the same one
Notion / Slack / GitHub use):

* Everyone can register — registration is always open.
* On registration each user gets their own personal workspace and becomes
  its Owner ("your own apps").
* Users can create additional workspaces and switch between them.
* Workspace owners/admins can add other registered users as members.
* All stock data (kit types, kits, stock usage) is scoped to a workspace.

Helpers here are the single source of truth for "which workspace is active"
and "who may manage what" — views must go through them rather than querying
Workspace/WorkspaceMember directly.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from .models import Workspace, WorkspaceMember

# Standard kit types seeded into every NEW workspace so the stock dropdowns
# are never empty (same list as migration 0002_seed_kit_types).
DEFAULT_KIT_TYPES = [
    # (name, code, description, unit)
    ('Feets', 'FEET', 'Feets', 'pieces'),
    ('VHB Boss Tape 18mm', 'VHB18', 'VHB Boss Tape 18mm', 'rolls'),
    ('VHB Boss Tape 12mm', 'VHB12', 'VHB Boss Tape 12mm', 'rolls'),
    ('VHB Boss Tape 7mm', 'VHB7', 'VHB Boss Tape 7mm', 'rolls'),
    ('PI Strips', 'PISTRIP', 'PI Strips', 'pieces'),
    ('Rivnuts 8mm', 'RIV8', 'Rivnuts 8mm', 'pieces'),
    ('Rivnuts 6mm', 'RIV6', 'Rivnuts 6mm', 'pieces'),
    ('Rivnuts 5mm', 'RIV5', 'Rivnuts 5mm', 'pieces'),
    ('Rivnuts 4mm', 'RIV4', 'Rivnuts 4mm', 'pieces'),
]


def registration_open():
    """Public registration is always open: everyone can sign up and will
    receive their own workspace."""
    return True


def default_kit_type_codes():
    return [code for _, code, _, _ in DEFAULT_KIT_TYPES]


def seed_kit_types(workspace, created_by=None):
    """Give a workspace the standard kit types so stock can be added at once.

    Idempotent: never overwrites edits an admin has made.
    """
    from .models import KitType

    for name, code, description, unit in DEFAULT_KIT_TYPES:
        KitType.objects.get_or_create(
            workspace=workspace, code=code,
            defaults={
                'name': name,
                'description': description,
                'unit_of_measure': unit,
                'is_active': True,
                'created_by': created_by,
            },
        )


@transaction.atomic
def create_workspace(name, owner, role=WorkspaceMember.ROLE_OWNER, seed=True):
    """Create a workspace, add its owner, and seed starter kit types."""
    workspace = Workspace.objects.create(name=name, created_by=owner)
    WorkspaceMember.objects.create(
        workspace=workspace, user=owner,
        role=WorkspaceMember.ROLE_OWNER if role == WorkspaceMember.ROLE_OWNER else role,
    )
    if seed:
        seed_kit_types(workspace, created_by=owner)
    return workspace


def ensure_user_workspace(user):
    """Return the user's first workspace, creating a personal one if needed.

    This is the "your own apps" provisioning step: every registered user
    owns at least one workspace.
    """
    membership = user.workspace_memberships.select_related('workspace').order_by('joined_at', 'id').first()
    if membership:
        return membership.workspace
    name = f'{user.first_name or user.username}’s Workspace'
    return create_workspace(name, user)


def user_workspaces(user):
    """All workspaces the user belongs to (via memberships)."""
    return Workspace.objects.filter(
        is_active=True, memberships__user=user,
    ).distinct().order_by('memberships__joined_at', 'id')


def get_membership(user, workspace):
    if not user or not user.is_authenticated or workspace is None:
        return None
    return WorkspaceMember.objects.filter(workspace=workspace, user=user).first()


def is_workspace_manager(user, workspace):
    """True when the user may manage this workspace's data (owner/admin
    membership, or a global manager/admin)."""
    if not user or not user.is_authenticated or workspace is None:
        return False
    if user.is_manager:
        return True
    membership = get_membership(user, workspace)
    return membership is not None and membership.is_manager


def workspace_member_users(workspace):
    """Active users who belong to the workspace (for people pickers)."""
    User = get_user_model()
    return User.objects.filter(
        is_active=True, workspace_memberships__workspace=workspace,
    ).distinct().order_by('username')


def set_current_workspace(request, workspace):
    request.session['workspace_id'] = workspace.id if workspace else None


def current_workspace(request):
    """The workspace the request is acting in.

    Resolution order (standard tenant-context pattern):
    1. the workspace chosen in the session (validated against membership),
    2. the user's first membership,
    3. auto-provision a personal workspace (keeps a fresh superuser or a
       legacy account from ever landing in a dead end).
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return None

    ws_id = request.session.get('workspace_id')
    if ws_id:
        workspace = Workspace.objects.filter(
            id=ws_id, is_active=True, memberships__user=user,
        ).first()
        if workspace:
            return workspace
        # stale or foreign workspace in session -> drop it
        request.session.pop('workspace_id', None)

    workspace = ensure_user_workspace(user)
    set_current_workspace(request, workspace)
    return workspace
