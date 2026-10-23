#!/bin/bash
set -e

echo "Starting Django Stock Management Application..."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput --settings=app_conf.settings

# Create superuser if needed (only in development)
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput --settings=app_conf.settings
fi

# Load initial data if needed
if [ "$DJANGO_LOAD_INITIAL_DATA" = "true" ]; then
    echo "Loading initial data..."
    python manage.py loaddata initial_data --settings=app_conf.settings
fi

# Collect static files (including PWA manifest and service worker)
echo "Collecting static files (including PWA assets)..."
python manage.py collectstatic --noinput --settings=app_conf.settings

# Create necessary directories
mkdir -p /app/logs /app/media /app/static /app/staticfiles

# Set proper permissions (ignore errors for mounted volumes)
chmod -R 755 /app/logs /app/media /app/static /app/staticfiles 2>/dev/null || true

# Ensure PWA files are accessible
if [ -f "/app/staticfiles/sw.js" ]; then
    echo "PWA Service Worker found at /app/staticfiles/sw.js"
fi
if [ -f "/app/staticfiles/manifest.json" ]; then
    echo "PWA Manifest found at /app/staticfiles/manifest.json"
fi

echo "Django application setup complete!"

# Execute the command
if [ "$DJANGO_RUNSERVER" != "" ]; then
    echo "Starting Django development server on $DJANGO_RUNSERVER..."
    exec python manage.py runserver "$DJANGO_RUNSERVER" --settings=app_conf.settings
else
    exec "$@"
fi
