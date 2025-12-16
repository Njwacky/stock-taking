# Stock Management System - Requirements

## System Requirements

### Hardware Requirements
- **Minimum**: 1GB RAM, 1 CPU Core, 5GB Storage
- **Recommended**: 2GB RAM, 2 CPU Cores, 10GB Storage
- **Production**: 4GB RAM, 4 CPU Cores, 20GB+ Storage

### Software Requirements

#### Core Dependencies
- **Python**: 3.9 or higher
- **Django**: 5.2.x (Web Framework)
- **Database**: SQLite (development), PostgreSQL (production recommended)

#### Python Packages (requirements.txt)
```
Django>=5.2,<6.0
qrcode[pil]>=7.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0
django-filter>=23.0
```

#### Optional Packages for Enhanced Functionality
```
# Database (Production)
psycopg2-binary>=2.8.0

# Email Services
django-anymail>=8.0.0

# Caching
redis>=4.0.0
django-redis>=5.0.0

# File Storage
boto3>=1.20.0  # For AWS S3
django-storages>=1.12.0

# Monitoring
sentry-sdk>=1.5.0
django-debug-toolbar>=3.2.0

# Testing
pytest>=7.0.0
pytest-django>=4.4.0
factory-boy>=3.2.0
coverage>=6.0.0
```

### Browser Requirements
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **JavaScript**: Enabled (required for interactive features)
- **Cookies**: Enabled (for session management)
- **Screen Resolution**: Minimum 1024x768, Recommended 1920x1080

### Network Requirements
- **Bandwidth**: Minimum 1 Mbps (recommended 5 Mbps+)
- **Latency**: Under 200ms for optimal user experience
- **Protocols**: HTTPS (production), HTTP/2 supported

## Functional Requirements

### User Management
- **Role-based Access Control**:
  - Administrator: Full system access
  - Manager: View reports, manage users
  - Supervisor: View all kits, transfer kits
  - User: Basic kit management
- **User Authentication**: Login/logout functionality
- **User Registration**: New user creation with validation
- **Clock Number System**: Unique employee identification

### Kit Management
- **Kit Types**:
  - Feets
  - VHB Boss Tape (18mm, 12mm, 7mm)
  - PI Strips
  - Rivnuts (8mm, 6mm, 5mm, 4mm)
- **Kit Tracking**:
  - Quantity management
  - Condition tracking (New, Good, Fair, Poor, Damaged)
  - Location tracking
  - Expiration date monitoring
- **Kit Operations**:
  - Add new kits
  - Edit existing kits
  - Delete kits (with confirmation)
  - Bulk operations
  - Kit transfers between users

### Reporting & Analytics
- **Report Types**:
  - Inventory Summary
  - User Activity
  - Kit Usage Statistics
  - Transfer History
  - Expiration Report
- **Export Formats**: PDF, CSV, Excel, JSON
- **Real-time Dashboards**: Visual data representation

### Profile Management
- **Profile Viewing**: Users can view their own profile and others' profiles
- **Profile Information**: Username, clock number, date joined, user type
- **QR Code Integration**: Profile QR codes for quick access
- **Kit Display**: Show all kits assigned to user with types and quantities
- **PDF Export**: Download complete profile as PDF document
- **Print Functionality**: Print-optimized profile output
- **Export Features**:
  - One-click PDF generation
  - Automatic filename generation (username_timestamp.pdf)
  - Include user information, QR code, and complete kit inventory
  - Loading states and progress feedback
  - Error handling and user notifications

### System Features
- **Audit Logging**: Track all system actions
- **Search & Filter**: Advanced filtering capabilities
- **Responsive Design**: Mobile-friendly interface
- **QR Code Generation**: For kit identification
- **Email Notifications**: System alerts and notifications

## Non-Functional Requirements

