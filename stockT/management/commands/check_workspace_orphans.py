"""Fail when tenant-owned records have no workspace assigned."""
from django.core.management.base import BaseCommand, CommandError

from stockT.models import Kit, KitType, StockUsage


class Command(BaseCommand):
    help = 'Check for stock data with NULL workspace ownership.'

    def handle(self, *args, **options):
        models = (KitType, Kit, StockUsage)
        orphan_counts = {
            model._meta.label: model.objects.filter(workspace__isnull=True).count()
            for model in models
        }
        total = sum(orphan_counts.values())
        if total:
            details = ', '.join(
                f'{label}: {count}'
                for label, count in orphan_counts.items()
                if count
            )
            raise CommandError(
                f'Found {total} tenant-owned row(s) with no workspace ({details}). '
                'These rows are excluded from tenant views. Assign them to the '
                'correct workspace before continuing.'
            )
        self.stdout.write(self.style.SUCCESS('Workspace ownership check passed.'))
