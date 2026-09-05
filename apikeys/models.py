from django.db import models
from django.contrib.auth.models import User

class ApiProvider(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    documentation_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class AIModel(models.Model):
    provider = models.ForeignKey(ApiProvider, on_delete=models.CASCADE, related_name='ai_models')
    name = models.CharField(max_length=100)
    model_id = models.CharField(max_length=100)  # ID yang digunakan untuk API call
    description = models.TextField(blank=True, null=True)
    capabilities = models.JSONField(default=dict)  # Menyimpan kemampuan model dalam format JSON
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.provider.name} - {self.name}"

class ApiKey(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
        ('testing', 'Testing'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    provider = models.ForeignKey(ApiProvider, on_delete=models.CASCADE, related_name='api_keys')
    key_name = models.CharField(max_length=100)
    key_value = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='testing')
    is_valid = models.BooleanField(default=False)
    last_tested = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    usage_count = models.IntegerField(default=0)  # Menambahkan penghitung penggunaan
    
    class Meta:
        unique_together = ('user', 'provider', 'key_name')
    
    def __str__(self):
        return f"{self.user.username} - {self.provider.name} - {self.key_name}"
    
    def increment_usage(self):
        """Increment the usage count of this API key"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

class ApiTest(models.Model):
    TEST_STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    )
    
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='tests')
    test_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='pending')
    response_time = models.FloatField(blank=True, null=True)  # in milliseconds
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.api_key} - {self.test_date} - {self.status}"

class ErrorLog(models.Model):
    ERROR_TYPES = (
        ('api_error', 'API Error'),
        ('rate_limit', 'Rate Limit'),
        ('authentication', 'Authentication Error'),
        ('timeout', 'Timeout'),
        ('server_error', 'Server Error'),
        ('other', 'Other Error'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='error_logs')
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='error_logs', null=True, blank=True)
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    error_message = models.TextField()
    error_details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.error_type} - {self.timestamp}"

class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.timestamp}"

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='chat_sessions')
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, related_name='chat_sessions', null=True, blank=True)
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    messages = models.ManyToManyField(ChatMessage, related_name='session')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.created_at}"

class ChatAttachment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_attachments')
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.file_name} - {self.uploaded_at}"
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