### Performance
- **Response Time**: Under 2 seconds for all operations
- **Concurrent Users**: Support 100+ simultaneous users
- **Data Processing**: Handle 10,000+ kit records efficiently
- **Uptime**: 99.5% availability (production)

### Security
- **Authentication**: Secure user authentication
- **Authorization**: Role-based access control
- **Data Protection**: Encrypted sensitive data
- **Session Management**: Secure session handling
- **Input Validation**: Protection against XSS, SQL injection
- **CSRF Protection**: Cross-site request forgery prevention

### Reliability
- **Data Integrity**: ACID compliance for database operations
- **Backup System**: Automated daily backups
- **Error Handling**: Graceful error recovery
- **Logging**: Comprehensive system logging

### Usability
- **User Interface**: Intuitive, consistent design
- **Accessibility**: WCAG 2.1 AA compliance
- **Help System**: Context-sensitive help and documentation
- **Multilingual Support**: English (default), extensible for other languages

### Scalability
- **Vertical Scaling**: Support for increased server resources
- **Horizontal Scaling**: Load balancer support
- **Database Scaling**: Support for read replicas
- **File Storage**: Scalable storage solutions

## Environmental Requirements

### Development Environment
- **Operating System**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python Environment**: Virtual environment recommended
- **IDE**: VS Code, PyCharm, or similar
- **Version Control**: Git
- **Containerization**: Docker & Docker Compose

### Testing Environment
- **Unit Testing**: pytest with Django test framework
- **Integration Testing**: Django test client
- **Browser Testing**: Selenium for cross-browser testing
- **Performance Testing**: Load testing tools
- **Container Testing**: Docker-based testing environments

### Production Environment
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **Containerization**: Docker with multi-stage builds
- **Web Server**: Gunicorn with Nginx
- **Database**: PostgreSQL 12+
- **Caching**: Redis
- **File Storage**: AWS S3 or similar
- **Monitoring**: Application performance monitoring
- **Orchestration**: Docker Compose or Kubernetes

## Docker Deployment Requirements

### Container Specifications
- **Base Image**: Python 3.9-slim
- **Architecture**: Multi-stage build for optimization
- **Security**: Non-root user execution, proper file permissions
- **Health Checks**: Integrated health monitoring for all services

### Docker Services
- **Web Application**: Django with Gunicorn WSGI server
- **Database**: PostgreSQL 13 with persistent volumes
- **Cache**: Redis 6 with persistence
- **Web Server**: Nginx with SSL termination and security headers
- **Background Tasks**: Celery worker and beat scheduler (optional)

### Environment Configuration
- **Settings**: Environment-based configuration via .env files
- **Security**: Secure secret management, CSRF protection
- **Database**: PostgreSQL connection with connection pooling
- **Caching**: Redis integration for session and application caching
- **File Storage**: Configurable for local or cloud storage (AWS S3)

### Performance Requirements
- **Build Optimization**: Multi-stage builds, proper .dockerignore
- **Resource Limits**: Configurable CPU and memory constraints
- **Static Files**: Efficient static file serving with caching
- **Database**: Connection pooling and query optimization
- **Load Balancing**: Ready for horizontal scaling

### Security Requirements
- **Container Security**: Non-root execution, read-only filesystem where possible
- **Network Security**: Isolated networks, proper firewall rules
- **Data Security**: Encrypted connections, secure secret management
- **Access Control**: Role-based access, rate limiting
- **Monitoring**: Security event logging and alerting

### Deployment Commands
```bash
# Development
docker-compose up

# Production
docker-compose --profile production up -d

# Build images
docker-compose build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables
Required environment variables for Docker deployment:
- `DEBUG`: Debug mode setting
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_HOSTS`: Allowed hostnames
- `CSRF_TRUSTED_ORIGINS`: Trusted CSRF origins
- `EMAIL_*`: Email configuration settings
- `AWS_*`: AWS S3 configuration (if using cloud storage)

## Compliance Requirements

