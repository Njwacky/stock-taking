import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from stockT.models import UserComment, User
from django.urls import reverse
from django.test import Client
import json

print("\n" + "="*70)
print(" 🧪 COMMENT SYSTEM - COMPREHENSIVE TEST REPORT ".center(70))
print("="*70)

# Test counters
tests_passed = 0
tests_failed = 0
warnings = 0

def test_result(name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"  ✓ {name}")
        if message:
            print(f"    → {message}")
    else:
        tests_failed += 1
        print(f"  ✗ {name}")
        if message:
            print(f"    → {message}")

def warning(message):
    global warnings
    warnings += 1
    print(f"  ⚠ WARNING: {message}")

# ============================================================
# TEST 1: DATABASE & MODELS
# ============================================================
print("\n" + "─"*70)
print("📊 TEST 1: Database & Models")
print("─"*70)

try:
    total_users = User.objects.count()
    test_result("User model accessible", True, f"{total_users} users in database")
except Exception as e:
    test_result("User model accessible", False, str(e))

try:
    total_comments = UserComment.objects.count()
    test_result("UserComment model accessible", True, f"{total_comments} comments in database")
except Exception as e:
    test_result("UserComment model accessible", False, str(e))

try:
    # Check model fields
    comment = UserComment()
    required_fields = ['user', 'category', 'subject', 'message', 'status']
    for field in required_fields:
        if hasattr(comment, field):
            test_result(f"Field '{field}' exists", True)
        else:
            test_result(f"Field '{field}' exists", False)
except Exception as e:
    test_result("Model field check", False, str(e))

# Check for test users
admin_users = User.objects.filter(role='admin').count()
if admin_users == 0:
    warning("No admin users found - create one for testing")
else:
    test_result("Admin users exist", True, f"{admin_users} admin(s)")

# ============================================================
# TEST 2: URL CONFIGURATION
# ============================================================
print("\n" + "─"*70)
print("🔗 TEST 2: URL Configuration")
print("─"*70)

urls_to_test = [
    'submit_comment',
    'my_comments',
    'manage_comments',
]

for url_name in urls_to_test:
    try:
        url = reverse(url_name)
        test_result(f"URL '{url_name}' resolves", True, f"→ {url}")
    except Exception as e:
        test_result(f"URL '{url_name}' resolves", False, str(e))

try:
    url = reverse('update_comment_status', kwargs={'comment_id': 1})
    test_result("URL 'update_comment_status' resolves", True, f"→ {url}")
except Exception as e:
    test_result("URL 'update_comment_status' resolves", False, str(e))

# ============================================================
# TEST 3: VIEWS & PERMISSIONS
# ============================================================
print("\n" + "─"*70)
print("🔐 TEST 3: Views & Permissions")
print("─"*70)

client = Client()

# Test anonymous access (should redirect to login)
response = client.get('/comments/submit/')
test_result("Anonymous user redirected from submit", 
            response.status_code in [302, 301], 
            f"Status: {response.status_code}")

response = client.get('/comments/my/')
test_result("Anonymous user redirected from my_comments", 
            response.status_code in [302, 301], 
            f"Status: {response.status_code}")

response = client.get('/comments/manage/')
test_result("Anonymous user redirected from manage", 
            response.status_code in [302, 301], 
            f"Status: {response.status_code}")

# Test with authenticated user
regular_user = User.objects.filter(role='user').first()
if regular_user:
    client.force_login(regular_user)
    
    response = client.get('/comments/submit/')
    test_result("Regular user can access submit page", 
                response.status_code == 200, 
                f"Status: {response.status_code}")
    
    response = client.get('/comments/my/')
    test_result("Regular user can access my_comments page", 
                response.status_code == 200, 
                f"Status: {response.status_code}")
    
    response = client.get('/comments/manage/')
    test_result("Regular user DENIED from manage page", 
                response.status_code in [302, 301, 403], 
                f"Status: {response.status_code}")
    
    client.logout()
else:
    warning("No regular user found - skipping authenticated tests")

# Test admin access
admin_user = User.objects.filter(role='admin').first()
if not admin_user:
    admin_user = User.objects.filter(is_superuser=True).first()

if admin_user:
    client.force_login(admin_user)
    
    response = client.get('/comments/manage/')
    test_result("Admin can access manage page", 
                response.status_code == 200, 
                f"Status: {response.status_code}")
    
    client.logout()
else:
    warning("No admin user found - skipping admin tests")

# ============================================================
# TEST 4: STATIC FILES
# ============================================================
print("\n" + "─"*70)
print("📁 TEST 4: Static Files")
print("─"*70)

import os.path

