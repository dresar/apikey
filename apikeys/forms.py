from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import ApiKey, ApiProvider, ChatSession, ChatMessage, ErrorLog, ChatAttachment, AIModel

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        # Tambahkan kelas CSS untuk styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']
        
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        # Tambahkan kelas CSS untuk styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'

class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        fields = ['provider', 'key_name', 'key_value', 'notes']
        widgets = {
            'key_value': forms.PasswordInput(render_value=True),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ApiKeyForm, self).__init__(*args, **kwargs)
        
        # Tambahkan kelas CSS untuk styling
        for field_name, field in self.fields.items():
            if field_name != 'notes':  # notes sudah memiliki atribut class
                field.widget.attrs['class'] = 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'
    
    def save(self, commit=True):
        instance = super(ApiKeyForm, self).save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance

class ApiTestForm(forms.Form):
    api_key = forms.ModelChoiceField(queryset=ApiKey.objects.none())
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ApiTestForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['api_key'].queryset = ApiKey.objects.filter(user=user)

class ChatMessageForm(forms.ModelForm):
    attachment = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'hidden', 'id': 'file-upload'}))
    
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ketik pesan Anda di sini...', 'class': 'w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'}),
        }
        labels = {
            'content': '',
        }

class ChatSessionForm(forms.ModelForm):
    class Meta:
        model = ChatSession
        fields = ['title', 'api_key', 'ai_model']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'}),
            'ai_model': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ChatSessionForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['api_key'].queryset = ApiKey.objects.filter(user=user, is_valid=True)
            
            # Jika api_key sudah dipilih, filter model AI berdasarkan provider
            if 'api_key' in self.data:
                try:
                    api_key_id = int(self.data.get('api_key'))
                    api_key = ApiKey.objects.get(id=api_key_id)
                    self.fields['ai_model'].queryset = AIModel.objects.filter(provider=api_key.provider, is_active=True)
                except (ValueError, ApiKey.DoesNotExist):
                    pass
            elif self.instance.pk and self.instance.api_key:
                self.fields['ai_model'].queryset = AIModel.objects.filter(provider=self.instance.api_key.provider, is_active=True)

class ErrorLogFilterForm(forms.Form):
    error_type = forms.ChoiceField(
        choices=[(None, '-- Semua Tipe Error --')] + list(ErrorLog.ERROR_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'})
    )
    resolved = forms.TypedChoiceField(
        choices=[(None, '-- Semua Status --'), ('True', 'Resolved'), ('False', 'Unresolved')],
        required=False,
        coerce=lambda x: {'True': True, 'False': False}.get(x),
        empty_value=None,
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white'})
    )

class ChatAttachmentForm(forms.ModelForm):
    class Meta:
        model = ChatAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'hidden', 'id': 'file-upload'}),
        }
        labels = {
            'file': '',
        }