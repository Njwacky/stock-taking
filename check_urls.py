import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from django.urls import reverse

print("="*60)
print("CHECKING COMMENT SYSTEM URLS")
print("="*60)

urls_to_check = [
    ('submit_comment', 'Submit Comment'),
    ('my_comments', 'My Comments'),
    ('manage_comments', 'Manage Comments'),
]

print("\n✅ Testing URL resolution:")
for url_name, description in urls_to_check:
    try:
        url = reverse(url_name)
        print(f"  ✓ {description}: {url}")
    except Exception as e:
        print(f"  ✗ {description}: ERROR - {e}")

# Test URL with parameter
try:
    url = reverse('update_comment_status', kwargs={'comment_id': 1})
    print(f"  ✓ Update Comment Status: {url}")
except Exception as e:
    print(f"  ✗ Update Comment Status: ERROR - {e}")

print("\n" + "="*60)
print("✅ URL check complete!")
print("="*60)
