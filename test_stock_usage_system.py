#!/usr/bin/env python
"""
Test script for Stock Usage Tracking System

This script tests the complete workflow of the stock usage tracking system
including signal receivers and automatic stock deletion.

Run with: python manage.py shell < test_stock_usage_system.py
Or: python test_stock_usage_system.py (if Django is configured)
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from django.contrib.auth import get_user_model
from stockT.models import Kit, KitType, StockUsage
from django.utils import timezone

User = get_user_model()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_stock_usage_system():
    """Test the complete stock usage tracking system"""
    
    print_header("STOCK USAGE TRACKING SYSTEM TEST")
    
    # 1. Setup test data
    print_header("1. Setting up test data...")
    
    # Get or create test users
    try:
        test_user = User.objects.get(username='testuser')
        print(f"✓ Found test user: {test_user.username}")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            clock_number='TEST001'
        )
        print(f"✓ Created test user: {test_user.username}")
    
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='testadmin',
                password='admin123',
                email='admin@test.com',
                clock_number='ADMIN001'
            )
            print(f"✓ Created admin user: {admin_user.username}")
        else:
            print(f"✓ Found admin user: {admin_user.username}")
    except Exception as e:
        print(f"✗ Error creating admin: {e}")
        return
    
    # Get or create test kit type
    kit_type, created = KitType.objects.get_or_create(
        code='TEST_KIT',
        defaults={
            'name': 'Test Kit Type',
            'description': 'Test kit for usage tracking',
            'unit_of_measure': 'pieces',
            'is_active': True
        }
    )
    print(f"✓ {'Created' if created else 'Found'} kit type: {kit_type.name}")
    
    # Create test kit
    test_kit = Kit.objects.create(
        user=test_user,
        kit_type_fk=kit_type,
        quantity=10,
        condition='new',
        notes='Test kit for usage tracking'
    )
    print(f"✓ Created test kit: ID={test_kit.id}, Quantity={test_kit.quantity}")
    
    # 2. Test creating stock usage
    print_header("2. Testing stock usage creation...")
    
    usage = StockUsage.objects.create(
        user=test_user,
        clock_number=test_user.clock_number,
        kit=test_kit,
        kit_type=kit_type,
        kit_type_name=kit_type.name,
        quantity_used=3,
        feedback='Test feedback - kit quality is good',
        purpose='Testing stock usage system',
        status='pending'
    )
    print(f"✓ Created stock usage: ID={usage.id}, Status={usage.status}")
    print(f"  User: {usage.user.username}")
    print(f"  Kit Type: {usage.kit_type_name}")
    print(f"  Quantity: {usage.quantity_used}")
    print(f"  Feedback: {usage.feedback}")
    
    # 3. Test approval and automatic stock deletion
    print_header("3. Testing approval and automatic stock deletion...")
    
    print(f"Before approval:")
    print(f"  Kit quantity: {test_kit.quantity}")
    print(f"  Usage status: {usage.status}")
    print(f"  Stock deleted: {usage.stock_deleted}")
    
    # Approve the usage (this should trigger the signal)
    usage.status = 'approved'
    usage.reviewed_by = admin_user
    usage.reviewed_at = timezone.now()
    usage.admin_notes = 'Approved for testing'
    usage.save()
    
    print(f"\n✓ Approved usage request")
    
    # Refresh from database to see signal effects
    usage.refresh_from_db()
    test_kit.refresh_from_db()
    
    print(f"\nAfter approval (signal should have fired):")
    print(f"  Kit quantity: {test_kit.quantity} (should be 7)")
    print(f"  Usage status: {usage.status} (should be 'completed')")
    print(f"  Stock deleted: {usage.stock_deleted} (should be True)")
    
    # Verify the results
    if test_kit.quantity == 7 and usage.status == 'completed' and usage.stock_deleted:
        print(f"\n✓✓✓ SUCCESS! Signal worked correctly!")
        print(f"    Stock was automatically reduced from 10 to 7")
    else:
        print(f"\n✗✗✗ FAILED! Signal did not work as expected")
        print(f"    Expected: quantity=7, status='completed', stock_deleted=True")
        print(f"    Got: quantity={test_kit.quantity}, status={usage.status}, stock_deleted={usage.stock_deleted}")
    
    # 4. Test complete deletion
    print_header("4. Testing complete stock deletion...")
    
    # Create another usage that uses all remaining stock
    usage2 = StockUsage.objects.create(
        user=test_user,
        clock_number=test_user.clock_number,
        kit=test_kit,
        kit_type=kit_type,
        kit_type_name=kit_type.name,
        quantity_used=7,  # Use all remaining
        feedback='Using all remaining stock',
        purpose='Complete deletion test',
        status='pending'
    )
    print(f"✓ Created second usage: ID={usage2.id}, Quantity={usage2.quantity_used}")
    
    kit_id = test_kit.id
    print(f"Before approval: Kit #{kit_id} exists with quantity {test_kit.quantity}")
    
    # Approve (should delete the entire kit)
    usage2.status = 'approved'
    usage2.reviewed_by = admin_user
    usage2.reviewed_at = timezone.now()
    usage2.save()
    
    print(f"✓ Approved second usage")
    
    # Check if kit was deleted
    usage2.refresh_from_db()
    kit_exists = Kit.objects.filter(id=kit_id).exists()
    
    print(f"\nAfter approval:")
    print(f"  Kit exists: {kit_exists} (should be False)")
    print(f"  Usage status: {usage2.status} (should be 'completed')")
    print(f"  Stock deleted: {usage2.stock_deleted} (should be True)")
    
    if not kit_exists and usage2.status == 'completed' and usage2.stock_deleted:
        print(f"\n✓✓✓ SUCCESS! Complete deletion worked!")
        print(f"    Kit was automatically deleted")
    else:
        print(f"\n✗✗✗ FAILED! Complete deletion did not work")
    
    # 5. Summary
    print_header("5. Test Summary")
    
    all_usages = StockUsage.objects.filter(user=test_user).order_by('-usage_date')
    print(f"\nTotal usage records created: {all_usages.count()}")
    for u in all_usages:
        print(f"  - Usage #{u.id}: {u.quantity_used} {u.kit_type_name} - {u.status}")
    
    print_header("TEST COMPLETE")
    print("\nTo view logs, check: logs/django.log")
    print("To clean up test data, run:")
    print(f"  StockUsage.objects.filter(user__username='testuser').delete()")
    print(f"  User.objects.filter(username='testuser').delete()")
    print(f"  KitType.objects.filter(code='TEST_KIT').delete()")

if __name__ == '__main__':
    try:
        test_stock_usage_system()
    except Exception as e:
        print(f"\n✗✗✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
