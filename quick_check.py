import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from stockT.models import UserComment, User

print("="*60)
print("QUICK DATABASE CHECK")
print("="*60)

# Count users
total_users = User.objects.count()
admins = User.objects.filter(role='admin').count()
managers = User.objects.filter(role='manager').count()
regular = User.objects.filter(role='user').count()

print(f"\n👥 Users:")
print(f"  Total: {total_users}")
print(f"  Admins: {admins}")
print(f"  Managers: {managers}")
print(f"  Regular: {regular}")

# Count comments
total_comments = UserComment.objects.count()
pending = UserComment.objects.filter(status='pending').count()
reviewed = UserComment.objects.filter(status='reviewed').count()
resolved = UserComment.objects.filter(status='resolved').count()
dismissed = UserComment.objects.filter(status='dismissed').count()

print(f"\n💬 Comments:")
print(f"  Total: {total_comments}")
print(f"  Pending: {pending}")
print(f"  Reviewed: {reviewed}")
print(f"  Resolved: {resolved}")
print(f"  Dismissed: {dismissed}")

# Count by category
print(f"\n📊 By Category:")
for category, label in UserComment.CATEGORY_CHOICES:
    count = UserComment.objects.filter(category=category).count()
    print(f"  {label}: {count}")

# Recent comments
print(f"\n📝 Recent Comments (last 5):")
recent = UserComment.objects.order_by('-created_at')[:5]
if recent:
    for comment in recent:
        print(f"  [{comment.status}] {comment.subject[:40]} - by {comment.user.username}")
else:
    print("  No comments yet")

print("\n" + "="*60)
print("✅ Database check complete!")
print("="*60)
