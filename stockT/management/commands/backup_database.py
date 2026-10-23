"""Create an online-consistent database backup."""
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from stockT.management.backup import backup_sqlite, postgres_environment


class Command(BaseCommand):
    help = 'Back up the configured SQLite or PostgreSQL database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            help='Destination path. Defaults to backups/stock-<timestamp>.<ext>.',
        )

    def handle(self, *args, **options):
        connection = connections['default']
        database = connection.settings_dict
        output = options['output']
        if output:
            destination = Path(output).expanduser()
            if not destination.is_absolute():
                destination = Path(settings.BASE_DIR) / destination
        else:
            extension = 'sqlite3' if connection.vendor == 'sqlite' else 'dump'
            timestamp = datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
            destination = Path(settings.BASE_DIR) / 'backups' / f'stock-{timestamp}.{extension}'
        destination = destination.resolve()

        if connection.vendor == 'sqlite':
            source = backup_sqlite(database['NAME'], destination)
        elif connection.vendor == 'postgresql':
            source = self._backup_postgres(database, destination)
        else:
            raise CommandError(
                f'Backups are not implemented for database vendor "{connection.vendor}".'
            )
        self.stdout.write(self.style.SUCCESS(f'Backup created: {source}'))

    def _backup_postgres(self, database, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=f'.{destination.name}.', suffix='.tmp', dir=destination.parent,
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
            env, database_name = postgres_environment(database)
            subprocess.run(
                [
                    'pg_dump', '--no-password', '--format=custom', '--no-owner',
                    '--no-privileges', '--file', str(temporary), '--dbname', database_name,
                ],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            if temporary.stat().st_size == 0:
                raise CommandError('pg_dump produced an empty backup file.')
            temporary.replace(destination)
            return destination
        except FileNotFoundError as exc:
            raise CommandError('pg_dump is required for PostgreSQL backups.') from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or exc.stdout or str(exc)).strip()
            raise CommandError(f'pg_dump failed: {message}') from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
