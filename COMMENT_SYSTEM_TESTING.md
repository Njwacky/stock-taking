# Comment System Testing Guide

## 🧪 Comprehensive Testing Checklist

### 1. Basic Functionality Tests

#### A. Floating Button Tests
- [ ] **Button Visibility**
  - Login as regular user → Button should appear
  - Logout → Button should disappear
  - Login as admin → Button should appear
  - Login as manager → Button should appear
  
- [ ] **Button Interaction**
  - Click button → Panel should open
  - Click button again → Panel should close (toggle)
  - Click outside panel → Panel should close
  - Click calculator button → Calculator should appear ABOVE comment panel
  - Both buttons visible and not overlapping

#### B. Submit Feedback Tab Tests
- [ ] **Form Validation**
  - Submit empty form → Should show validation errors
  - Submit without category → Should show error
  - Submit without subject → Should show error
  - Submit without message → Should show error
  - Submit with only category → Should show error
  - Submit with all fields → Should succeed

- [ ] **Field Limits**
  - Subject: Try entering 201+ characters → Should be limited to 200
  - Message: Try very long text (1000+ chars) → Should accept
  - Category: Try selecting each option → All should work

- [ ] **AJAX Submission**
  - Submit valid form → Should show success message
  - Form should clear after successful submission
  - Should NOT reload the page
  - Should automatically switch to "My Feedback" tab

- [ ] **Error Handling**
  - Disconnect internet → Submit form → Should show error
  - Submit while server is processing → Should disable button
  - Submit button should show "Submitting..." during process

#### C. My Feedback Tab Tests
- [ ] **Loading Comments**
  - Switch to "My Feedback" tab → Should load comments
  - No comments → Should show "No feedback submitted yet" message
  - With comments → Should display last 5 comments
  - More than 5 comments → Should show "View All X Comments" link

- [ ] **Comment Display**
  - Check category badges → Should be color-coded correctly
  - Check status badges → Should show correct status
  - Check truncation → Long messages should be truncated to 100 chars
  - Check dates → Should display formatted dates
  - Check admin responses → Should display if present

- [ ] **Status Colors**
  - Pending → Yellow background
  - Reviewed → Blue background
  - Resolved → Green background
  - Dismissed → Red background

### 2. Full Page Tests

#### A. Submit Comment Page (`/comments/submit/`)
- [ ] **Access Control**
  - Not logged in → Should redirect to login
  - Logged in → Should show form
  
- [ ] **Form Submission**
  - Submit valid form → Should show success message
  - Submit invalid form → Should show errors
  - Should redirect to dashboard after success
  - Cancel button → Should return to dashboard

#### B. My Comments Page (`/comments/my/`)
- [ ] **Access Control**
  - Not logged in → Should redirect to login
  - Logged in → Should show own comments only
  
- [ ] **Pagination**
  - Create 21+ comments → Should paginate (20 per page)
  - Test "Next" button → Should work
  - Test "Previous" button → Should work
  - Test "First" and "Last" buttons → Should work
  
- [ ] **Comment Details**
  - All fields should display correctly
  - Admin responses should be visible
  - Dates should be formatted properly

#### C. Manage Comments Page (`/comments/manage/`)
- [ ] **Access Control**
  - Not logged in → Should redirect to login
  - Regular user → Should redirect/show error
  - Supervisor → Should redirect/show error
  - Manager → Should show page
  - Admin → Should show page
  
- [ ] **Filtering**
  - Filter by status → Should show only matching comments
  - Filter by category → Should show only matching comments
  - Combine filters → Should work correctly
  - Change filter → Should auto-submit form
  
- [ ] **Pagination**
  - Create 31+ comments → Should paginate (30 per page)
  - Test pagination with filters applied
  
- [ ] **Update Comment**
  - Change status → Should save
  - Add admin response → Should save
  - Update existing response → Should overwrite
  - Check reviewed_by field → Should be current user
  - Check reviewed_at field → Should be current timestamp

### 3. Permission & Security Tests

#### A. URL Access Tests
Try accessing URLs directly:
- [ ] `/comments/submit/` - Logged out → Redirect to login
- [ ] `/comments/my/` - Logged out → Redirect to login
- [ ] `/comments/manage/` - Regular user → Denied
- [ ] `/comments/manage/` - Supervisor → Denied
- [ ] `/comments/manage/` - Manager → Allowed
- [ ] `/comments/manage/` - Admin → Allowed
- [ ] `/comments/update/1/` - Regular user → Denied
- [ ] `/comments/update/1/` - Manager → Allowed

