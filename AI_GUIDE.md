# Stock Management System - AI Developer Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Code Structure](#code-structure)
4. [Development Guidelines](#development-guidelines)
5. [Common Tasks](#common-tasks)
6. [Testing Guidelines](#testing-guidelines)
7. [Debugging Tips](#debugging-tips)
8. [Performance Considerations](#performance-considerations)
9. [Security Best Practices](#security-best-practices)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)
12. [Future Development](#future-development)

## Project Overview

### System Description
This is a Django-based Stock Management System designed to track and manage various types of kits (Feets, VHB Boss Tape, PI Strips, Rivnuts, etc.) across an organization. The system features role-based access control, comprehensive audit logging, and a responsive web interface.

### Key Features
- **User Management**: Role-based access (Admin, Manager, Supervisor, User)
- **Kit Management**: CRUD operations with condition tracking and expiration monitoring
- **Transfer System**: Kit transfers between users with audit trail
- **Reporting**: Multiple report formats and export capabilities
- **Audit Logging**: Comprehensive action tracking for compliance
- **Responsive UI**: Mobile-friendly interface with modern design

### Technology Stack
- **Backend**: Django 5.2, Python 3.9+
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Authentication**: Django's built-in auth system
- **Additional**: QR code generation, REST framework (for future API)

## Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   Web Server    │────│  App Server     │
│                 │    │   (Nginx)       │    │  (Gunicorn)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                              ┌─────────────────┐
                                              │   Database      │
                                              │ (PostgreSQL)    │
                                              └─────────────────┘
```

### Django Application Structure
```
stock_management_system/
├── app_conf/                 # Django project configuration
│   ├── __init__.py
│   ├── settings.py          # Main settings file
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── stockT/                 # Main Django app
│   ├── __init__.py
│   ├── admin.py            # Django admin configuration
│   ├── apps.py             # App configuration
│   ├── models.py           # Data models
│   ├── views.py            # View functions
│   ├── urls.py             # App URL configuration
│   ├── forms.py            # Form classes
│   ├── tests.py            # Test cases
│   ├── managers.py         # Custom model managers
│   └── signals.py          # Django signals
├── static/                 # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/              # HTML templates
│   └── stockT/
├── media/                  # User-uploaded files
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
└── README.md              # Project documentation
```

### Data Models Overview

#### User Model (Custom AbstractUser)
```python
class User(AbstractUser):
    clock_number = models.IntegerField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
```

#### Kit Model
```python
class Kit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kit_type = models.CharField(max_length=20, choices=KIT_TYPES)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    location = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
```

#### Supporting Models
- `KitTransfer`: Tracks kit transfers between users
- `AuditLog`: Comprehensive action logging
- `Report`: Stores generated reports
- `SystemSettings`: Global configuration

## Code Structure

### File Organization Conventions

#### Models (stockT/models.py)
- Group related models together
- Use clear, descriptive field names
- Include appropriate validators and constraints
- Add Meta classes for ordering and indexes
- Include helpful properties and methods

#### Views (stockT/views.py)
- Use function-based views for simplicity
- Implement proper authentication checks
- Include error handling and validation
- Use Django's built-in decorators (@login_required, etc.)
- Return appropriate HTTP responses

#### Templates (templates/stockT/)
- Follow Django's template inheritance structure
- Use base.html for common layout elements
- Include proper CSRF protection
- Use template tags for common functionality
- Implement responsive design patterns

#### Static Files (static/)
- Organize by type (css/, js/, images/)
- Use descriptive filenames
- Include version control for cache busting
- Follow CSS naming conventions (BEM methodology preferred)
- Minimize and compress for production

### Naming Conventions

#### Python Code
- **Functions and Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Members**: `_leading_underscore`
- **Database Fields**: `snake_case`

#### Templates
- **Blocks**: `{% block content %}` (snake_case)
- **Variables**: `{{ variable_name }}` (snake_case)
- **Template Files**: `feature_name.html` (snake_case)

#### CSS/HTML
- **Classes**: `kebab-case` or `BEM` methodology
- **IDs**: `kebab-case` (use sparingly)
- **HTML Files**: `feature_name.html` (snake_case)

### Code Style Guidelines

#### Python Code Style
- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter default)
- Include docstrings for all public functions and classes
- Use type hints where appropriate

#### Django-Specific Guidelines
- Use Django's ORM instead of raw SQL
- Prefer `get_object_or_404()` over `get()` for user-facing views
- Use `reverse()` or `{% url %}` instead of hardcoded URLs
- Implement proper form validation
- Use Django's built-in security features

#### JavaScript Guidelines
- Use modern ES6+ features
- Avoid global variables; use IIFEs or modules
- Include proper error handling
- Use semantic HTML5 elements
- Ensure accessibility (ARIA labels, keyboard navigation)

## Development Guidelines

### Setting Up Development Environment

#### Prerequisites
```bash
# Install Python 3.9+
python --version  # Should be 3.9+

# Install virtual environment
pip install virtualenv

# Create and activate virtual environment
virtualenv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Project Setup
```bash
# Clone the repository
git clone <repository-url>
cd stock_management_system

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Working with Git

#### Branch Strategy
- `main`: Production-ready code

### Docker Development Setup

#### Prerequisites
```bash
# Install Docker and Docker Compose
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

#### Docker Development Commands
```bash
# Build and start all services
docker-compose up

# Build images only
docker-compose build

# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop services and remove volumes
docker-compose down -v

# Access Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View database
docker-compose exec db psql -U postgres -d stock_management
```

#### Service Overview
- **web**: Django application with Gunicorn
- **db**: PostgreSQL database
- **redis**: Redis cache server
- **nginx**: Nginx web server (production profile)
- **celery**: Background task worker (production profile)
- **celery-beat**: Scheduled task scheduler (production profile)

### Docker Production Deployment

#### Production Setup
```bash
# Create production environment file
cp .env.example .env.production
# Edit .env.production with production settings

# Start production services
docker-compose --profile production up -d

# View production logs
docker-compose --profile production logs -f

# Backup database
docker-compose exec db pg_dump -U postgres stock_management > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres stock_management < backup.sql
```

#### Production Configuration
- **Environment**: Set `DEBUG=False` and configure proper `SECRET_KEY`
- **Database**: Use PostgreSQL with persistent volumes
- **Static Files**: Served by Nginx with caching
- **Media Files**: Stored in persistent volumes or cloud storage
- **SSL**: Configure SSL certificates in Nginx
- **Security**: Enable all security headers and rate limiting
- **Monitoring**: Health checks and logging enabled

#### Production Services
- **Web Application**: 3 Gunicorn workers, optimized for production
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for session and application caching
- **Web Server**: Nginx with SSL termination and compression
- **Background Tasks**: Celery for email sending and periodic tasks
- **Monitoring**: Health checks and comprehensive logging

#### Environment Variables for Production
```bash
# Required
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:pass@db:5432/stock_management
REDIS_URL=redis://redis:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Docker File Structure
```
project-root/
├── Dockerfile              # Multi-stage build configuration
├── docker-compose.yml      # Service orchestration
├── docker-entrypoint.sh    # Startup script
├── .dockerignore          # Build optimization
├── nginx.conf             # Nginx configuration
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── stockT/                # Django app
├── static/                # Static files
├── media/                 # User uploads
└── logs/                  # Application logs
```

#### Docker Best Practices
- **Multi-stage builds**: Use separate build and runtime stages
- **Non-root user**: Run containers as non-root user for security
- **Health checks**: Implement health checks for all services
- **Resource limits**: Set appropriate CPU and memory limits
- **Volumes**: Use persistent volumes for data storage
- **Networks**: Use isolated networks for service communication
- **Secrets**: Use Docker secrets or environment variables for sensitive data
- **Logging**: Configure centralized logging with proper rotation

#### Troubleshooting Docker Issues
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs redis

# Access container shell
docker-compose exec web bash
docker-compose exec db bash

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a

# Rebuild specific service
docker-compose build --no-cache web

# Force recreate containers
docker-compose up -d --force-recreate
```

## Recent Bug Fixes & Updates

### Database Schema Fix (September 2025)
- **Issue**: NOT NULL constraint error when adding kits through `/add_items/` endpoint
- **Root Cause**: Mismatch between model definition and database schema for `kit_type_fk` field
- **Solution Applied**:
  - Updated `kit_type_fk` field in `Kit` model to include `blank=True, null=True`
  - Created and applied migration `0007_remove_kit_stockt_kit_user_id_c54fc5_idx_and_more.py`
  - Verified existing KitType records in database (9 default kit types confirmed)
- **Impact**: Resolved kit creation failures, restored full functionality to add items feature

### Technical Details
- **Files Modified**: `stockT/models.py`
- **Migrations Created**: `stockT/migrations/0007_remove_kit_stockt_kit_user_id_c54fc5_idx_and_more.py`
- **Database Changes**: Removed old index, updated field constraints, created new composite index
- **Testing**: Verified kit types exist in database and form submission works correctly

### Lessons Learned
- Always ensure model definitions match database schema
- Test database migrations thoroughly in development environment
- Verify foreign key relationships and constraints before deployment
- Keep backup of working database state before applying major schema changes

### Authentication and Navigation Improvements (September 2025)
- **Issue**: Register and login buttons were always visible, even when users were logged in
- **Root Cause**: Missing conditional visibility logic in navigation template
- **Solution Applied**:
  - Modified `base.html` template to show register/login buttons only when user is not authenticated
  - Added conditional logic to display logout button only when user is authenticated
  - Implemented proper user authentication state checking
- **Impact**: Improved user experience with context-aware navigation

### Technical Details
- **Files Modified**: `stockT/templates/base.html`
- **Template Logic**: Added `{% if user.is_authenticated %}` conditional blocks
- **User Experience**: Cleaner navigation interface showing relevant options based on auth state

### Dynamic Page Titles Implementation (September 2025)
- **Issue**: Page titles were static and didn't reflect user-specific information
- **Root Cause**: Missing dynamic title generation logic
- **Solution Applied**:
  - Enhanced `base.html` template with dynamic title generation
  - Added logic to show "Dashboard-(username)" when user is logged in and on dashboard
  - Implemented page-specific titles for different sections (Add Stock, Manage Users, Profile, etc.)
  - Added conditional titles for authenticated vs non-authenticated users
- **Impact**: Improved user experience with personalized and context-aware page titles

### Technical Details
- **Files Modified**: `stockT/templates/base.html`
- **Implementation**: Used `request.resolver_match.url_name` for page detection and `user.username` for personalization
- **User Experience**: Dynamic titles that reflect current page and user state

### Why Register Carousel Implementation (September 2025)
- **Issue**: Why register section was too large and needed a more compact, engaging presentation
- **Root Cause**: Grid layout was taking too much vertical space
- **Solution Applied**:
  - Converted grid layout to horizontal carousel with sliding functionality
  - Implemented smaller cards (200px width) arranged in single line
  - Added navigation controls (prev/next buttons) and dot indicators
  - Implemented auto-advance functionality (5-second intervals)
  - Added smooth CSS transitions and JavaScript carousel logic
  - Made cards more compact with shorter text and smaller icons
- **Impact**: Significantly reduced vertical space usage while maintaining all registration benefits information

### Technical Details
- **Files Modified**: `stockT/templates/dashboard.html`, `static/most-received-kits.css`
- **Carousel Features**: 3 slides showing 2 cards each, auto-advance, manual navigation, responsive design
- **User Experience**: More engaging, space-efficient presentation of registration benefits

### Complete Requirements Integration (September 2025)
- **Issue**: Project needed comprehensive integration of all requirements from documentation
- **Root Cause**: Missing dependencies, CSS classes, and feature implementations
- **Solution Applied**:
  - Updated `requirements.txt` with all production and development dependencies
  - Added all required CSS classes to `static/base.css` from requirements specification
  - Verified clock number validation implementation (models, forms, templates)
  - Confirmed QR code generation and profile functionality are fully implemented
  - Ensured all CSS files exist and are properly imported
  - Updated AI guide with all recent improvements and technical details
- **Impact**: Project now fully compliant with all requirements and specifications

### Technical Details
- **Files Modified**: `requirements.txt`, `static/base.css`, `AI_GUIDE.md`
- **Dependencies**: Added production-ready packages (PostgreSQL, Redis, monitoring, testing)
- **CSS Classes**: Added 20+ required CSS classes for various components
- **Feature Verification**: Confirmed all major features are implemented and working

### Dashboard Selection Count Implementation (September 2025)
- **Issue**: Dashboard was missing selected kit count functionality similar to manage users page
- **Root Cause**: Missing JavaScript functions for selection management and count display
- **Solution Applied**:
  - Implemented complete selection management functionality in `static/js/dashboard.js`
  - Added `updateSelection()` function to display real-time count of selected kits
  - Added `toggleSelectAll()` function for select-all checkbox functionality
  - Added `clearSelection()` function to clear all selections
  - Added `submitBulkDelete()` function for bulk deletion with confirmation
  - Implemented dual counter support for both sticky and regular bulk action bars
  - Added dynamic show/hide of bulk action bars based on selection state
  - Enhanced user experience with smooth interactions and proper state management
- **Impact**: Dashboard now provides consistent selection management experience matching manage users page

### Technical Details
- **Files Modified**: `static/js/dashboard.js`
- **Functions Added**: `updateSelection()`, `toggleSelectAll()`, `clearSelection()`, `submitBulkDelete()`
- **Features Implemented**: Real-time count display, dynamic bulk actions, select-all functionality, confirmation dialogs
- **User Experience**: Enhanced with immediate visual feedback and intuitive bulk operations
- **Integration**: Maintains compatibility with existing dashboard filtering, sorting, and pagination

### Profile PDF Export Implementation (September 2025)
- **Issue**: Profile page lacked PDF export functionality for users to download and print their profiles with kit information
- **Root Cause**: Missing PDF generation libraries and export functionality
- **Solution Applied**:
  - Added PDF generation libraries (jsPDF and html2canvas) via CDN to profile template
  - Implemented download and print buttons in profile header with appropriate styling
  - Enhanced profile CSS with button styles (green for print, blue for download)
  - Completely rewrote profile JavaScript with comprehensive PDF functionality:
    - PDF generation using html2canvas to capture profile content
    - jsPDF integration for PDF creation and download
    - Loading states and comprehensive error handling
    - Success/error notifications with auto-dismiss
    - Print-optimized CSS for clean print output
    - Automatic filename generation based on profile username and timestamp
    - Proper handling of user's own profile vs. viewing others' profiles
  - Added console logging for debugging library loading and PDF generation process
- **Impact**: Users can now download their complete profile (including user info, QR code, and kits with quantities) as PDF or print directly from profile page

### Technical Details
- **Files Modified**: `stockT/templates/profile.html`, `static/profile.css`, `static/js/profile.js`
- **Libraries Added**: jsPDF 2.5.1, html2canvas 1.4.1 (via CDN)
- **Features Implemented**: PDF download, print functionality, loading states, error handling, notifications
- **User Experience**: One-click PDF generation with progress feedback and automatic filename generation
- **Profile Content**: Captures user information, QR code, and all kit data (types and quantities like "Rivnuts: 12")
- **Cross-browser Compatibility**: Works across modern browsers with fallback error handling

### Carousel Functionality Fix (September 2025)
- **Issue**: "Why Register" carousel cards were not moving/sliding on the dashboard page for non-authenticated users
- **Root Cause**: JavaScript carousel functionality was missing from dashboard.js file despite HTML template and CSS being properly implemented
- **Solution Applied**:
  - Added comprehensive carousel JavaScript functionality to `static/js/dashboard.js`:
    - Implemented global carousel variables for tracking slide index and auto-advance state
    - Created `initializeCarousel()` function to start auto-advance and set up hover interactions
    - Added `moveCarousel(direction)` function for manual prev/next button navigation
    - Implemented `currentSlide(slideIndex)` function for dot indicator navigation
    - Created `updateCarousel()` function for smooth sliding animations and dot state updates
    - Added `startCarouselAutoAdvance()` and `stopCarouselAutoAdvance()` functions with 5-second intervals
    - Implemented hover-to-pause functionality for better user experience
  - Enhanced carousel initialization in DOMContentLoaded event handler
  - Proper interval cleanup to prevent memory leaks
- **Impact**: "Why Register" carousel now functions correctly with auto-advance, manual controls, and smooth animations

### Technical Details
- **Files Modified**: `static/js/dashboard.js`
- **Functions Added**: `initializeCarousel()`, `moveCarousel()`, `currentSlide()`, `updateCarousel()`, `startCarouselAutoAdvance()`, `stopCarouselAutoAdvance()`
- **Features Implemented**: Auto-advance (5-second intervals), manual navigation (prev/next buttons), dot indicators, hover-to-pause, smooth CSS transitions
- **User Experience**: Cards automatically slide every 5 seconds, users can manually navigate, carousel pauses on hover for better interaction
- **Carousel Configuration**: 3 slides showing 2 cards each (6 total cards), 220px card width including gaps, wrap-around navigation
- **Integration**: Seamlessly integrated with existing dashboard functionality without conflicts

### Hamburger Menu (Mobile Navigation) Attempted Fix (September 2025)
- **Issue**: Hamburger menu (mobile navigation) was not working on mobile devices.
- **Root Cause**: Unknown; initial implementation appeared correct, but menu did not open/close as expected on mobile.
- **Solution Attempted**:
  - Enhanced `static/js/base.js` to improve mobile menu robustness and accessibility:
    - Added ARIA attributes for accessibility.
    - Ensured overlay is appended as the last child of `<body>`.
    - Added touch event support for mobile devices.
    - Added focus trap for keyboard accessibility.
    - Improved menu close/open logic on window resize.
    - Added comments for clarity.
  - Verified that the HTML structure and CSS for the menu/button matched requirements and AI guide.
- **Result**: The hamburger menu still did not work on mobile devices after these changes. Further investigation is required (possible CSS/JS conflicts, z-index issues, or device/browser-specific bugs).

## AI assistant rules

These rules are intended for automated agents and human collaborators using AI assistance when making changes in this repository. They are short, actionable, and enforced as conventions for safe, auditable edits.

- Safety first: never exfiltrate secrets (API keys, passwords, tokens, or private config files). If a secret is needed, prompt the user and do not attempt network access to fetch it.
- No external network calls: avoid calling external services from automated runs unless explicitly authorized by the repository owner.
- Tests before commit: run the project's test suite after any non-trivial code change and only commit passing changes. If tests fail, attempt up to three targeted fixes; then stop and report.
- Don't change tests: do not modify existing tests to make changes pass unless the user explicitly asks for test updates.
- Small, incremental edits: prefer minimal diffs that implement the requested change. Break larger work into clearly described commits.
- Explain changes: every automated commit or patch must include a short summary of what changed and why, plus one-line instructions to reproduce (commands to run tests/build).
- Preserve user workflow: keep existing project conventions (formatters, linters, dependency manager). When adding dependencies, update the appropriate manifest (`requirements.txt`) and mention why.
- No guessing of file paths/APIs: if you need to call a file, template, or endpoint that isn't present, ask a clarifying question instead of inventing it.
- Respect privacy in logs: avoid logging or printing user data, and redact any sensitive values in generated messages.
- Prefer server-side enforcement: security and permission checks must be enforced on the server-side (views, models) rather than relying solely on the client.
- Create reproducible commands: when suggesting commands for building/testing, prefer explicit, single-line commands that work on the project's OS (Windows PowerShell in this workspace).
- Communication: ask at most one clarifying question if essential; otherwise, proceed and report back with a concise change summary and verification steps.
