from django.contrib import admin
from .models import ApiProvider, ApiKey, ApiTest

@admin.register(ApiProvider)
class ApiProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'key_name', 'status', 'is_valid', 'created_at', 'last_tested')
    list_filter = ('status', 'is_valid', 'provider', 'created_at')
    search_fields = ('key_name', 'user__username', 'provider__name')
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(ApiTest)
class ApiTestAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'test_date', 'status', 'response_time')
    list_filter = ('status', 'test_date')
    search_fields = ('api_key__key_name', 'api_key__provider__name')
    readonly_fields = ('test_date',)
