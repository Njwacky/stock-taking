"""
Backfill workspaces for existing (pre-workspace) installs.

Every legacy row (kit types, kits, stock usage) belongs to one shared
"Main Workspace", and every existing user becomes a member of it (the first
admin-capable account is the Owner). Fresh installs with no data skip this.
"""
from django.db import migrations
from django.utils.text import slugify


def _unique_slug(Model, name):
    base = slugify(name)[:100] or 'workspace'
    slug = base
    n = 2
    while Model.objects.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


def backfill(apps, schema_editor):
    User = apps.get_model('stockT', 'User')
    Workspace = apps.get_model('stockT', 'Workspace')
    WorkspaceMember = apps.get_model('stockT', 'WorkspaceMember')
    KitType = apps.get_model('stockT', 'KitType')
    Kit = apps.get_model('stockT', 'Kit')
    StockUsage = apps.get_model('stockT', 'StockUsage')

    users_exist = User.objects.exists()
    data_exists = (
        KitType.objects.filter(workspace__isnull=True).exists()
        or Kit.objects.filter(workspace__isnull=True).exists()
        or StockUsage.objects.filter(workspace__isnull=True).exists()
    )
    if not users_exist and not data_exists:
        return  # nothing to migrate

    owner = (
        User.objects.filter(is_superuser=True).order_by('id').first()
        or User.objects.filter(role='admin').order_by('id').first()
        or User.objects.order_by('id').first()
    )

    workspace = Workspace.objects.create(
        name='Main Workspace',
        slug=_unique_slug(Workspace, 'Main Workspace'),
        created_by=owner,
    )

    KitType.objects.filter(workspace__isnull=True).update(workspace=workspace)
    Kit.objects.filter(workspace__isnull=True).update(workspace=workspace)
    StockUsage.objects.filter(workspace__isnull=True).update(workspace=workspace)

    for user in User.objects.all().order_by('id'):
        WorkspaceMember.objects.get_or_create(
            workspace=workspace, user=user,
            defaults={
                'role': 'owner' if owner and user.id == owner.id else 'member',
            },
        )


def unbackfill(apps, schema_editor):
    # Keep the data; only remove the synthetic workspace wiring.
    apps.get_model('stockT', 'Workspace').objects.filter(name='Main Workspace').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stockT', '0003_workspacemember_alter_kittype_code_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
