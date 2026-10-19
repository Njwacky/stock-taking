#!/usr/bin/env python
"""
Quick test script for Comment System
Run with: python -m tests.manual.test_comment_system
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from stockT.models import User, UserComment
from django.utils import timezone
from datetime import timedelta


def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_model_creation():
    """Test creating UserComment instances"""
    print_section("Testing Model Creation")
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_commenter',
            defaults={
                'clock_number': '9999',
                'role': 'user'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✓ Created test user: {user.username}")
        else:
            print(f"✓ Using existing user: {user.username}")
        
        # Create test comment
        comment = UserComment.objects.create(
            user=user,
            category='bug',
            subject='Test Bug Report',
            message='This is a test bug report to verify the system works.',
            status='pending'
        )
        print(f"✓ Created comment ID: {comment.id}")
        print(f"  - Category: {comment.get_category_display()}")
        print(f"  - Status: {comment.get_status_display()}")
        print(f"  - Created: {comment.created_at}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_comment_queries():
    """Test querying comments"""
    print_section("Testing Comment Queries")
    
    try:
        # Count total comments
        total = UserComment.objects.count()
        print(f"✓ Total comments: {total}")
        
        # Count by status
        pending = UserComment.objects.filter(status='pending').count()
        reviewed = UserComment.objects.filter(status='reviewed').count()
        resolved = UserComment.objects.filter(status='resolved').count()
        dismissed = UserComment.objects.filter(status='dismissed').count()
        
        print(f"  - Pending: {pending}")
        print(f"  - Reviewed: {reviewed}")
        print(f"  - Resolved: {resolved}")
        print(f"  - Dismissed: {dismissed}")
        
        # Count by category
        print("\n✓ Comments by category:")
        for category, label in UserComment.CATEGORY_CHOICES:
            count = UserComment.objects.filter(category=category).count()
            print(f"  - {label}: {count}")
        
        # Recent comments
        recent = UserComment.objects.order_by('-created_at')[:5]
        print(f"\n✓ Recent comments (last 5):")
        for comment in recent:
            print(f"  - [{comment.status}] {comment.subject[:50]}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_comment_updates():
    """Test updating comments"""
    print_section("Testing Comment Updates")
    
    try:
        # Get a pending comment
        comment = UserComment.objects.filter(status='pending').first()
        
        if not comment:
            print("⚠ No pending comments to test with")
            return True
        
        print(f"✓ Testing with comment ID: {comment.id}")
        print(f"  - Original status: {comment.status}")
        
        # Get or create admin user
        admin, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'clock_number': '1111',
                'role': 'admin',
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        # Update comment
        comment.status = 'reviewed'
        comment.reviewed_by = admin
        comment.reviewed_at = timezone.now()
        comment.admin_response = 'Thank you for your feedback. We are looking into this.'
        comment.save()
        
        print(f"✓ Updated comment status to: {comment.status}")
        print(f"  - Reviewed by: {comment.reviewed_by.username}")
        print(f"  - Response added: {comment.admin_response[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_permissions():
    """Test permission checks"""
    print_section("Testing Permissions")
    
    try:
        # Check user roles
        admins = User.objects.filter(role='admin').count()
        managers = User.objects.filter(role='manager').count()
        supervisors = User.objects.filter(role='supervisor').count()
        users = User.objects.filter(role='user').count()
        
        print(f"✓ User roles:")
        print(f"  - Admins: {admins}")
        print(f"  - Managers: {managers}")
        print(f"  - Supervisors: {supervisors}")
        print(f"  - Regular users: {users}")
        
        # Check permissions
        admin = User.objects.filter(role='admin').first()
        if admin:
            can_manage = admin.role in ['admin', 'manager'] or admin.is_superuser
            print(f"\n✓ Admin '{admin.username}' can manage comments: {can_manage}")
        
        regular_user = User.objects.filter(role='user').first()
        if regular_user:
            can_manage = regular_user.role in ['admin', 'manager'] or regular_user.is_superuser
            print(f"✓ Regular user '{regular_user.username}' can manage comments: {can_manage}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_data_integrity():
    """Test data integrity"""
    print_section("Testing Data Integrity")
    
    try:
        # Check for orphaned comments (user deleted)
        total_comments = UserComment.objects.count()
        comments_with_users = UserComment.objects.filter(user__isnull=False).count()
        orphaned = total_comments - comments_with_users
        
        print(f"✓ Data integrity check:")
        print(f"  - Total comments: {total_comments}")
        print(f"  - Comments with valid users: {comments_with_users}")
        print(f"  - Orphaned comments: {orphaned}")
        
        if orphaned > 0:
            print(f"  ⚠ Warning: {orphaned} orphaned comments found!")
        
        # Check for comments without required fields
        invalid_comments = []
        for comment in UserComment.objects.all():
            if not comment.subject or not comment.message or not comment.category:
                invalid_comments.append(comment.id)
        
        if invalid_comments:
            print(f"  ⚠ Warning: {len(invalid_comments)} comments with missing required fields")
            print(f"    IDs: {invalid_comments}")
        else:
            print(f"  ✓ All comments have required fields")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def create_test_data():
    """Create sample test data"""
    print_section("Creating Test Data")
    
    try:
        # Get or create test users
        users = []
        for i in range(3):
            user, created = User.objects.get_or_create(
                username=f'test_user_{i+1}',
                defaults={
                    'clock_number': str(1000 + i),
                    'role': 'user'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        
        print(f"✓ Created/verified {len(users)} test users")
        
        # Create sample comments
        categories = ['bug', 'feature', 'improvement', 'question', 'other']
        statuses = ['pending', 'reviewed', 'resolved', 'dismissed']
        
        comments_created = 0
        for i, user in enumerate(users):
            for j in range(3):  # 3 comments per user
                category = categories[j % len(categories)]
                status = statuses[j % len(statuses)]
                
                comment, created = UserComment.objects.get_or_create(
                    user=user,
                    subject=f'Test {category.title()} #{i*3+j+1}',
                    defaults={
                        'category': category,
                        'message': f'This is a test {category} report. Lorem ipsum dolor sit amet.',
                        'status': status
                    }
                )
                if created:
                    comments_created += 1
        
        print(f"✓ Created {comments_created} new test comments")
        print(f"✓ Total comments in system: {UserComment.objects.count()}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print_section("Cleanup Test Data")
    
    response = input("Do you want to delete all test data? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled")
        return False
    
    try:
        # Delete test comments
        test_users = User.objects.filter(username__startswith='test_')
        comment_count = UserComment.objects.filter(user__in=test_users).count()
        UserComment.objects.filter(user__in=test_users).delete()
        print(f"✓ Deleted {comment_count} test comments")
        
        # Delete test users
        user_count = test_users.count()
        test_users.delete()
        print(f"✓ Deleted {user_count} test users")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 COMMENT SYSTEM TEST SUITE".center(60))
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Model Creation", test_model_creation()))
    results.append(("Comment Queries", test_comment_queries()))
    results.append(("Comment Updates", test_comment_updates()))
    results.append(("Permissions", test_permissions()))
    results.append(("Data Integrity", test_data_integrity()))
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return passed == total


def main():
    """Main function"""
    print("\n" + "="*60)
    print("  COMMENT SYSTEM TEST UTILITY")
    print("="*60)
    print("\nOptions:")
    print("  1. Run all tests")
    print("  2. Create test data")
    print("  3. Test model creation")
    print("  4. Test queries")
    print("  5. Test updates")
    print("  6. Test permissions")
    print("  7. Test data integrity")
    print("  8. Cleanup test data")
    print("  9. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            run_all_tests()
        elif choice == '2':
            create_test_data()
        elif choice == '3':
            test_model_creation()
        elif choice == '4':
            test_comment_queries()
        elif choice == '5':
            test_comment_updates()
        elif choice == '6':
            test_permissions()
        elif choice == '7':
            test_data_integrity()
        elif choice == '8':
            cleanup_test_data()
        elif choice == '9':
            print("\nExiting... Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