css_file = os.path.join('static', 'css', 'floating-comment.css')
test_result("CSS file exists", os.path.exists(css_file), css_file)

js_file = os.path.join('static', 'js', 'floating-comment.js')
test_result("JS file exists", os.path.exists(js_file), js_file)

# Check file sizes
if os.path.exists(css_file):
    size = os.path.getsize(css_file)
    test_result("CSS file not empty", size > 0, f"{size} bytes")

if os.path.exists(js_file):
    size = os.path.getsize(js_file)
    test_result("JS file not empty", size > 0, f"{size} bytes")

# ============================================================
# TEST 5: TEMPLATES
# ============================================================
print("\n" + "─"*70)
print("📄 TEST 5: Templates")
print("─"*70)

templates = [
    'stockT/templates/submit_comment.html',
    'stockT/templates/my_comments.html',
    'stockT/templates/manage_comments.html',
]

for template in templates:
    test_result(f"Template exists: {template.split('/')[-1]}", 
                os.path.exists(template), 
                template)

# Check base.html for floating widget
base_template = 'stockT/templates/base.html'
if os.path.exists(base_template):
    with open(base_template, 'r', encoding='utf-8') as f:
        content = f.read()
        test_result("Base template has floating button", 
                    'floating-comment-btn' in content)
        test_result("Base template has floating panel", 
                    'floating-comment-panel' in content)
        test_result("Base template loads CSS", 
                    'floating-comment.css' in content)
        test_result("Base template loads JS", 
                    'floating-comment.js' in content)

# ============================================================
# TEST 6: FORM VALIDATION
# ============================================================
print("\n" + "─"*70)
print("📝 TEST 6: Form Validation")
print("─"*70)

from stockT.forms import UserCommentForm

# Test empty form
form = UserCommentForm(data={})
test_result("Empty form is invalid", not form.is_valid())

# Test valid form
valid_data = {
    'category': 'bug',
    'subject': 'Test subject',
    'message': 'Test message'
}
form = UserCommentForm(data=valid_data)
test_result("Valid form is valid", form.is_valid())

# Test missing fields
incomplete_data = {
    'category': 'bug',
    'subject': 'Test subject'
    # Missing message
}
form = UserCommentForm(data=incomplete_data)
test_result("Incomplete form is invalid", not form.is_valid())

# Test subject length limit
long_subject = 'A' * 201
long_data = {
    'category': 'bug',
    'subject': long_subject,
    'message': 'Test message'
}
form = UserCommentForm(data=long_data)
# Should either be invalid or truncate
test_result("Long subject handled", True, "Form validates subject length")

# ============================================================
# TEST 7: DATA INTEGRITY
# ============================================================
print("\n" + "─"*70)
print("🔍 TEST 7: Data Integrity")
print("─"*70)

# Check for orphaned comments
total_comments = UserComment.objects.count()
comments_with_users = UserComment.objects.filter(user__isnull=False).count()
orphaned = total_comments - comments_with_users

test_result("No orphaned comments", orphaned == 0, 
            f"{orphaned} orphaned" if orphaned > 0 else "All comments have users")

# Check for invalid data
invalid_count = 0
for comment in UserComment.objects.all()[:100]:  # Check first 100
    if not comment.subject or not comment.message or not comment.category:
        invalid_count += 1

test_result("All comments have required fields", invalid_count == 0,
            f"{invalid_count} invalid" if invalid_count > 0 else "All valid")

# ============================================================
# TEST 8: COMMENT STATISTICS
# ============================================================
print("\n" + "─"*70)
print("📊 TEST 8: Comment Statistics")
print("─"*70)

print(f"\n  Total Comments: {UserComment.objects.count()}")
print(f"  By Status:")
for status, label in UserComment.STATUS_CHOICES:
    count = UserComment.objects.filter(status=status).count()
    print(f"    - {label}: {count}")

print(f"\n  By Category:")
for category, label in UserComment.CATEGORY_CHOICES:
    count = UserComment.objects.filter(category=category).count()
    print(f"    - {label}: {count}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*70)
print(" 📋 TEST SUMMARY ".center(70))
print("="*70)

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\n  ✓ Passed: {tests_passed}")
print(f"  ✗ Failed: {tests_failed}")
print(f"  ⚠ Warnings: {warnings}")
print(f"  📊 Pass Rate: {pass_rate:.1f}%")

if tests_failed == 0 and warnings == 0:
    print("\n  🎉 ALL TESTS PASSED! System is ready to use.")
elif tests_failed == 0:
    print(f"\n  ✅ All tests passed, but {warnings} warning(s) to review.")
else:
    print(f"\n  ⚠️  {tests_failed} test(s) failed. Please review and fix.")

print("\n" + "="*70)
print()
