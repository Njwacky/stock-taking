from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    ContactInfo,
    DailyStats,
    DeviceTracker,
    Kit,
    KitType,
    NotificationLog,
    PageView,
    PasswordResetRequest,
    SessionTracker,
    StockUsage,
    SystemSettings,
    UsageMilestone,
    User,
    UserComment,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'clock_number', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Stock Management', {'fields': ('clock_number', 'department', 'phone_number', 'role')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Stock Management', {'fields': ('clock_number', 'department', 'phone_number', 'role')}),
    )


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ('id', 'kit_type_name', 'user', 'quantity', 'condition', 'is_active', 'timestamp')
    list_filter = ('condition', 'is_active')
    search_fields = ('user__username', 'kit_type_string', 'kit_type_fk__name', 'location')


@admin.register(KitType)
class KitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit_of_measure', 'is_active')
    search_fields = ('name', 'code')


@admin.register(StockUsage)
class StockUsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kit_type_name', 'quantity_used', 'status', 'stock_deleted', 'usage_date')
    list_filter = ('status', 'stock_deleted')
    search_fields = ('user__username', 'clock_number', 'kit_type_name')


@admin.register(UserComment)
class UserCommentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'category', 'status', 'created_at')
    list_filter = ('category', 'status')
    search_fields = ('subject', 'message', 'user__username')


admin.site.register([
    ContactInfo,
    DailyStats,
    DeviceTracker,
    NotificationLog,
    PageView,
    PasswordResetRequest,
    SessionTracker,
    SystemSettings,
    UsageMilestone,
])
