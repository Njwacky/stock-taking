"""
Quick Setup Script for Analytics System
Run this to set up the analytics tracking system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings


def setup_analytics():
    """Set up analytics system"""
    print("=" * 60)
    print("📊 Analytics System Setup")
    print("=" * 60)
    print()
    
    # Step 1: Check if middleware is configured
    print("Step 1: Checking middleware configuration...")
    middleware_path = 'stockT.middleware.analytics_middleware.AnalyticsMiddleware'
    if middleware_path in settings.MIDDLEWARE:
        print("✅ Analytics middleware already configured")
    else:
        print("⚠️  Analytics middleware NOT configured")
        print(f"   Please add '{middleware_path}' to MIDDLEWARE in settings.py")
    print()
    
    # Step 2: Run migrations
    print("Step 2: Running database migrations...")
    try:
        call_command('makemigrations', 'stockT')
        call_command('migrate')
        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration error: {e}")
    print()
    
    # Step 3: Generate initial daily stats
    print("Step 3: Generating initial statistics...")
    try:
        from stockT.analytics_service import AnalyticsService
        from django.utils import timezone
        
        today = timezone.now().date()
        daily_stat = AnalyticsService.generate_daily_stats(today)
        print(f"✅ Generated stats for {today}")
        print(f"   - Unique Devices: {daily_stat.unique_devices}")
        print(f"   - Total Sessions: {daily_stat.total_sessions}")
        print(f"   - Active Users: {daily_stat.active_users}")
    except Exception as e:
        print(f"⚠️  Could not generate initial stats: {e}")
    print()
    
    # Step 4: Check for milestones
    print("Step 4: Checking for milestones...")
    try:
        from stockT.analytics_service import AnalyticsService
        notifications = AnalyticsService.check_and_notify_milestones()
        if notifications:
            print(f"✅ {len(notifications)} milestone(s) detected!")
            for notif in notifications:
                print(f"   🎉 {notif.title}")
        else:
            print("✅ No new milestones (keep growing!)")
    except Exception as e:
        print(f"⚠️  Could not check milestones: {e}")
    print()
    
    # Step 5: Display access information
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("📍 Access your analytics dashboard at:")
    print("   http://localhost:8000/analytics/")
    print()
    print("📚 Read the full guide:")
    print("   docs/ANALYTICS_SETUP_GUIDE.md")
    print()
    print("🚀 Next steps:")
    print("   1. Make sure middleware is added to settings.py")
    print("   2. Start your Django server: python manage.py runserver")
    print("   3. Visit /analytics/ as an admin user")
    print("   4. Watch your app usage grow!")
    print()
    print("=" * 60)


if __name__ == '__main__':
    setup_analytics()
