from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and auth routes
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('analytics/', views.analytics, name='analytics'),
    path('health-check/', views.health_check, name='health_check'),
    
    # API Key routes
    path('api-keys/', views.api_key_list, name='api_key_list'),
    path('api-keys/add/', views.api_key_create, name='api_key_create'),
    path('api-keys/<int:pk>/edit/', views.api_key_update, name='api_key_update'),
    path('api-keys/<int:pk>/delete/', views.api_key_delete, name='api_key_delete'),
    path('api-keys/<int:pk>/test/', views.test_api_key, name='test_api_key'),
    path('api-keys/<int:api_key_id>/history/', views.api_test_history, name='api_test_history'),
    path('api-keys/test-delete/<int:test_id>/', views.delete_api_test, name='delete_api_test'),
    path('api-keys/test-details/<int:test_id>/', views.get_test_details, name='get_test_details'),
    path('api-keys/bulk-test/', views.bulk_test_api_keys, name='bulk_test_api_keys'),
    path('api-keys/bulk-create/<str:provider_name>/', views.bulk_create_api_keys, name='bulk_create_api_keys'),
    
    # Chat routes
    path('chat/sessions/', views.chat_sessions, name='chat_sessions'),
    path('chat/new/', views.new_chat_session, name='new_chat_session'),
    path('chat/<int:session_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    path('api/models-for-key/<int:key_id>/', views.get_models_for_key, name='get_models_for_key'),
    path('attachment/<int:attachment_id>/', views.view_attachment, name='view_attachment'),

    
    # Error logs routes
    path('error-logs/', views.error_logs, name='error_logs'),
    path('error-logs/<int:pk>/resolve/', views.resolve_error, name='resolve_error'),
    path('error-logs/<int:pk>/delete/', views.delete_error, name='delete_error'),
]