"""Restore a database from a backup (destructive; requires explicit opt-in)."""
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from stockT.management.backup import postgres_environment, restore_sqlite


class Command(BaseCommand):
    help = 'Restore the configured database from a backup. This replaces live data.'

    def add_arguments(self, parser):
        parser.add_argument('backup', help='Path to a backup created by backup_database.')
        parser.add_argument(
            '--confirm', action='store_true',
            help='Required acknowledgement that the configured database will be replaced.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError(
                'Restore is destructive. Stop the application, take a current backup, '
                'then rerun with --confirm.'
            )

        connection = connections['default']
        database = connection.settings_dict
        backup = options['backup']
        if connection.vendor == 'sqlite':
            connections.close_all()
            restored = restore_sqlite(backup, database['NAME'])
        elif connection.vendor == 'postgresql':
            restored = self._restore_postgres(database, backup)
        else:
            raise CommandError(
                f'Restore is not implemented for database vendor "{connection.vendor}".'
            )
        self.stdout.write(self.style.SUCCESS(f'Database restored from: {restored}'))

    def _restore_postgres(self, database, backup):
        from pathlib import Path

        source = Path(backup).expanduser().resolve()
        if not source.is_file():
            raise CommandError(f'Backup file does not exist: {source}')
        env, database_name = postgres_environment(database)
        try:
            subprocess.run(
                ['pg_restore', '--list', str(source)],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    'pg_restore', '--no-password', '--clean', '--if-exists',
                    '--no-owner', '--no-privileges', '--exit-on-error',
                    '--single-transaction', '--dbname', database_name, str(source),
                ],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise CommandError('pg_restore is required for PostgreSQL restores.') from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or exc.stdout or str(exc)).strip()
            raise CommandError(f'pg_restore failed: {message}') from exc
        return source
