# Comment System Documentation

## Overview
A floating comment/feedback system has been added to the application. Users can submit feedback, bug reports, feature requests, and questions directly from any page using a floating widget.

## Features

### 🎈 Floating Widget (Float Button)
- **Location**: Bottom-right corner of every page (for authenticated users)
- **Icon**: 💬 emoji button with gradient purple background
- **Behavior**: Clicking opens a floating panel with two tabs

### 📝 Submit Feedback Tab
Users can submit feedback with:
- **Category**: Bug Report, Feature Request, Improvement Suggestion, Question, or Other
- **Subject**: Brief summary (max 200 characters)
- **Message**: Detailed description
- **Submission**: AJAX-based, no page reload required

### 📋 My Feedback Tab
- View your own submitted feedback
- See status: Pending Review, Reviewed, Resolved, or Dismissed
- View admin responses
- Shows last 5 comments in floating panel
- Link to view all comments on dedicated page

### 🛠️ Admin Management (Admin/Manager Only)
- **Navigation Link**: Comment icon in navbar (visible to admins/managers)
- **Filter Options**: Filter by status and category
- **Actions**:
  - Update comment status
  - Add admin responses
  - Track who reviewed and when

## URLs

### User URLs
- `/comments/submit/` - Submit new feedback (full page)
- `/comments/my/` - View all your feedback (full page)

### Admin URLs
- `/comments/manage/` - Manage all user feedback (admin/manager only)
- `/comments/update/<id>/` - Update comment status (admin/manager only)

## Database Model

### UserComment Model
```python
- user: ForeignKey to User (who submitted)
- category: Choice field (bug, feature, improvement, question, other)
- subject: CharField (max 200)
- message: TextField
- status: Choice field (pending, reviewed, resolved, dismissed)
- created_at: DateTimeField (auto)
- reviewed_at: DateTimeField (nullable)
- reviewed_by: ForeignKey to User (nullable)
- admin_response: TextField (nullable)
```

## Permissions
- **Submit Feedback**: All authenticated users
- **View Own Feedback**: All authenticated users
- **Manage All Feedback**: Admin and Manager roles only

## Files Added/Modified

### New Files
- `stockT/templates/submit_comment.html` - Full page feedback form
- `stockT/templates/my_comments.html` - User's feedback list
- `stockT/templates/manage_comments.html` - Admin management page
- `static/css/floating-comment.css` - Floating widget styles
- `static/js/floating-comment.js` - Floating widget functionality

### Modified Files
- `stockT/views.py` - Added comment views
- `stockT/urls.py` - Added comment URLs
- `stockT/forms.py` - Added UserCommentForm
- `stockT/models.py` - UserComment model (already existed)
- `stockT/templates/base.html` - Added floating widget and navigation link

## Usage

### For Users
1. Click the floating 💬 button in the bottom-right corner
2. Fill out the feedback form in the "Submit" tab
3. Click "Submit Feedback"
4. View your submissions in the "My Feedback" tab
5. Check for admin responses

### For Admins/Managers
1. Click the comment icon (💬) in the navigation bar
2. Use filters to find specific feedback
3. Update status and add responses
4. Users will see your responses in their feedback list

## Styling
- **Colors**: Purple gradient theme (#667eea to #764ba2)
- **Animation**: Smooth slide-up animation when opening
- **Responsive**: Mobile-friendly design
- **Position**: Fixed positioning, doesn't interfere with page content

## Technical Details
- AJAX form submission for seamless UX
- Pagination support (20 items per page for users, 30 for admins)
- Auto-loading of comments when switching tabs
- Click-outside-to-close functionality
- Form validation with error display
- Success/error messages in floating panel

## Future Enhancements
- Email notifications for new feedback
- Comment threading/replies
- Attachment support
- Priority levels
- Search functionality
- Export feedback to CSV/PDF
