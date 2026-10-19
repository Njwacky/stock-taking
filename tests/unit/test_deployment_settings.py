"""Deployment settings regression tests using isolated settings subprocesses."""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_ENV_VARS = (
    'DEBUG',
    'SECRET_KEY',
    'ALLOWED_HOSTS',
    'DATABASE_URL',
    'CSRF_TRUSTED_ORIGINS',
    'SECURE_SSL_REDIRECT',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_HSTS_SECONDS',
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'SECURE_HSTS_PRELOAD',
    'USE_X_FORWARDED_PROTO',
)


def run_settings(tmp_path, overrides, code):
    """Import project settings in a fresh process without reading a local .env."""
    env = os.environ.copy()
    for name in SETTINGS_ENV_VARS:
        env.pop(name, None)
    env.update(overrides)
    env['PYTHONPATH'] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_sqlite_database_url_resolves_relative_to_project(tmp_path):
    result = run_settings(
        tmp_path,
        {'DATABASE_URL': 'sqlite:///data/settings-test.sqlite3'},
        "import json, app_conf.settings as s; print(json.dumps(s.DATABASES['default']))",
    )

    assert result.returncode == 0, result.stderr
    database = json.loads(result.stdout)
    assert database['ENGINE'] == 'django.db.backends.sqlite3'
    assert database['NAME'] == str(PROJECT_ROOT / 'data' / 'settings-test.sqlite3')


def test_postgresql_database_url_parses_credentials_port_and_options(tmp_path):
    result = run_settings(
        tmp_path,
        {
            'DATABASE_URL': (
                'postgresql://app-user:p%40ssword@db.example.test:5433/stock_management'
                '?sslmode=require&connect_timeout=10'
            ),
        },
        "import json, app_conf.settings as s; print(json.dumps(s.DATABASES['default']))",
    )

    assert result.returncode == 0, result.stderr
    database = json.loads(result.stdout)
    assert database == {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stock_management',
        'USER': 'app-user',
        'PASSWORD': 'p@ssword',
        'HOST': 'db.example.test',
        'PORT': '5433',
        'OPTIONS': {'sslmode': 'require', 'connect_timeout': '10'},
    }


def test_production_defaults_enable_https_security(tmp_path):
    secret_key = secrets.token_urlsafe(50)
    result = run_settings(
        tmp_path,
        {
            'DEBUG': 'False',
            'SECRET_KEY': secret_key,
            'ALLOWED_HOSTS': 'stock.example.test,www.stock.example.test',
            'DATABASE_URL': 'sqlite:///data/settings-test.sqlite3',
            # Blank values should use mode-dependent defaults (e.g. Compose).
            'SECURE_SSL_REDIRECT': '',
            'SESSION_COOKIE_SECURE': '',
            'CSRF_COOKIE_SECURE': '',
            'SECURE_HSTS_SECONDS': '',
            'USE_X_FORWARDED_PROTO': '',
        },
        """
import json, app_conf.settings as s
print(json.dumps({
    'DEBUG': s.DEBUG,
    'ALLOWED_HOSTS': s.ALLOWED_HOSTS,
    'SECURE_SSL_REDIRECT': s.SECURE_SSL_REDIRECT,
    'SESSION_COOKIE_SECURE': s.SESSION_COOKIE_SECURE,
    'CSRF_COOKIE_SECURE': s.CSRF_COOKIE_SECURE,
    'SECURE_HSTS_SECONDS': s.SECURE_HSTS_SECONDS,
    'SECURE_PROXY_SSL_HEADER': s.SECURE_PROXY_SSL_HEADER,
}))
""",
    )

    assert result.returncode == 0, result.stderr
    settings = json.loads(result.stdout)
    assert settings == {
        'DEBUG': False,
        'ALLOWED_HOSTS': ['stock.example.test', 'www.stock.example.test'],
        'SECURE_SSL_REDIRECT': True,
        'SESSION_COOKIE_SECURE': True,
        'CSRF_COOKIE_SECURE': True,
        'SECURE_HSTS_SECONDS': 31536000,
        'SECURE_PROXY_SSL_HEADER': ['HTTP_X_FORWARDED_PROTO', 'https'],
    }


@pytest.mark.parametrize(
    ('overrides', 'expected_error'),
    [
        ({'SECRET_KEY': ''}, 'Set SECRET_KEY'),
        ({'SECRET_KEY': 'weak-key'}, 'at least 50 characters'),
        ({'ALLOWED_HOSTS': '*'}, 'must not contain *'),
        ({'ALLOWED_HOSTS': ''}, 'Set ALLOWED_HOSTS'),
    ],
)
def test_production_rejects_missing_or_unsafe_credentials_and_hosts(
    tmp_path, overrides, expected_error
):
    env = {
        'DEBUG': 'False',
        'SECRET_KEY': secrets.token_urlsafe(50),
        'ALLOWED_HOSTS': 'stock.example.test',
    }
    env.update(overrides)
    result = run_settings(
        tmp_path,
        env,
        'import app_conf.settings',
    )

    assert result.returncode != 0
    assert expected_error in result.stderr
