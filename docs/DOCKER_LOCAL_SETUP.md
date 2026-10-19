# Docker Setup for Local Use Only

## Overview

This Django Stock Management application is configured for **LOCAL USE ONLY** with PWA (Progressive Web App) support. Users in your local area can install the app on their devices and use it offline.

## Key Features

✅ **Local Network Access** - Configured to work on local network  
✅ **PWA Enabled** - Users can install the app on their devices  
✅ **Offline Support** - App works without internet connection  
✅ **Docker Optimized** - Simplified for local development and deployment  

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Prepare writable bind-mount directories
mkdir -p data media logs staticfiles

# On Linux/macOS, run the container as your host user so those mounts stay writable
export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"

# Build and start the application (or add -d to run in the background)
docker compose up --build
```

The application will be available at:
- **http://localhost:8001** (from the host machine)
- **http://<your-local-ip>:8001** (from other devices on your local network)

### 2. Access from Local Network

To allow other devices on your local network to access the app:

1. Find your local IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Linux/Mac: `ifconfig` or `ip addr`

2. Copy `.env.example` to `.env`, then add your local IP to both `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`:
   ```dotenv
   ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_LOCAL_IP
   CSRF_TRUSTED_ORIGINS=http://localhost:8001,http://127.0.0.1:8001,http://YOUR_LOCAL_IP:8001
   ```

3. Users can then access the app at `http://YOUR_LOCAL_IP:8001`

## PWA Installation

### Desktop (Chrome/Edge)

1. Open the app in Chrome or Edge
2. Look for the install icon (⊕) in the address bar
3. Click "Install" to add to desktop
4. The app will open in a standalone window

### Mobile (Android)

1. Open the app in Chrome mobile browser
2. Tap the menu (⋮)
3. Select "Install app" or "Add to Home Screen"
4. The app icon will appear on your home screen

### Mobile (iOS)

1. Open the app in Safari
2. Tap the Share button
3. Select "Add to Home Screen"
4. The app icon will appear on your home screen

## Docker Configuration

### Services

- **web**: Django application (main service)
- Production services (nginx, celery) are commented out for local use

### Ports

- **8001:8000**: Host port 8001 maps to the app's container port 8000

### Volumes

- `./data` → Database and application data
- `./media` → User uploaded files
- `./logs` → Application logs
- `./staticfiles` → Collected static files (including PWA assets)

## Environment Variables

The Compose setup uses SQLite at `./data/db.sqlite3` by default and runs in local development mode. Customize it with a `.env` file:

```bash
cp .env.example .env
```

For another device on your LAN, set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to include the host's IP address. For PostgreSQL, set `DATABASE_URL` to a reachable PostgreSQL URL; this Compose file does not start a PostgreSQL service.

## PWA Files

The following PWA files are automatically collected and served:

- `/static/sw.js` - Service Worker (enables offline functionality)
- `/static/manifest.json` - PWA Manifest (app configuration)
- `/static/images/*.png` - App icons

## Troubleshooting

### Service Worker Not Registering

1. Check browser console for errors
2. Verify `/static/sw.js` is accessible
3. Clear browser cache and reload
4. Check that static files were collected: `docker compose exec web python manage.py collectstatic`

### Cannot Access from Other Devices

1. Check firewall settings on host machine
2. Verify local IP address is correct
3. Add your local IP to `ALLOWED_HOSTS` in `.env`
4. Add the matching `http://YOUR_LOCAL_IP:8001` origin to `CSRF_TRUSTED_ORIGINS`

### Static Files Not Loading

1. Run collectstatic: `docker compose exec web python manage.py collectstatic --noinput`
2. Check volume mounts in docker-compose.yml
3. Verify static files directory permissions

### Database Issues

1. Check `./data` directory exists and has proper permissions
2. Run migrations: `docker compose exec web python manage.py migrate`

## Development Mode

For development, the source code is mounted as a volume, so changes are reflected immediately:

```yaml
volumes:
  - .:/app  # Source code mounted for development
```

**Note**: Remove this volume mount in production for better security.

## Production Considerations

⚠️ **This setup is for LOCAL USE ONLY**

For production deployment, do not use this local-development Compose configuration unchanged:
1. Use the Dockerfile's Gunicorn command (without the source-code mount or `runserver` override).
2. Set `DEBUG=False`, generate a strong `SECRET_KEY`, and set explicit `ALLOWED_HOSTS`.
3. Configure `DATABASE_URL` for a reachable PostgreSQL database and test migrations before rollout.
4. Terminate HTTPS at a trusted proxy such as the included Nginx config; set the secure-cookie and HSTS environment values.
5. Keep the application port private behind the proxy, serve collected static files, and configure backups.

When `DEBUG=False`, settings reject a missing/weak secret key, a wildcard/empty host list, and default to HTTPS redirects, secure cookies, and HSTS.

## Support

For issues or questions:
1. Check application logs: `docker compose logs web`
2. Check Django logs: `./logs/django.log`
3. Verify Docker containers: `docker compose ps`