### Data Privacy
- **GDPR Compliance**: User data protection
- **Data Retention**: Configurable retention policies
- **Data Deletion**: Right to be forgotten implementation

### Audit Requirements
- **Action Logging**: All user actions logged
- **Access Logging**: System access logging
- **Change Tracking**: Data change tracking
- **Report Generation**: Audit report capabilities

## Backup & Recovery

### Backup Strategy
- **Database Backups**: Daily automated backups
- **File Backups**: Weekly file system backups
- **Configuration Backups**: Version-controlled configuration
- **Off-site Storage**: Secure off-site backup storage

### Recovery Procedures
- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 24 hours
- **Disaster Recovery**: documented recovery procedures
- **Testing**: Regular recovery testing

## Maintenance Requirements

### Regular Maintenance
- **Security Updates**: Monthly security patching
- **System Updates**: Quarterly system updates
- **Performance Monitoring**: Continuous performance monitoring
- **Log Review**: Weekly log analysis

### Updates & Upgrades
- **Django Updates**: Follow LTS release cycle
- **Package Updates**: Monthly dependency updates
- **Database Updates**: As recommended by vendor
- **Security Patches**: Immediate application for critical issues

## Documentation Requirements

### User Documentation
- **User Manual**: Step-by-step user guide
- **Training Materials**: Video tutorials and guides
- **FAQ**: Frequently asked questions
- **Quick Start Guide**: Rapid onboarding guide

### Technical Documentation
- **API Documentation**: REST API documentation
- **Database Schema**: Complete data model documentation
- **Integration Guide**: Third-party integration instructions
- **Troubleshooting Guide**: Common issue resolution

### Administrative Documentation
- **Installation Guide**: System setup instructions
- **Configuration Guide**: System configuration options
- **Maintenance Guide**: System maintenance procedures
- **Security Guide**: Security best practices

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
- **Files Modified**: `stockT/models.py`, `stockT/views.py`
- **Migrations Created**: `stockT/migrations/0007_remove_kit_stockt_kit_user_id_c54fc5_idx_and_more.py`
- **Database Changes**: Removed old index, updated field constraints, created new composite index
- **Testing**: Verified kit types exist in database and form submission works correctly

### Additional Improvements (September 2025)
- **User Selection Enhancement**: Updated add_items view to show all users for managers, admins, and supervisors instead of just the current user
- **Role-Based Features**: 
  - Admin and Manager users can now see "Add New Kit Type" section in the add items form
  - Regular users can only add items for themselves
  - Supervisors can add items for any user but cannot create new kit types
- **User Interface**: Improved user experience with proper role-based feature visibility

## Recent Bug Fixes & Known Issues

### Hamburger Menu (Mobile Navigation) Attempted Fix (September 2025)
- **Issue**: Hamburger menu (mobile navigation) was not working on mobile devices.
- **Attempted Solution**:
  - Updated the JavaScript (`static/js/base.js`) to:
    - Add ARIA attributes for accessibility.
    - Add touch event support for mobile.
    - Ensure overlay is appended as last child of `<body>`.
    - Add focus trap for keyboard navigation.
    - Improve menu close/open logic on window resize.
  - Verified HTML and CSS structure per requirements.
- **Result**: The hamburger menu still did not work on mobile after these changes. Further investigation is needed (potential CSS/JS conflicts, z-index, or device/browser-specific issues).

## Future Enhancements

### Planned Features
- **Mobile Application**: Native mobile apps
- **Barcode Scanning**: Integration with barcode scanners
- **Advanced Analytics**: Business intelligence features
- **Integration APIs**: Third-party system integration
- **Multi-tenant Support**: Multiple organization support

### Technology Roadmap
- **Microservices Architecture**: Service decomposition
- **Containerization**: Docker deployment
- **Cloud Migration**: Cloud platform deployment
- **AI/ML Features**: Predictive analytics
- **Real-time Notifications**: WebSocket-based updates
