"""Remove only the pristine seed-only workspace left on fresh installations."""
from django.db import migrations


SEED_TYPES = {
    'FEET': 'Feets',
    'VHB18': 'VHB Boss Tape 18mm',
    'VHB12': 'VHB Boss Tape 12mm',
    'VHB7': 'VHB Boss Tape 7mm',
    'PISTRIP': 'PI Strips',
    'RIV8': 'Rivnuts 8mm',
    'RIV6': 'Rivnuts 6mm',
    'RIV5': 'Rivnuts 5mm',
    'RIV4': 'Rivnuts 4mm',
}


def remove_pristine_seed_workspace(apps, schema_editor):
    Workspace = apps.get_model('stockT', 'Workspace')
    WorkspaceMember = apps.get_model('stockT', 'WorkspaceMember')
    KitType = apps.get_model('stockT', 'KitType')
    Kit = apps.get_model('stockT', 'Kit')
    StockUsage = apps.get_model('stockT', 'StockUsage')
    SessionTracker = apps.get_model('stockT', 'SessionTracker')

    workspace = Workspace.objects.filter(
        name='Main Workspace',
        created_by__isnull=True,
        memberships__isnull=True,
    ).first()
    if workspace is None:
        return
    if Kit.objects.filter(workspace_id=workspace.pk).exists():
        return
    if StockUsage.objects.filter(workspace_id=workspace.pk).exists():
        return
    if SessionTracker.objects.filter(workspace_id=workspace.pk).exists():
        return
    if WorkspaceMember.objects.filter(workspace_id=workspace.pk).exists():
        return

    kit_types = KitType.objects.filter(workspace_id=workspace.pk)
    if kit_types.count() != len(SEED_TYPES):
        return
    if dict(kit_types.values_list('code', 'name')) != SEED_TYPES:
        return

    workspace.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('stockT', '0006_inventory_inventoryproduct'),
    ]

    operations = [
        migrations.RunPython(remove_pristine_seed_workspace, migrations.RunPython.noop),
    ]
