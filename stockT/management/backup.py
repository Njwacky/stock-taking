"""Database backup helpers used by the backup/restore management commands."""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
import tempfile
from pathlib import Path
from urllib.parse import quote

from django.core.management.base import CommandError


_PG_OPTION_ENV = {
    'sslmode': 'PGSSLMODE',
    'sslrootcert': 'PGSSLROOTCERT',
    'sslcert': 'PGSSLCERT',
    'sslkey': 'PGSSLKEY',
    'application_name': 'PGAPPNAME',
    'connect_timeout': 'PGCONNECT_TIMEOUT',
    'gssencmode': 'PGGSSENCMODE',
}


def _temporary_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(
        prefix=f'.{destination.name}.', suffix='.tmp', dir=destination.parent,
    )
    os.close(fd)
    return Path(name)


def _sqlite_path(name) -> Path:
    if str(name) == ':memory:' or str(name).startswith('file:'):
        raise CommandError('SQLite backup/restore requires a file-based database.')
    return Path(name).expanduser().resolve()


def backup_sqlite(source_name, destination) -> Path:
    """Create a consistent SQLite snapshot, including committed WAL changes."""
    source_path = _sqlite_path(source_name)
    if not source_path.is_file():
        raise CommandError(f'SQLite database does not exist: {source_path}')
    destination_path = Path(destination).expanduser().resolve()
    if source_path == destination_path:
        raise CommandError('Backup output must not be the live SQLite database file.')

    temporary = _temporary_path(destination_path)
    try:
        source_uri = f'file:{quote(str(source_path))}?mode=ro'
        with closing(sqlite3.connect(source_uri, uri=True, timeout=30)) as source:
            with closing(sqlite3.connect(temporary, timeout=30)) as target:
                source.backup(target)
                target.commit()
                result = target.execute('PRAGMA integrity_check').fetchone()[0]
                if result != 'ok':
                    raise CommandError(f'SQLite backup integrity check failed: {result}')
        os.replace(temporary, destination_path)
    finally:
        temporary.unlink(missing_ok=True)
    return destination_path


def restore_sqlite(backup_path, target_name) -> Path:
    """Atomically replace a file-based SQLite database from a verified backup."""
    source_path = Path(backup_path).expanduser().resolve()
    target_path = _sqlite_path(target_name)
    if source_path == target_path:
        raise CommandError('Restore source must not be the live SQLite database file.')
    if not source_path.is_file():
        raise CommandError(f'Backup file does not exist: {source_path}')

    temporary = _temporary_path(target_path)
    try:
        source_uri = f'file:{quote(str(source_path))}?mode=ro'
        with closing(sqlite3.connect(source_uri, uri=True, timeout=30)) as source:
            integrity = source.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity != 'ok':
                raise CommandError(f'Backup integrity check failed: {integrity}')
            with closing(sqlite3.connect(temporary, timeout=30)) as target:
                source.backup(target)
                target.commit()
        os.replace(temporary, target_path)
    finally:
        temporary.unlink(missing_ok=True)
    return target_path


def postgres_environment(database_settings) -> tuple[dict[str, str], str]:
    """Build libpq environment variables without putting credentials in argv."""
    env = os.environ.copy()
    env['PGDATABASE'] = str(database_settings.get('NAME') or 'postgres')
    for key, variable in (
        ('HOST', 'PGHOST'), ('PORT', 'PGPORT'), ('USER', 'PGUSER'),
        ('PASSWORD', 'PGPASSWORD'),
    ):
        value = database_settings.get(key)
        if value not in (None, ''):
            env[variable] = str(value)
    for key, variable in _PG_OPTION_ENV.items():
        value = database_settings.get('OPTIONS', {}).get(key)
        if value not in (None, ''):
            env[variable] = str(value)
    return env, env['PGDATABASE']
