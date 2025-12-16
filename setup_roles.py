"""
Script to create default user roles/groups for the stocktaking app.
Run this with: python manage.py shell < setup_roles.py
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from stockT.models import Kit, User

# Create groups
admin_group, _ = Group.objects.get_or_create(name='Admin')
manager_group, _ = Group.objects.get_or_create(name='Manager')
staff_group, _ = Group.objects.get_or_create(name='Staff')

# Get permissions
kit_ct = ContentType.objects.get_for_model(Kit)
user_ct = ContentType.objects.get_for_model(User)

# Admin: all permissions
admin_perms = Permission.objects.filter(content_type__in=[kit_ct, user_ct])
admin_group.permissions.set(admin_perms)

# Manager: can add/change/view kits, view users
manager_perms = Permission.objects.filter(
    content_type=kit_ct,
    codename__in=['add_kit', 'change_kit', 'view_kit']
)
manager_perms |= Permission.objects.filter(
    content_type=user_ct,
    codename__in=['view_user']
)
manager_group.permissions.set(manager_perms)

# Staff: can view kits only
staff_perms = Permission.objects.filter(
    content_type=kit_ct,
    codename__in=['view_kit']
)
staff_group.permissions.set(staff_perms)

print('Groups and permissions set up! Assign users to groups via Django admin or shell.')
