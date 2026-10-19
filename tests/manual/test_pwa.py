"""
Test PWA Setup
Verifies all PWA files and configuration are correct
"""

import os
import json

print("\n" + "="*70)
print(" 🧪 PWA SETUP VERIFICATION ".center(70))
print("="*70 + "\n")

tests_passed = 0
tests_failed = 0

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

# Test 1: Check manifest.json exists
print("📄 Testing Manifest File")
print("─" * 70)

manifest_path = os.path.join('static', 'manifest.json')
if os.path.exists(manifest_path):
    test_result("Manifest file exists", True, manifest_path)
    
    # Validate JSON
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        test_result("Manifest JSON is valid", True)
        
        # Check required fields
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        for field in required_fields:
            if field in manifest:
                test_result(f"Manifest has '{field}'", True, str(manifest[field])[:50])
            else:
                test_result(f"Manifest has '{field}'", False, "Missing")
        
        # Check icons
        if 'icons' in manifest and len(manifest['icons']) > 0:
            test_result("Manifest has icons", True, f"{len(manifest['icons'])} icons defined")
        else:
            test_result("Manifest has icons", False, "No icons defined")
            
    except json.JSONDecodeError as e:
        test_result("Manifest JSON is valid", False, str(e))
else:
    test_result("Manifest file exists", False, "File not found")

# Test 2: Check service worker
print("\n🔧 Testing Service Worker")
print("─" * 70)

sw_path = os.path.join('static', 'sw.js')
if os.path.exists(sw_path):
    test_result("Service worker file exists", True, sw_path)
    
    with open(sw_path, 'r', encoding='utf-8') as f:
        sw_content = f.read()
    
    # Check for key service worker features
    features = [
        ('install event', "addEventListener('install'"),
        ('activate event', "addEventListener('activate'"),
        ('fetch event', "addEventListener('fetch'"),
        ('cache API', 'caches.open'),
    ]
    
    for feature_name, feature_code in features:
        if feature_code in sw_content:
            test_result(f"Has {feature_name}", True)
        else:
            test_result(f"Has {feature_name}", False)
else:
    test_result("Service worker file exists", False, "File not found")

# Test 3: Check offline page
print("\n📱 Testing Offline Page")
print("─" * 70)

offline_path = os.path.join('stockT', 'templates', 'offline.html')
if os.path.exists(offline_path):
    test_result("Offline page exists", True, offline_path)
    
    with open(offline_path, 'r', encoding='utf-8') as f:
        offline_content = f.read()
    
    if 'offline' in offline_content.lower():
        test_result("Offline page has offline content", True)
    else:
        test_result("Offline page has offline content", False)
else:
    test_result("Offline page exists", False, "File not found")

# Test 4: Check icons
print("\n🎨 Testing PWA Icons")
print("─" * 70)

icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
images_dir = os.path.join('static', 'images')

icons_found = 0
for size in icon_sizes:
    icon_path = os.path.join(images_dir, f'icon-{size}x{size}.png')
    if os.path.exists(icon_path):
        icons_found += 1

test_result(f"PWA icons generated", icons_found == len(icon_sizes), 
            f"{icons_found}/{len(icon_sizes)} icons found")

# Test 5: Check base template
print("\n📝 Testing Base Template")
print("─" * 70)

base_template = os.path.join('stockT', 'templates', 'base.html')
if os.path.exists(base_template):
    test_result("Base template exists", True)
    
    with open(base_template, 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    # Check for PWA meta tags
    pwa_features = [
        ('Manifest link', 'manifest.json'),
        ('Theme color', 'theme-color'),
        ('Apple mobile capable', 'apple-mobile-web-app-capable'),
        ('Service worker registration', 'serviceWorker.register'),
    ]
    
    for feature_name, feature_code in pwa_features:
        if feature_code in base_content:
            test_result(f"Has {feature_name}", True)
        else:
            test_result(f"Has {feature_name}", False)
else:
    test_result("Base template exists", False)

# Test 6: Check URLs
print("\n🔗 Testing URLs")
print("─" * 70)

urls_file = os.path.join('stockT', 'urls.py')
if os.path.exists(urls_file):
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls_content = f.read()
    
    if 'offline' in urls_content:
        test_result("Offline URL configured", True)
    else:
        test_result("Offline URL configured", False)
else:
    test_result("URLs file exists", False)

# Test 7: Check views
print("\n👁️ Testing Views")
print("─" * 70)

views_file = os.path.join('stockT', 'views.py')
if os.path.exists(views_file):
    with open(views_file, 'r', encoding='utf-8') as f:
        views_content = f.read()
    
    if 'def offline' in views_content:
        test_result("Offline view exists", True)
    else:
        test_result("Offline view exists", False)
else:
    test_result("Views file exists", False)

# Final Summary
print("\n" + "="*70)
print(" 📊 TEST SUMMARY ".center(70))
print("="*70)

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\n  ✓ Passed: {tests_passed}")
print(f"  ✗ Failed: {tests_failed}")
print(f"  📊 Pass Rate: {pass_rate:.1f}%")

if tests_failed == 0:
    print("\n  🎉 ALL TESTS PASSED! PWA is ready to use.")
    print("\n  📝 Next Steps:")
    print("     1. Run: python manage.py runserver")
    print("     2. Open: http://localhost:8000")
    print("     3. Check DevTools → Application → Manifest")
    print("     4. Test install functionality")
else:
    print(f"\n  ⚠️  {tests_failed} test(s) failed. Please review and fix.")
    print("\n  💡 Common fixes:")
    print("     - Run: python generate_pwa_icons.py")
    print("     - Run: python manage.py collectstatic --noinput")
    print("     - Check file paths are correct")

print("\n" + "="*70 + "\n")