#### B. Data Isolation Tests
- [ ] User A submits comment
- [ ] User B views "My Feedback" → Should NOT see User A's comment
- [ ] Admin views "Manage Comments" → Should see ALL comments
- [ ] User A can only see their own comments in floating panel

#### C. CSRF Protection
- [ ] Submit form without CSRF token → Should fail
- [ ] Submit form with invalid CSRF token → Should fail
- [ ] Submit form with valid CSRF token → Should succeed

### 4. Edge Cases & Breaking Points

#### A. Database Tests
- [ ] **Empty Database**
  - No comments exist → All pages should handle gracefully
  - "My Feedback" → Show empty state
  - "Manage Comments" → Show empty state

- [ ] **Large Dataset**
  - Create 100+ comments → Test performance
  - Test pagination with large dataset
  - Test filtering with large dataset

- [ ] **Orphaned Data**
  - Delete user who submitted comment → Comment should still exist
  - Check comment.user → Should handle deleted user gracefully

#### B. Input Validation Tests
- [ ] **SQL Injection Attempts**
  - Subject: `'; DROP TABLE stockT_usercomment; --`
  - Message: `<script>alert('XSS')</script>`
  - Should be escaped/sanitized

- [ ] **XSS Attempts**
  - Subject: `<img src=x onerror=alert('XSS')>`
  - Message: `<iframe src="javascript:alert('XSS')"></iframe>`
  - Should be escaped in display

- [ ] **Special Characters**
  - Subject: `Test with "quotes" and 'apostrophes'`
  - Message: `Test with <brackets> & ampersands`
  - Should display correctly

- [ ] **Unicode/Emoji**
  - Subject: `Test 🚀 with 中文 and émojis`
  - Message: `Testing 🎉🎊🎈 multiple emojis`
  - Should save and display correctly

- [ ] **Very Long Input**
  - Subject: Exactly 200 characters → Should accept
  - Subject: 201 characters → Should reject or truncate
  - Message: 10,000+ characters → Should accept

#### C. Concurrent User Tests
- [ ] Two admins update same comment simultaneously
- [ ] User submits while admin is reviewing
- [ ] Multiple users submit at same time

#### D. Browser/Device Tests
- [ ] **Desktop Browsers**
  - Chrome → Test all features
  - Firefox → Test all features
  - Edge → Test all features
  - Safari → Test all features

- [ ] **Mobile Browsers**
  - Mobile Chrome → Test floating button position
  - Mobile Safari → Test floating button position
  - Test panel responsiveness on small screens
  - Test form usability on mobile

- [ ] **Screen Sizes**
  - Desktop (1920x1080) → Both buttons visible
  - Laptop (1366x768) → Both buttons visible
  - Tablet (768px) → Buttons should adjust
  - Mobile (375px) → Buttons should stack/adjust

#### E. Network Conditions
- [ ] **Slow Connection**
  - Submit form on slow 3G → Should show loading state
  - Load comments on slow connection → Should show loading

- [ ] **Offline**
  - Open panel while offline → Should handle gracefully
  - Submit form while offline → Should show error

- [ ] **Connection Loss**
  - Start submission → Disconnect → Should show error
  - Reconnect → Should allow retry

### 5. Integration Tests

#### A. Navigation Tests
- [ ] Click "Manage Feedback" in navbar → Should go to manage page
- [ ] Click "View All Comments" in floating panel → Should go to my comments page
- [ ] Submit from floating panel → Should update "My Feedback" tab
- [ ] Submit from full page → Should redirect properly

#### B. Calculator Interaction
- [ ] Open calculator → Should appear above comment panel
- [ ] Open comment panel → Calculator should still be accessible
- [ ] Open both → Both should be usable
- [ ] Close calculator → Comment panel should remain functional

#### C. Session Tests
- [ ] Submit comment → Logout → Login → Comment should persist
- [ ] Start typing comment → Logout → Data should be lost
- [ ] Long session → Submit comment → Should work (CSRF token valid)

### 6. Performance Tests

#### A. Load Time Tests
- [ ] First page load with floating widget → Should be fast
- [ ] Open floating panel → Should open instantly
- [ ] Load "My Feedback" tab → Should load quickly
- [ ] Switch tabs → Should be instant

