"""Seed the standard kit types (docs/REQUIREMENTS.md) so a fresh install can add
stock immediately — previously KitType rows could only be created through the
Django admin, leaving every stock dropdown empty.

Idempotent: get_or_create never overwrites edits an admin has made.
"""
from django.db import migrations

SEED = [
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


def seed_kit_types(apps, schema_editor):
    KitType = apps.get_model('stockT', 'KitType')
    for name, code, description, unit in SEED:
        KitType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'unit_of_measure': unit,
                'is_active': True,
            },
        )


def unseed_kit_types(apps, schema_editor):
    KitType = apps.get_model('stockT', 'KitType')
    KitType.objects.filter(code__in=[code for _, code, _, _ in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stockT', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_kit_types, unseed_kit_types),
    ]
