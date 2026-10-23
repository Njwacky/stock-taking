# Production operations: security and database recovery

This guide complements `DOCKER_LOCAL_SETUP.md`. The checked-in Compose file is
for local use; it is not a production deployment. Production must use a
maintained PostgreSQL service, a private application network, HTTPS, and a
secrets manager or protected environment variables.

## Before exposing the app

- Set `DEBUG=False`, a generated `SECRET_KEY` (never the development fallback),
  explicit `ALLOWED_HOSTS`, and the production `DATABASE_URL`.
- Terminate TLS at a trusted reverse proxy and configure its forwarded-proto
  header. Keep the Django/Gunicorn port private.
- Keep the database and backup storage private. Give backup jobs only the
  database credentials and storage permissions they need.
- Use a distinct PostgreSQL database for each environment. Apply migrations
  during a controlled release, not concurrently from multiple web instances.
- Review user access and workspace membership after importing legacy data. Run
  `python manage.py check_workspace_orphans` after migrations/imports; it fails
  if stock data has no explicit workspace owner.

## Create a database backup

The management command supports the configured SQLite and PostgreSQL database.
SQLite uses SQLite's online backup API (so committed WAL data is included).
PostgreSQL uses `pg_dump` custom format. PostgreSQL images need `pg_dump` and
`pg_restore`; the project Docker image installs `postgresql-client`.

```sh
# Writes a timestamped file under ./backups by default.
python manage.py backup_database

# Prefer a mounted, encrypted backup volume or a remote backup destination.
python manage.py backup_database --output /mnt/stock-backups/stock-$(date +%F-%H%M%S).dump
```

The command writes to a temporary file first and only publishes a completed
backup. Keep backups outside the application container and repository, encrypt
them at rest and in transit, restrict access, and apply a retention policy.
Back up uploaded media separately if media storage is enabled.

## Restore and test recovery

A restore replaces data in the database configured by `DATABASE_URL`. Stop all
web and background-worker processes first. Back up the current database before
restoring, and verify the chosen backup and target environment carefully.

```sh
# PostgreSQL: configure DATABASE_URL for the intended target database.
python manage.py backup_database --output /mnt/stock-backups/pre-restore.dump
python manage.py restore_database /mnt/stock-backups/stock-2026-10-21.dump --confirm

# SQLite: same command; restore replaces the configured SQLite file.
python manage.py restore_database /mnt/stock-backups/stock-2026-10-21.sqlite3 --confirm
```

The restore command refuses to run without `--confirm`. PostgreSQL restore
uses `pg_restore` with error-stop and single-transaction options. SQLite restore
checks database integrity and atomically replaces the database file. For
PostgreSQL, restoring to a fresh database is preferred for recovery drills;
when restoring over an existing database, the application must remain stopped.

Perform a recovery drill at least quarterly and after material database or
infrastructure changes:

1. Restore a recent backup to an isolated database and storage location.
2. Start the application against that isolated copy.
3. Verify login, workspace membership, inventory totals, stock usage history,
   exports, and any uploaded media.
4. Record the restore duration and any data-loss window, then delete the drill
   environment securely.

A successful backup job is not proof of recoverability. Monitor backup age,
size, exit status, and restore-drill results; alert when the last verified
backup is older than the agreed recovery point objective.

## Sign-in protection

The application records failed logins with django-axes and temporarily locks
a username/IP pair after five unsuccessful attempts for 15 minutes. A
successful login clears prior failures. Lockouts return HTTP 429 with a
recovery link. IP detection uses `REMOTE_ADDR` unless
`TRUST_X_FORWARDED_FOR=True`; in that trusted-proxy mode, the app uses
`X-Real-IP`. Only enable that setting behind a proxy that overwrites this
header (the checked-in Nginx configuration does). Keep the app port private.

To inspect or clear an account lockout, use the django-axes management
commands, for example `python manage.py axes_list_attempts` and
`python manage.py axes_reset_username <username>`. Schedule a daily review or
cleanup consistent with your security and privacy policy; Axes attempt records
contain account and network identifiers.

The application enforces a 12-character password minimum, in addition to
Django's similarity, common-password, and numeric-password checks. Keep
administrator accounts unique, revoke accounts promptly when people leave,
and never send passwords in plain email or chat. A managed identity provider
and MFA are recommended for production administrators.
