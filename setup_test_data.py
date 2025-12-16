import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from stockT.models import User, UserComment
from django.utils import timezone

print("\n" + "="*70)
print(" 🔧 SETTING UP TEST DATA ".center(70))
print("="*70)

# Check existing users
existing_users = User.objects.count()
print(f"\n📊 Current database state:")
print(f"   Users: {existing_users}")
print(f"   Comments: {UserComment.objects.count()}")

# Create test users if they don't exist
users_created = 0

# 1. Create regular test user
if not User.objects.filter(username='testuser').exists():
    user = User.objects.create_user(
        username='testuser',
        password='test123',
        clock_number='5000',
        role='user'
    )
    users_created += 1
    print(f"\n✅ Created regular user:")
    print(f"   Username: testuser")
    print(f"   Password: test123")
    print(f"   Role: user")
else:
    print(f"\n✓ Regular user 'testuser' already exists")

# 2. Create admin test user
if not User.objects.filter(username='testadmin').exists():
    admin = User.objects.create_user(
        username='testadmin',
        password='admin123',
        clock_number='1000',
        role='admin',
        is_superuser=True,
        is_staff=True
    )
    users_created += 1
    print(f"\n✅ Created admin user:")
    print(f"   Username: testadmin")
    print(f"   Password: admin123")
    print(f"   Role: admin")
else:
    print(f"\n✓ Admin user 'testadmin' already exists")

# 3. Create manager test user
if not User.objects.filter(username='testmanager').exists():
    manager = User.objects.create_user(
        username='testmanager',
        password='manager123',
        clock_number='2000',
        role='manager'
    )
    users_created += 1
    print(f"\n✅ Created manager user:")
    print(f"   Username: testmanager")
    print(f"   Password: manager123")
    print(f"   Role: manager")
else:
    print(f"\n✓ Manager user 'testmanager' already exists")

# Create sample comments
comments_created = 0
testuser = User.objects.filter(username='testuser').first()

if testuser and UserComment.objects.filter(user=testuser).count() < 3:
    sample_comments = [
        {
            'category': 'bug',
            'subject': 'Login button not working on mobile',
            'message': 'When I try to login on my iPhone, the login button does not respond. This happens consistently.',
            'status': 'pending'
        },
        {
            'category': 'feature',
            'subject': 'Add dark mode support',
            'message': 'It would be great to have a dark mode option for night-time use. Many modern apps have this feature.',
            'status': 'reviewed'
        },
        {
            'category': 'improvement',
            'subject': 'Dashboard loading is slow',
            'message': 'The dashboard takes about 5 seconds to load. Could this be optimized?',
            'status': 'resolved'
        }
    ]
    
    for comment_data in sample_comments:
        if not UserComment.objects.filter(user=testuser, subject=comment_data['subject']).exists():
            comment = UserComment.objects.create(
                user=testuser,
                **comment_data
            )
            comments_created += 1
            
            # Add admin response to reviewed/resolved comments
            if comment.status in ['reviewed', 'resolved']:
                admin = User.objects.filter(role='admin').first()
                if admin:
                    comment.reviewed_by = admin
                    comment.reviewed_at = timezone.now()
                    if comment.status == 'reviewed':
                        comment.admin_response = "Thank you for your feedback! We're looking into this."
                    else:
                        comment.admin_response = "This has been fixed in the latest update. Please let us know if you still experience issues."
                    comment.save()
    
    if comments_created > 0:
        print(f"\n✅ Created {comments_created} sample comments")
else:
    print(f"\n✓ Sample comments already exist")

# Final summary
print("\n" + "="*70)
print(" 📊 FINAL DATABASE STATE ".center(70))
print("="*70)

print(f"\n👥 Users: {User.objects.count()}")
for role in ['admin', 'manager', 'supervisor', 'user']:
    count = User.objects.filter(role=role).count()
    if count > 0:
        print(f"   - {role.title()}: {count}")

print(f"\n💬 Comments: {UserComment.objects.count()}")
for status, label in UserComment.STATUS_CHOICES:
    count = UserComment.objects.filter(status=status).count()
    if count > 0:
        print(f"   - {label}: {count}")

print("\n" + "="*70)
print(" ✅ TEST DATA SETUP COMPLETE ".center(70))
print("="*70)

print("\n📝 Test Credentials:")
print("   Regular User: testuser / test123")
print("   Admin User:   testadmin / admin123")
print("   Manager User: testmanager / manager123")

print("\n🚀 Next Steps:")
print("   1. Server should be running at http://localhost:8000")
print("   2. Login with any of the test credentials above")
print("   3. Look for the 💬 button in bottom-right corner")
print("   4. Click and test the comment system!")

print("\n" + "="*70 + "\n")
