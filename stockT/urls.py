"""URL configuration for the stockT application."""
from django.urls import path

from . import views

urlpatterns = [
    # Dashboard / home
    path('', views.dashboard, name='dashboard'),

    # Auth
    path('register/', views.register, name='register'),
    path('workspace/create/', views.workspace_create, name='workspace_create'),
    path('workspace/switch/', views.workspace_switch, name='workspace_switch'),
    path('workspace/settings/', views.workspace_settings, name='workspace_settings'),
    path('workspace/members/add/', views.workspace_member_add, name='workspace_member_add'),
    path('workspace/members/remove/', views.workspace_member_remove, name='workspace_member_remove'),
    path('password-reset/request/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/manage/', views.manage_reset_requests, name='manage_reset_requests'),
    path('password-reset/process/<int:reset_id>/', views.process_reset_request, name='process_reset_request'),
    path('change-password/', views.change_password, name='change_password'),

    # Stock items
    path('add-items/', views.add_items, name='add_items'),
    path('export/kits.csv', views.export_kits_csv, name='export_kits_csv'),
    path('get_user_kits/<int:user_id>/', views.get_user_kits, name='get_user_kits'),
    path('get_kit_types_for_edit/', views.get_kit_types_for_edit, name='get_kit_types_for_edit'),
    path('update_kit/<int:kit_id>/', views.update_kit, name='update_kit'),
    path('delete_kit/<int:kit_id>/', views.delete_kit, name='delete_kit'),

    # User management
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/add/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('edit-user/<int:user_id>/set-password/', views.set_user_password, name='set_user_password'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    # Kit types
    path('kit-types/', views.manage_kit_types, name='manage_kit_types'),

    # Profiles
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),

    # Stock usage tracking
    path('tracking/', views.stock_usage_tracking, name='stock_usage_tracking'),
    path('tracking/history/', views.stock_usage_history, name='stock_usage_history'),
    path('tracking/review/<int:usage_id>/', views.review_stock_usage, name='review_stock_usage'),
    path('tracking/delete/<int:usage_id>/', views.delete_stock_usage, name='delete_stock_usage'),

    # Stock distribution
    path('stock-distribution/', views.stock_distribution, name='stock_distribution'),

    # Inventory helpers
    path('most-received-kits/', views.most_received_kits, name='most_received_kits'),
    path('calculator/', views.inventory_calculator, name='inventory_calculator'),

    # Comments / feedback
    path('comments/submit/', views.submit_comment, name='submit_comment'),
    path('comments/my/', views.my_comments, name='my_comments'),
    path('comments/my-comments-json/', views.my_comments_json, name='my_comments_json'),
    path('comments/manage/', views.manage_comments, name='manage_comments'),
    path('comments/update/<int:comment_id>/', views.update_comment_status, name='update_comment_status'),

    # Admin management
    path('admin/manage/', views.manage_admins, name='manage_admins'),
    path('admin/create/', views.create_admin, name='create_admin'),
    path('admin/promote/<int:user_id>/', views.promote_admin, name='promote_admin'),
    path('admin/demote/<int:user_id>/', views.demote_admin, name='demote_admin'),

    # Footer contacts
    path('footer/contacts/', views.manage_footer_contacts, name='manage_footer_contacts'),
    path('footer/contacts/add/', views.add_footer_contact, name='add_footer_contact'),
    path('footer/contacts/edit/<int:contact_id>/', views.edit_footer_contact, name='edit_footer_contact'),
    path('footer/contacts/delete/<int:contact_id>/', views.delete_footer_contact, name='delete_footer_contact'),
    path('footer/contacts/toggle/<int:contact_id>/', views.toggle_footer_contact, name='toggle_footer_contact'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/live-stats/', views.analytics_live_stats, name='analytics_live_stats'),
    path('analytics/chart-data/', views.analytics_chart_data, name='analytics_chart_data'),
    path('analytics/notifications/', views.analytics_notifications, name='analytics_notifications'),
    path('analytics/devices/', views.analytics_devices, name='analytics_devices'),
    path('analytics/report/', views.generate_daily_report, name='generate_daily_report'),
    path('devices/', views.analytics_devices, name='devices'),

    # PWA
    path('offline/', views.offline, name='offline'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
]
