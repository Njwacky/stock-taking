# 📊 Analytics & Device Tracking System - Setup Guide

## Overview
This system tracks how many devices have opened your app, when they accessed it, and sends you notifications for milestones to encourage you to keep developing!

## Features
- ✅ **Device Tracking** - Track unique devices accessing your app
- ✅ **Session Monitoring** - Monitor user sessions and activity
- ✅ **Page View Analytics** - See which pages are most popular
- ✅ **Real-time Statistics** - See who's online right now
- ✅ **Milestone Notifications** - Get notified when you reach usage milestones
- ✅ **Beautiful Dashboard** - Visual charts and statistics
- ✅ **Daily Reports** - Automatic daily statistics generation

## Installation Steps

### 1. Install Required Package
```bash
pip install pyyaml ua-parser user-agents
```

### 2. Update Models
Add the analytics models to your database:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Add Middleware
Add the analytics middleware to your `settings.py`:

```python
MIDDLEWARE = [
    # ... existing middleware ...
    'stockT.middleware.analytics_middleware.AnalyticsMiddleware',  # Add this line
]
```

### 4. Update URLs
Add analytics URLs to your `stockT/urls.py`:

```python
from stockT import analytics_views

urlpatterns = [
    # ... existing URLs ...
    
    # ========== ANALYTICS URLS ==========
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/chart-data/', analytics_views.analytics_chart_data, name='analytics_chart_data'),
    path('analytics/live-stats/', analytics_views.analytics_live_stats, name='analytics_live_stats'),
    path('analytics/notifications/', analytics_views.analytics_notifications, name='analytics_notifications'),
    path('analytics/devices/', analytics_views.analytics_devices, name='analytics_devices'),
    path('analytics/generate-report/', analytics_views.generate_daily_report, name='generate_daily_report'),
]
```

### 5. Add Navigation Link
Add a link to the analytics dashboard in your `base.html` navbar (for admins only):

```html
{% if user.is_authenticated and user.role in 'admin,manager' or user.is_superuser %}
<a href="{% url 'analytics_dashboard' %}" class="nav-link">
    <i class="fa fa-chart-line"></i> Analytics
</a>
{% endif %}
```

### 6. Set Up Daily Report Generation (Optional)
To automatically generate daily reports, add a cron job or scheduled task:

**Linux/Mac (crontab):**
```bash
# Run daily at midnight
0 0 * * * cd /path/to/summerlife && python manage.py shell -c "from stockT.analytics_service import AnalyticsService; AnalyticsService.generate_daily_stats()"
```

**Windows (Task Scheduler):**
Create a batch file `generate_daily_report.bat`:
```batch
cd C:\Users\njway\OneDrive\Desktop\summerlife
python manage.py shell -c "from stockT.analytics_service import AnalyticsService; AnalyticsService.generate_daily_stats()"
```
Then schedule it to run daily at midnight.

## Usage

### Accessing the Dashboard
1. Log in as an admin or manager
2. Click on "Analytics" in the navigation menu
3. View your statistics and charts!

### What You'll See

#### **Overview Statistics**
- **Total Devices** - How many unique devices have accessed your app
- **Total Sessions** - Total number of user sessions
- **Total Users** - Number of registered users
- **Online Now** - Users currently active (last 5 minutes)

#### **Charts**
- **Usage Trends** - Daily device, session, and user activity over time
- **Device Types** - Breakdown of mobile, tablet, and desktop users

#### **Recent Activity**
- **Recent Devices** - Latest devices that accessed your app
- **Active Sessions** - Currently active user sessions

#### **Milestones & Notifications**
You'll automatically receive notifications when you reach:
- **Device Count**: 10, 25, 50, 100, 250, 500, 1000 devices
- **Session Count**: 50, 100, 500, 1000, 5000 sessions
- **User Count**: 10, 25, 50, 100, 250 users

### Viewing Notifications
- Notifications appear on the analytics dashboard
- Click "Notifications" to see all milestone achievements
- Get encouraged to keep developing! 🎉

## How It Works

### Device Tracking
- Each device gets a unique ID stored in a cookie
- Tracks device type (mobile/tablet/desktop), browser, OS
- Records first seen and last seen timestamps
- Counts total sessions per device

### Session Tracking
- Creates a new session when a user visits
- Tracks pages visited and actions performed
- Calculates session duration
- Marks sessions as active/inactive

### Page View Tracking
- Records every page view
- Tracks time spent on each page
- Identifies most popular pages

### Milestone Detection
- Automatically checks for milestones on each admin dashboard visit
- Creates notifications when thresholds are reached
- Sends encouraging messages to keep you motivated!

## Privacy Considerations
- Device IDs are randomly generated UUIDs (not personally identifiable)
- IP addresses are stored but can be disabled if needed
- Users can be anonymous (not logged in)
- No sensitive personal data is collected

## Customization

### Adding Custom Milestones
Edit `analytics_service.py` and modify the `check_and_notify_milestones()` method:

```python
milestones_to_check = [
    ('device_count', DeviceTracker.objects.count(), [10, 25, 50, 100, 250, 500, 1000]),
    ('session_count', SessionTracker.objects.count(), [50, 100, 500, 1000, 5000]),
    ('user_count', User.objects.filter(is_active=True).count(), [10, 25, 50, 100, 250]),
    # Add your custom milestones here!
]
```

### Disabling IP Tracking
In `analytics_middleware.py`, comment out the IP address line:

```python
device = DeviceTracker.objects.create(
    # ...
    # ip_address=self._get_client_ip(request),  # Comment this out
    # ...
)
```

## Troubleshooting

### Charts Not Loading
- Make sure Chart.js is loaded: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- Check browser console for JavaScript errors

### No Devices Being Tracked
- Verify middleware is added to `settings.py`
- Check that cookies are enabled in your browser
- Ensure migrations have been run

### Milestones Not Triggering
- Visit the analytics dashboard (milestones are checked on each visit)
- Manually check: `python manage.py shell -c "from stockT.analytics_service import AnalyticsService; AnalyticsService.check_and_notify_milestones()"`

## API Endpoints

### Get Chart Data
```
GET /analytics/chart-data/?days=30
```
Returns JSON with daily statistics for charts.

### Get Live Stats
```
GET /analytics/live-stats/
```
Returns real-time statistics (online users, active devices, etc.).

### Generate Daily Report
```
POST /analytics/generate-report/
```
Manually trigger daily report generation.

## Congratulations! 🎉
Your analytics system is now set up! Every time someone uses your app, you'll see it tracked in the dashboard. Watch your numbers grow and get motivated to add more features!

## Next Steps
1. Share your app with more users
2. Watch the analytics dashboard
3. Celebrate each milestone
4. Keep building awesome features!

Remember: Every user interaction is a sign that your hard work is paying off! 🚀
