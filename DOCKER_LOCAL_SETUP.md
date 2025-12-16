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
# Build and start the application
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The application will be available at:
- **http://localhost:8000** (from the host machine)
- **http://<your-local-ip>:8000** (from other devices on your local network)

### 2. Access from Local Network

To allow other devices on your local network to access the app:

1. Find your local IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Linux/Mac: `ifconfig` or `ip addr`

2. Update `docker-compose.yml` if needed:
   ```yaml
   - CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://YOUR_LOCAL_IP:8000
   ```

3. Users can then access the app at `http://YOUR_LOCAL_IP:8000`

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

- **8000:8000**: Main application port

### Volumes

- `./data` → Database and application data
- `./media` → User uploaded files
- `./logs` → Application logs
- `./staticfiles` → Collected static files (including PWA assets)

## Environment Variables

You can customize the setup using environment variables:

```bash
# Create a .env file (optional)
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=*
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

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
4. Check that static files were collected: `docker-compose exec web python manage.py collectstatic`

### Cannot Access from Other Devices

1. Check firewall settings on host machine
2. Verify local IP address is correct
3. Ensure `ALLOWED_HOSTS=*` in docker-compose.yml
4. Add your local IP to `CSRF_TRUSTED_ORIGINS`

### Static Files Not Loading

1. Run collectstatic: `docker-compose exec web python manage.py collectstatic --noinput`
2. Check volume mounts in docker-compose.yml
3. Verify static files directory permissions

### Database Issues

1. Check `./data` directory exists and has proper permissions
2. Run migrations: `docker-compose exec web python manage.py migrate`

## Development Mode

For development, the source code is mounted as a volume, so changes are reflected immediately:

```yaml
volumes:
  - .:/app  # Source code mounted for development
```

**Note**: Remove this volume mount in production for better security.

## Production Considerations

⚠️ **This setup is for LOCAL USE ONLY**

For production deployment:
1. Remove source code volume mount
2. Set `DEBUG=False`
3. Use a proper secret key
4. Configure HTTPS (required for PWA in production)
5. Set up proper database (PostgreSQL recommended)
6. Configure nginx for static file serving
7. Set up proper backup strategy

## Support

For issues or questions:
1. Check application logs: `docker-compose logs web`
2. Check Django logs: `./logs/django.log`
3. Verify Docker containers: `docker-compose ps`

