import os, sys, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
import django
django.setup()
from django.test import Client
from django.conf import settings

# Allow the test client host
settings.ALLOWED_HOSTS = ['testserver', '127.0.0.1', 'localhost']

c = Client()
from django.contrib.auth import get_user_model
User = get_user_model()

# Ensure a test user exists and log in
username = 'test_admin'
password = 'testpass123'
user, created = User.objects.get_or_create(username=username)
if created:
    user.set_password(password)
    # give admin-ish permissions if possible
    user.is_staff = True
    user.is_superuser = True
    user.save()

logged_in = c.login(username=username, password=password)
if not logged_in:
    print('Could not log in as test user')
    resp = c.get('/')
else:
    resp = c.get('/')

import re
html = resp.content.decode('utf-8')
match = re.search(r"<div[^>]*id=['\"]kitStatsData['\"][^>]*>([\s\S]*?)</div>", html)
print('STATUS:', resp.status_code)
print('kitStatsData div:')
if match:
    content = match.group(1).strip()
    print(content)
else:
    print('NO kitStatsData DIV FOUND')