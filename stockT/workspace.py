"""
Single-workspace helpers for the stockT application.

This app runs exactly ONE workspace. The first person to register becomes the
workspace Superadmin (the owner); public registration then closes forever and
the Superadmin adds everybody else from Manage Users -> Add User.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q


def workspace_has_owner():
    """True once the workspace has an admin-capable account."""
    User = get_user_model()
    return User.objects.filter(
        Q(is_superuser=True) | Q(is_staff=True) | Q(role=User.ROLE_ADMIN)
    ).exists()


def registration_open():
    """
    Public registration is only open while the workspace has no owner.

    - Fresh install: nobody registered yet -> the first registration creates
      the Superadmin.
    - Legacy installs: users may exist without any admin (created while
      registration was open to everyone) -> the next registration creates the
      Superadmin so the workspace can never end up ownerless and locked.
    """
    return not workspace_has_owner()
