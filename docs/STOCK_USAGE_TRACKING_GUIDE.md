# Stock Usage Tracking System Guide

## Overview

The Stock Usage Tracking System allows users to log their stock/kit usage and request deletion of stock items even when supervisors are not around. The system uses Django signals to automatically process approved requests and delete or reduce stock quantities.

## Key Features

✅ **Self-Service Stock Usage Logging** - Any authenticated user can log their stock usage  
✅ **Automatic Stock Deletion** - Signal receivers automatically delete/reduce stock after approval  
✅ **Feedback System** - Users can provide feedback about stock quality and issues  
✅ **Admin Review Workflow** - Admins/Managers review and approve/reject usage requests  
✅ **Audit Trail** - Complete logging of all stock usage and deletions  
✅ **Notification System** - Admins receive notifications about pending requests  

---

## User Workflow

### For Regular Users

1. **Navigate to Track Usage**
   - Click "Track Usage" in the navigation menu
   - Or go to `/tracking/`

2. **Log Stock Usage**
   - Enter your clock number (must match your account)
   - Select the kit type you used
   - Enter the quantity used
   - Optionally add purpose and feedback
   - Click "Submit Usage"

3. **Track Your Requests**
   - View your recent usage in the sidebar
   - Check status: Pending → Approved → Completed
   - View full history at `/tracking/history/`

### For Admins/Managers

1. **Review Pending Requests**
   - See notification badge on "Track Usage" link
   - Click "Review Pending" button on tracking page
   - Or go to `/tracking/history/?status=pending`

2. **Approve or Reject**
   - Click "Review" button on any pending request
   - Add optional admin notes
   - Click "Approve & Delete Stock" or "Reject"

3. **Automatic Processing**
   - Upon approval, signals automatically:
     - Delete the kit if quantity matches usage
     - Reduce kit quantity if partial usage
     - Update usage status to "Completed"
     - Log all actions for audit trail

---

## Technical Architecture

### Models

**StockUsage Model** (`stockT/models.py`)
- Tracks who used stock, when, and how much
- Stores feedback and purpose
- Links to Kit and KitType
- Status: pending → approved/rejected → completed

### Signal Receivers

**`handle_stock_usage_approval`** (`stockT/signals.py`)
- Listens for StockUsage status changes
- Triggers when status = 'approved'
- Automatically deletes or reduces stock
- Logs all actions with detailed information

**`log_kit_deletion`** (`stockT/signals.py`)
- Listens for Kit deletions
- Updates related StockUsage records
- Maintains audit trail

**`notify_on_stock_usage`** (`stockT/signals.py`)
- Listens for new StockUsage creation
- Logs new usage requests
- Can be extended for email notifications

### Views

**`stock_usage_tracking`** - Main page for logging usage  
**`stock_usage_history`** - View all usage records with filters  
**`review_stock_usage`** - Admin review page  
**`delete_stock_after_usage`** - Manual deletion fallback  

### URLs

```
/tracking/                          - Log stock usage
/tracking/history/                  - View usage history
/tracking/review/<id>/              - Review specific usage
/tracking/delete/<id>/              - Manual stock deletion
```

---

## Signal Flow Diagram

```
User Logs Usage
    ↓
StockUsage Created (status='pending')
    ↓
notify_on_stock_usage signal fires
    ↓
Logs creation + feedback
    ↓
Admin Reviews Request
    ↓
Status Changed to 'approved'
    ↓
handle_stock_usage_approval signal fires
    ↓
Check if kit exists and has sufficient quantity
    ↓
If quantity matches → Delete entire kit
If quantity less → Reduce kit quantity
    ↓
Update StockUsage (stock_deleted=True, status='completed')
    ↓
Log action to django.log
```

---

## Logging

All stock usage actions are logged to `logs/django.log`:

**Log Levels:**
- `INFO` - Normal operations (creation, deletion, reduction)
- `WARNING` - Issues (no kit, insufficient quantity)
- `ERROR` - Failures during processing

**Log Format:**
```
[STOCK DELETED] Kit #123 (VHB Boss Tape 18mm) completely deleted. User: john, Quantity: 5, Approved by: admin
[STOCK REDUCED] Kit #124 (Rivnuts 8mm) quantity reduced from 100 to 95. User: jane, Used: 5, Approved by: manager
[NEW USAGE] User john (Clock: 12345) logged usage of 5 VHB Boss Tape 18mm. Status: pending
```

---

## Database Schema

### StockUsage Table Fields

| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey | User who used the stock |
| clock_number | CharField | Clock number verification |
| kit | ForeignKey | Associated kit (nullable) |
| kit_type | ForeignKey | Type of kit used |
| kit_type_name | CharField | Stored for history |
| quantity_used | IntegerField | Amount used |
| usage_date | DateTimeField | When logged |
| feedback | TextField | User feedback (optional) |
| purpose | CharField | Purpose of usage (optional) |
| status | CharField | pending/approved/rejected/completed |
| reviewed_by | ForeignKey | Admin who reviewed |
| reviewed_at | DateTimeField | When reviewed |
| admin_notes | TextField | Admin notes |
| stock_deleted | BooleanField | Whether stock was deleted |

---

## Permissions

**All Users:**
- Log their own stock usage
- View their own usage history

**Admins/Managers:**
- Review all usage requests
- Approve/reject requests
- View all usage history
- Manual stock deletion (fallback)

---

## Configuration

### Context Processor

Add to `settings.py`:
```python
'stockT.context_processors.pending_stock_usage_count',
```

This provides `pending_usage_count` to all templates for notification badges.

### Signal Registration

Signals are automatically registered in `stockT/apps.py`:
```python
def ready(self):
    import stockT.signals
```

---

## Troubleshooting

### Issue: Stock not deleted after approval

**Solution:**
1. Check logs in `logs/django.log` for errors
2. Verify kit exists and has sufficient quantity
3. Use manual deletion fallback: `/tracking/delete/<usage_id>/`

### Issue: Signal not firing

**Solution:**
1. Verify signals are imported in `apps.py`
2. Check that app is in `INSTALLED_APPS`
3. Restart Django server

### Issue: User can't log usage

**Solution:**
1. Verify user has clock_number set
2. Check that kit_type exists and is active
3. Ensure user is authenticated

---

## Future Enhancements

### Email Notifications (TODO)

Uncomment email code in `signals.py`:
```python
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()
admins = User.objects.filter(role__in=['admin', 'manager'])
for admin in admins:
    send_mail(
        subject=f'New Stock Usage Request from {instance.user.username}',
        message=f'User {instance.user.username} has logged usage...',
        from_email='noreply@stocktracker.com',
        recipient_list=[admin.email],
        fail_silently=True,
    )
```

### SMS Notifications

Integrate with Twilio or similar service for urgent notifications.

### Automated Approval

For trusted users, implement auto-approval after X successful requests.

---

## Testing Checklist

- [ ] User can log stock usage with valid clock number
- [ ] User cannot log usage with invalid clock number
- [ ] Admin sees notification badge for pending requests
- [ ] Admin can approve usage request
- [ ] Stock is automatically deleted/reduced after approval
- [ ] Usage status changes to 'completed'
- [ ] Admin can reject usage request
- [ ] Logs are created for all actions
- [ ] User can view their usage history
- [ ] Admin can view all usage history with filters
- [ ] Manual deletion works as fallback
- [ ] Feedback is captured and displayed

---

## Support

For issues or questions:
1. Check logs in `logs/django.log`
2. Review this documentation
3. Contact system administrator

---

**Last Updated:** 2025-10-10  
**Version:** 1.0  
**Author:** Stock Tracker Development Team
