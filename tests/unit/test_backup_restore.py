"""Database backup helpers must produce verified, restorable SQLite snapshots."""
import sqlite3

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from stockT.management.backup import backup_sqlite, restore_sqlite


def test_sqlite_backup_and_restore_round_trip(tmp_path):
    source = tmp_path / 'source.sqlite3'
    backup = tmp_path / 'backups' / 'stock.sqlite3'
    restored = tmp_path / 'restored.sqlite3'

    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE inventory (code TEXT PRIMARY KEY, quantity INTEGER NOT NULL)')
        db.execute('INSERT INTO inventory VALUES (?, ?)', ('BOLT-8', 42))

    assert backup_sqlite(source, backup) == backup.resolve()
    with sqlite3.connect(backup) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT code, quantity FROM inventory').fetchone() == ('BOLT-8', 42)

    assert restore_sqlite(backup, restored) == restored.resolve()
    with sqlite3.connect(restored) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT code, quantity FROM inventory').fetchone() == ('BOLT-8', 42)


def test_sqlite_backup_refuses_to_overwrite_live_database(tmp_path):
    database = tmp_path / 'stock.sqlite3'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE marker (value TEXT)')

    with pytest.raises(CommandError, match='must not be the live'):
        backup_sqlite(database, database)


def test_restore_command_requires_explicit_confirmation():
    with pytest.raises(CommandError, match='Restore is destructive'):
        call_command('restore_database', '/tmp/nonexistent-stock-backup.sqlite3')


def test_sqlite_restore_refuses_to_use_live_database_as_backup(tmp_path):
    database = tmp_path / 'stock.sqlite3'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE marker (value TEXT)')

    with pytest.raises(CommandError, match='must not be the live'):
        restore_sqlite(database, database)