#### B. Memory Tests
- [ ] Open/close panel 50 times → No memory leaks
- [ ] Submit 10 comments in a row → Should handle well
- [ ] Load page with 100+ comments → Should not crash

### 7. Accessibility Tests

#### A. Keyboard Navigation
- [ ] Tab to floating button → Should be focusable
- [ ] Press Enter on button → Should open panel
- [ ] Tab through form fields → Should work
- [ ] Submit with Enter key → Should work
- [ ] Escape key → Should close panel

#### B. Screen Reader Tests
- [ ] Button has proper aria-label/title
- [ ] Form fields have proper labels
- [ ] Error messages are announced
- [ ] Success messages are announced

### 8. Admin Workflow Tests

#### A. Review Process
- [ ] User submits bug report
- [ ] Admin receives notification (if implemented)
- [ ] Admin filters by "pending" status
- [ ] Admin reads comment
- [ ] Admin adds response
- [ ] Admin changes status to "reviewed"
- [ ] User sees response in "My Feedback"

#### B. Bulk Operations
- [ ] Filter by category → Update multiple comments
- [ ] Change status on 10+ comments
- [ ] Add responses to multiple comments

### 9. Error Recovery Tests

#### A. Form Errors
- [ ] Submit invalid form → Fix errors → Resubmit → Should work
- [ ] Get error → Refresh page → Form should be empty
- [ ] Get error → Go back → Form data should be preserved

#### B. Server Errors
- [ ] 500 error during submission → Should show error message
- [ ] 404 error on comment update → Should handle gracefully
- [ ] Database connection error → Should show friendly error

### 10. Data Integrity Tests

#### A. Comment Data
- [ ] Submit comment → Check database → All fields saved correctly
- [ ] Update status → Check database → Status updated
- [ ] Add response → Check database → Response saved
- [ ] Check timestamps → created_at should be set
- [ ] Check timestamps → reviewed_at should be set after review

#### B. User Association
- [ ] Comment.user → Should be submitter
- [ ] Comment.reviewed_by → Should be admin who reviewed
- [ ] Delete user → Comment should remain (or handle gracefully)

---

## 🐛 Known Potential Issues to Test

1. **CSRF Token Expiry**: Long session → Submit form → May fail
2. **Concurrent Updates**: Two admins updating same comment
3. **Large Message**: 10,000+ character message → Display issues?
4. **Special Characters**: HTML/JavaScript in messages → XSS risk?
5. **Mobile Keyboard**: Keyboard covers form on mobile
6. **Browser Back Button**: Submit → Back → Resubmit → Duplicate?
7. **Multiple Tabs**: Open in 2 tabs → Submit in both → Race condition?
8. **Slow Server**: Form submission timeout → User clicks multiple times
9. **Panel Positioning**: Very small screens → Panel off-screen?
10. **Z-index Conflicts**: Other modals/popups → Overlap issues?

---

## 🔧 Testing Tools

### Manual Testing
```bash
# Run development server
python manage.py runserver

# Create test users
python manage.py createsuperuser

# Access admin panel
http://localhost:8000/admin
```

### Browser DevTools
- **Console**: Check for JavaScript errors
- **Network**: Monitor AJAX requests
- **Application**: Check localStorage/sessionStorage
- **Performance**: Monitor load times

### Database Inspection
```bash
# Django shell
python manage.py shell

# Check comments
from stockT.models import UserComment
UserComment.objects.all()
UserComment.objects.filter(status='pending')
```

### Load Testing (Optional)
```bash
# Install locust
pip install locust

# Create locustfile.py for load testing
# Run load test
locust -f locustfile.py
```

---

## ✅ Success Criteria

- [ ] All basic functionality works
- [ ] No JavaScript errors in console
- [ ] No SQL errors in server logs
- [ ] Proper permission enforcement
- [ ] Data saves correctly to database
- [ ] UI is responsive on all devices
- [ ] Calculator and comment button don't conflict
- [ ] Performance is acceptable (< 2s load time)
- [ ] No XSS or SQL injection vulnerabilities
- [ ] Accessible via keyboard
- [ ] Works in all major browsers

---

## 📝 Bug Report Template

When you find issues, document them:

```
**Bug Title**: [Brief description]

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**: 

**Actual Behavior**: 

**Browser/Device**: 

**User Role**: 

**Screenshots**: [If applicable]

**Console Errors**: [If any]

**Priority**: High/Medium/Low
```
