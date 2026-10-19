# Quick Test Guide - Comment System

## 🚀 Quick Start Testing (5 Minutes)

### Step 1: Start the Server
```bash
cd c:\Users\njway\OneDrive\Desktop\summerlife
python manage.py runserver
```

### Step 2: Create Test Users (if not already done)
```bash
# In another terminal
python manage.py shell
```

```python
from stockT.models import User

# Create regular user
user = User.objects.create_user(
    username='testuser',
    password='test123',
    clock_number='5000',
    role='user'
)

# Create admin user
admin = User.objects.create_user(
    username='testadmin',
    password='admin123',
    clock_number='1000',
    role='admin',
    is_superuser=True
)

print("Users created!")
exit()
```

### Step 3: Basic Visual Test (2 minutes)

1. **Login as regular user**
   - Go to: `http://localhost:8000/`
   - Login: `testuser` / `test123`
   - ✓ Check: Floating 💬 button appears (bottom-right, left of calculator)
   - ✓ Check: Calculator button visible (bottom-right corner)

2. **Test floating button**
   - Click 💬 button
   - ✓ Check: Panel opens with two tabs
   - ✓ Check: "Submit" tab is active
   - ✓ Check: Form has Category, Subject, Message fields
   - Click outside panel
   - ✓ Check: Panel closes

3. **Test calculator overlap**
   - Click calculator button
   - ✓ Check: Calculator appears ABOVE comment panel
   - Click 💬 button
   - ✓ Check: Both are visible and usable

### Step 4: Submit Test Comment (1 minute)

1. Click 💬 button
2. Fill form:
   - Category: Bug Report
   - Subject: "Test bug"
   - Message: "This is a test message"
3. Click "Submit Feedback"
4. ✓ Check: Success message appears
5. ✓ Check: Form clears
6. ✓ Check: Switches to "My Feedback" tab
7. ✓ Check: Your comment appears in the list

### Step 5: Test Admin Features (2 minutes)

1. **Logout and login as admin**
   - Logout
   - Login: `testadmin` / `admin123`

2. **Check admin navigation**
   - ✓ Check: Comment icon (💬) appears in navbar
   - Click comment icon in navbar
   - ✓ Check: Goes to "Manage Feedback" page

3. **Test comment management**
   - ✓ Check: See all user comments
   - ✓ Check: Filter dropdowns work (Status, Category)
   - Select a comment
   - Change status to "Reviewed"
   - Add response: "Thank you for your feedback!"
   - Click "Update Comment"
   - ✓ Check: Success message appears

4. **Verify user sees response**
   - Logout
   - Login as `testuser` / `test123`
   - Click 💬 button
   - Go to "My Feedback" tab
   - ✓ Check: Comment shows "Reviewed" status
   - ✓ Check: Admin response is visible

---

## 🔥 Critical Tests (Must Pass)

### Test 1: Button Positioning
```
Expected: Comment button left of calculator, both visible
Test: Open both → Should not overlap
```

### Test 2: AJAX Submission
```
Expected: Form submits without page reload
Test: Submit form → Page should NOT refresh
```

### Test 3: Permission Enforcement
```
Expected: Regular users can't access admin pages
Test: Go to /comments/manage/ as regular user → Should be denied
```

### Test 4: Data Persistence
```
Expected: Comments save to database
Test: Submit → Logout → Login → Comment still there
```

### Test 5: XSS Protection
```
Expected: HTML/JavaScript is escaped
Test: Subject: <script>alert('XSS')</script>
      Should display as text, not execute
```

---

## 🐛 Common Issues to Check

### Issue 1: Floating Button Not Visible
**Symptoms**: No 💬 button appears
**Check**:
- Are you logged in?
- Check browser console for errors (F12)
- Check if CSS file loaded: `/static/css/floating-comment.css`

**Fix**:
```bash
python manage.py collectstatic --noinput
```

### Issue 2: Form Submission Fails
**Symptoms**: Error when submitting
**Check**:
- Browser console for errors
- Server terminal for error messages
- CSRF token present in form

**Debug**:
```python
# Check in Django shell
from stockT.models import UserComment
UserComment.objects.all()  # Should show comments
```

### Issue 3: Admin Can't See Comments
**Symptoms**: Manage page is empty
**Check**:
- Are there any comments in database?
- Is user actually admin role?

**Debug**:
```python
# Check user role
from stockT.models import User
user = User.objects.get(username='testadmin')
print(user.role)  # Should be 'admin'
print(user.is_superuser)  # Should be True
```

### Issue 4: Panel Positioning Wrong
**Symptoms**: Panel appears off-screen
**Check**:
- Browser window size
- Mobile vs desktop view
- Z-index conflicts

**Fix**: Check `floating-comment.css` positioning values

### Issue 5: Calculator Blocks Comment Button
**Symptoms**: Can't click comment button
**Check**:
- Z-index values (calculator should be higher)
- Button positions (should not overlap)

**Current values**:
- Calculator: z-index 1000/1100
- Comment: z-index 999
- Comment button: right: 100px
- Calculator button: right: 20px

---

## 📊 Quick Database Check

```bash
python manage.py shell
```

```python
from stockT.models import UserComment, User

# Count comments
print(f"Total comments: {UserComment.objects.count()}")

# Count by status
print(f"Pending: {UserComment.objects.filter(status='pending').count()}")
print(f"Reviewed: {UserComment.objects.filter(status='reviewed').count()}")

# List recent comments
for c in UserComment.objects.order_by('-created_at')[:5]:
    print(f"{c.id}: [{c.status}] {c.subject}")

# Check user roles
for u in User.objects.all():
    print(f"{u.username}: {u.role}")
```

---

## 🧪 Run Automated Tests

```bash
# Run the test script
python -m tests.manual.test_comment_system

# Choose option 1 to run all tests
# Choose option 2 to create test data
# Choose option 8 to cleanup test data
```

---

## 📱 Mobile Testing

### Test on Mobile Device
1. Get your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Access from phone: `http://YOUR_IP:8000`
3. Login and test floating button
4. ✓ Check: Button positioned correctly
5. ✓ Check: Panel is responsive
6. ✓ Check: Form is usable on mobile

### Test Responsive Design
1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test different screen sizes:
   - iPhone SE (375px)
   - iPad (768px)
   - Desktop (1920px)

---

## ✅ Success Checklist

- [ ] Floating button appears for logged-in users
- [ ] Button positioned left of calculator
- [ ] Panel opens/closes smoothly
- [ ] Form validation works
- [ ] AJAX submission works (no page reload)
- [ ] Comments appear in "My Feedback" tab
- [ ] Admin can access manage page
- [ ] Regular users cannot access manage page
- [ ] Admin can update comment status
- [ ] Admin responses appear for users
- [ ] No JavaScript errors in console
- [ ] No server errors in terminal
- [ ] Works on mobile devices
- [ ] Calculator and comment don't conflict

---

## 🆘 Need Help?

### Check Logs
```bash
# Server logs
# Look in terminal where runserver is running

# Django logs
# Check: logs/django.log
```

### Check Browser Console
```
F12 → Console tab
Look for red errors
```

### Check Database
```bash
python manage.py dbshell
SELECT * FROM stockT_usercomment;
```

### Reset Everything
```bash
# Delete all comments
python manage.py shell
>>> from stockT.models import UserComment
>>> UserComment.objects.all().delete()
>>> exit()

# Restart server
Ctrl+C
python manage.py runserver
```
