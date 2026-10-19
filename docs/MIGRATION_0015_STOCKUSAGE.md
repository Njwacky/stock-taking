# Migration 0015: StockUsage Table Creation

## Issue
```
OperationalError at /tracking/
no such table: stockT_stockusage
```

The `StockUsage` model was defined in `models.py` but the database table didn't exist because migrations hadn't been created and applied.

## Solution

### 1. Created Migration
```bash
python manage.py makemigrations stockT
```

**Result:** Created `stockT/migrations/0015_stockusage.py`

### 2. Applied Migration
```bash
python manage.py migrate
```

**Result:** Created `stockT_stockusage` table in database

## Migration Details

**File:** `stockT/migrations/0015_stockusage.py`

**Created Table:** `stockT_stockusage`

**Fields:**
- `id` - BigAutoField (Primary Key)
- `clock_number` - CharField(10)
- `kit_type_name` - CharField(200)
- `quantity_used` - IntegerField
- `usage_date` - DateTimeField (auto_now_add)
- `feedback` - TextField (nullable)
- `purpose` - CharField(200, nullable)
- `status` - CharField(20) with choices
- `reviewed_at` - DateTimeField (nullable)
- `admin_notes` - TextField (nullable)
- `stock_deleted` - BooleanField (default=False)
- `kit` - ForeignKey to Kit (nullable, SET_NULL)
- `kit_type` - ForeignKey to KitType (nullable, SET_NULL)
- `reviewed_by` - ForeignKey to User (nullable, SET_NULL)
- `user` - ForeignKey to User (CASCADE)

**Model Options:**
- Ordering: `-usage_date` (newest first)
- Verbose names: "Stock Usage" / "Stock Usages"
- Custom permission: `review_stock_usage`

## Verification

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

## Status
✅ **RESOLVED** - The tracking page now works correctly at `/tracking/`

## Related Files
- `stockT/models.py` - StockUsage model definition
- `stockT/migrations/0015_stockusage.py` - Migration file
- `stockT/views.py` - stock_usage_tracking view
- `stockT/templates/stock_usage_tracking.html` - Template

## Date
2025-10-10
