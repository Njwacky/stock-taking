
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from stockT import views as stockT_views

def health_check(request):
    """Simple health check endpoint for Docker/kubernetes monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Application is running'
    })

# Global error handlers
handler404 = 'stockT.views.custom_404'
handler500 = 'stockT.views.custom_500'

urlpatterns = [
    path('', include('stockT.urls')),
    path('django-admin/', admin.site.urls),  # Changed from 'admin/' to 'django-admin/' to avoid conflicts
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', stockT_views.logout_confirm, name='logout'),
    path('health/', health_check, name='health_check'),
]

# Serve static files during development and when DEBUG=True
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
