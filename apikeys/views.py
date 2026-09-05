from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time
import json
import os
import requests
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
import anthropic
import cohere
from .models import ApiKey, ApiProvider, AIModel, ApiTest, ErrorLog, ChatSession, ChatMessage, ChatAttachment
from .forms import UserRegisterForm, UserLoginForm, ApiKeyForm, ApiTestForm, ChatMessageForm, ChatSessionForm, ErrorLogFilterForm
from google.genai import types

# Helper functions
def get_ai_response(api_key, message_history):
    """Helper function to get AI response from different providers"""
    try:
        provider_name = api_key.provider.name.lower()
        
        if 'openai' in provider_name:
            client = OpenAI(api_key=api_key.key_value)
            response = client.chat.completions.create(
                model="gpt-4o",  # Menggunakan model terbaru
                messages=message_history
            )
            return response.choices[0].message.content, None
            
        elif 'gemini' in provider_name:
            genai.configure(api_key=api_key.key_value)
            # Try available Gemini models in order of preference
            model = None
            available_models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-pro', 'gemini-1.5-flash']
            for model_name in available_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception:
                    continue
            
            if not model:
                raise Exception("No available Gemini model found")
            
            # Format pesan untuk Gemini
            gemini_messages = []
            for msg in message_history:
                if msg["role"] == "user":
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_messages.append({"role": "model", "parts": [msg["content"]]})
            
            response = model.generate_content(gemini_messages)
            
            # Handle different response formats from Gemini
            if hasattr(response, 'text') and response.text:
                ai_response = response.text
            elif hasattr(response, 'parts') and response.parts:
                ai_response = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'candidates') and response.candidates:
                # Handle candidates format
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    ai_response = ''.join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                else:
                    ai_response = str(candidate)
            else:
                # Fallback: convert response to string
                ai_response = str(response) if response else "No response generated"
            
            return ai_response, None
            
        elif 'groq' in provider_name:
            client = Groq(api_key=api_key.key_value)
            response = client.chat.completions.create(
                model="llama3-70b-8192",  # Menggunakan model terbaru
                messages=message_history
            )
            return response.choices[0].message.content, None
            
        elif 'claude' in provider_name or 'anthropic' in provider_name:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key.key_value)
            
            # Konversi format pesan untuk Claude
            claude_messages = []
            for msg in message_history:
                claude_messages.append({"role": msg["role"], "content": msg["content"]})
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Menggunakan model terbaru
                messages=claude_messages
            )
            return response.content[0].text, None
            
        elif 'mistral' in provider_name:
            from mistralai.client import MistralClient
            
            client = MistralClient(api_key=api_key.key_value)
            
            # Menggunakan format pesan yang sama dengan OpenAI
            response = client.chat(
                model="mistral-large-latest",
                messages=message_history
            )
            return response.choices[0].message.content, None
            
        elif 'cohere' in provider_name:
            import cohere
            client = cohere.Client(api_key=api_key.key_value)
            
            # Konversi format pesan untuk Cohere
            chat_history = []
            for i in range(0, len(message_history)-1, 2):
                if i+1 < len(message_history):
                    chat_history.append({"user_name": "User", "text": message_history[i]["content"]})
                    chat_history.append({"user_name": "Assistant", "text": message_history[i+1]["content"]})
            
            response = client.chat(
                message=message_history[-1]["content"],
                chat_history=chat_history,
                model="command"
            )
            return response.text, None
            
        elif 'perplexity' in provider_name:
            client = OpenAI(api_key=api_key.key_value, base_url="https://api.perplexity.ai")
            response = client.chat.completions.create(
                model="sonar-medium-online",
                messages=message_history
            )
            return response.choices[0].message.content, None
            
        else:
            return None, (f"Provider {provider_name} tidak didukung", 'API_ERROR')
    except Exception as e:
        error_type = 'API_ERROR'
        if 'rate limit' in str(e).lower() or 'quota' in str(e).lower():
            error_type = 'RATE_LIMIT_ERROR'
        elif 'authentication' in str(e).lower() or 'invalid api key' in str(e).lower():
            error_type = 'AUTH_ERROR'
        elif 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            error_type = 'CONNECTION_ERROR'
        
        return None, (str(e), error_type)

# View functions
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Akun berhasil dibuat! Anda telah masuk.')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'auth/register.html', {'form': form})

@login_required
def dashboard(request):
    api_keys = ApiKey.objects.filter(user=request.user)
    api_tests = ApiTest.objects.filter(api_key__user=request.user).order_by('-test_date')[:10]
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:5]
    error_logs = ErrorLog.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    # Tambahkan statistik untuk dashboard
    valid_keys_count = api_keys.filter(is_valid=True).count()
    total_tests_count = ApiTest.objects.filter(api_key__user=request.user).count()
    unresolved_errors_count = ErrorLog.objects.filter(user=request.user, resolved=False).count()
    
    context = {
        'api_keys': api_keys,
        'api_tests': api_tests,
        'chat_sessions': chat_sessions,
        'error_logs': error_logs,
        'valid_keys_count': valid_keys_count,
        'total_tests_count': total_tests_count,
        'unresolved_errors_count': unresolved_errors_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def api_key_list(request):
    api_keys = ApiKey.objects.filter(user=request.user)
    form = ApiKeyForm(user=request.user)
    return render(request, 'api_keys/api_key_modal.html', {'api_keys': api_keys, 'form': form})

@login_required
def api_key_create(request):
    if request.method == 'POST':
        form = ApiKeyForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'API Key berhasil ditambahkan!')
            return redirect('api_key_list')
    else:
        # Jika bukan POST, kita tidak perlu render form terpisah karena sudah ada di modal
        return redirect('api_key_list')

@login_required
def api_key_update(request, pk):
    api_key = get_object_or_404(ApiKey, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ApiKeyForm(request.POST, instance=api_key, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'API Key berhasil diperbarui!')
            return redirect('api_key_list')
        else:
            messages.error(request, 'Terjadi kesalahan dalam memperbarui API Key!')
            return redirect('api_key_list')
    else:
        # Jika bukan POST, kita tidak perlu render form terpisah karena sudah ada di modal
        return redirect('api_key_list')

@login_required
def api_key_delete(request, pk):
    api_key = get_object_or_404(ApiKey, pk=pk, user=request.user)
    
    if request.method == 'POST':
        api_key.delete()
        messages.success(request, 'API Key berhasil dihapus!')
        return redirect('api_key_list')
    else:
        # Jika bukan POST, kita tidak perlu render halaman konfirmasi terpisah karena sudah ada di modal
        return redirect('api_key_list')

@login_required
def test_api_key(request, pk):
    api_key = get_object_or_404(ApiKey, pk=pk, user=request.user)
    provider = api_key.provider
    
    # Buat objek test baru
    api_test = ApiTest(api_key=api_key)
    
    start_time = time.time()
    success = False
    response_data = None
    error_message = None
    
    try:
        # Tes API berdasarkan provider
        if 'gemini' in provider.name.lower():
            # Tes Gemini API
            genai.configure(api_key=api_key.key_value)
            # Try available Gemini 2.5 models first
            model = None
            available_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro']
            for model_name in available_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception:
                    continue
            
            if not model:
                raise Exception("No available Gemini model found")
                
            response = model.generate_content('Hello, this is a test message to verify the API key.')
            
            # Handle different response formats from Gemini
            ai_response = None
            if hasattr(response, 'text') and response.text:
                ai_response = response.text
            elif hasattr(response, 'parts') and response.parts:
                ai_response = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'candidates') and response.candidates:
                # Handle candidates format
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    ai_response = ''.join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                else:
                    ai_response = str(candidate)
            else:
                # Fallback: convert response to string
                ai_response = str(response) if response else "No response generated"
            
            if ai_response:
                success = True
                response_data = {'response': ai_response}
            else:
                raise Exception("No valid response received from Gemini API")
            
        elif 'groq' in provider.name.lower():
            # Tes Groq API
            client = Groq(api_key=api_key.key_value)
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a test message to verify the API key."}
                ]
            )
            success = True
            response_data = {'response': completion.choices[0].message.content}
            
        elif 'openai' in provider.name.lower():
            # Tes OpenAI API
            client = OpenAI(api_key=api_key.key_value)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a test message to verify the API key."}
                ]
            )
            success = True
            response_data = {'response': completion.choices[0].message.content}
            
        elif 'claude' in provider.name.lower() or 'anthropic' in provider.name.lower():
            # Tes Claude API
            client = anthropic.Anthropic(api_key=api_key.key_value)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message to verify the API key."}
                ]
            )
            success = True
            response_data = {'response': message.content[0].text}
            
        elif 'mistral' in provider.name.lower():
            # Tes Mistral API
            from mistralai.client import MistralClient
            client = MistralClient(api_key=api_key.key_value)
            response = client.chat(
                model="mistral-small-latest",
                messages=[
                    {"role": "user", "content": "Hello, this is a test message to verify the API key."}
                ]
            )
            success = True
            response_data = {'response': response.choices[0].message.content}
            
        elif 'cohere' in provider.name.lower():
            # Tes Cohere API
            client = cohere.Client(api_key=api_key.key_value)
            response = client.chat(
                message="Hello, this is a test message to verify the API key.",
                model="command"
            )
            success = True
            response_data = {'response': response.text}
            
        elif 'perplexity' in provider.name.lower():
            # Tes Perplexity API
            client = OpenAI(api_key=api_key.key_value, base_url="https://api.perplexity.ai")
            response = client.chat.completions.create(
                model="sonar-small-online",
                messages=[
                    {"role": "user", "content": "Hello, this is a test message to verify the API key."}
                ]
            )
            success = True
            response_data = {'response': response.choices[0].message.content}
            
        else:
            # Provider tidak dikenal
            error_message = f"Provider {provider.name} tidak didukung untuk pengujian."
    
    except Exception as e:
        error_message = str(e)
    
    # Hitung waktu respons
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # konversi ke ms
    
    # Update objek test
    api_test.status = 'success' if success else 'failed'
    api_test.response_time = response_time
    api_test.response_data = response_data
    api_test.error_message = error_message
    api_test.save()
    
    # Update status API key
    api_key.is_valid = success
    api_key.last_tested = timezone.now()
    api_key.status = 'active' if success else 'expired'
    api_key.save()
    
    if success:
        messages.success(request, f'API Key berhasil diuji dan valid! Waktu respons: {response_time:.2f} ms')
    else:
        messages.error(request, f'API Key tidak valid. Error: {error_message}')
    
    return redirect('api_key_list')

@login_required
def api_test_history(request, api_key_id):
    api_key = get_object_or_404(ApiKey, pk=api_key_id, user=request.user)
    tests = ApiTest.objects.filter(api_key=api_key).order_by('-test_date')
    
    # Pagination
    paginator = Paginator(tests, 10)  # 10 tests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'api_keys/api_test_history.html', {
        'api_key': api_key,
        'tests': page_obj
    })

@login_required
def bulk_create_api_keys(request, provider_name):
    provider = get_object_or_404(ApiProvider, name__icontains=provider_name)
    
    if request.method == 'POST':
        num_keys = int(request.POST.get('num_keys', 1))
        base_name = request.POST.get('base_name', 'API Key')
        key_value = request.POST.get('key_value', '')
        
        if num_keys > 0 and key_value:
            created_count = 0
            for i in range(1, num_keys + 1):
                key_name = f"{base_name} {i}"
                
                # Cek apakah kombinasi user-provider-key_name sudah ada
                if not ApiKey.objects.filter(user=request.user, provider=provider, key_name=key_name).exists():
                    ApiKey.objects.create(
                        user=request.user,
                        provider=provider,
                        key_name=key_name,
                        key_value=key_value,
                        status='testing',
                        notes=f"Dibuat secara massal pada {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Berhasil membuat {created_count} API Key baru untuk {provider.name}')
            else:
                messages.warning(request, f'Tidak ada API Key baru yang dibuat. Kemungkinan nama key sudah ada.')
        else:
            messages.error(request, 'Jumlah key harus lebih dari 0 dan nilai key harus diisi.')
        
        return redirect('api_key_list')
    
    return render(request, 'api_keys/bulk_create_api_keys.html', {
        'provider': provider
    })

@login_required
def chat_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    # Get valid API keys for the user
    api_keys = ApiKey.objects.filter(user=request.user, is_valid=True)
    
    # Pagination
    paginator = Paginator(sessions, 10)  # 10 sessions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'chat/chat_sessions.html', {
        'sessions': page_obj,
        'api_keys': api_keys
    })

@login_required
def new_chat_session(request):
    if request.method == 'POST':
        form = ChatSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('chat_detail', session_id=session.id)
        else:
            # Jika form tidak valid, kembali ke halaman chat_sessions dengan pesan error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('chat_sessions')
    else:
        # Jika bukan POST request, redirect ke halaman chat_sessions
        return redirect('chat_sessions')

@login_required
def get_models_for_key(request, key_id):
    """API endpoint untuk mendapatkan model AI berdasarkan API key"""
    try:
        api_key = ApiKey.objects.get(id=key_id, user=request.user)
        models = AIModel.objects.filter(provider=api_key.provider, is_active=True)
        
        models_data = [{
            'id': model.id,
            'name': model.name
        } for model in models]
        
        return JsonResponse({'models': models_data})
    except ApiKey.DoesNotExist:
        return JsonResponse({'error': 'API key not found'}, status=404)

def get_ai_response(session, messages):
    """Helper function to get AI response based on provider and model"""
    ai_response = None
    error = None
    
    try:
        provider_name = session.api_key.provider.name.lower()
        api_key_value = session.api_key.key_value
        
        # Get model ID from session or use default
        model_id = None
        if session.ai_model:
            model_id = session.ai_model.model_id
        
        if 'gemini' in provider_name:
            genai.configure(api_key=api_key_value)
            # Use selected model or default to gemini-2.5-flash
            model_name = model_id or 'gemini-2.5-flash'
            try:
                model = genai.GenerativeModel(model_name)
            except Exception as e:
                # Fallback to other available models
                fallback_models = ['gemini-2.5-pro', 'gemini-2.5-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro']
                model = None
                for fallback_model in fallback_models:
                    try:
                        model = genai.GenerativeModel(fallback_model)
                        break
                    except Exception:
                        continue
                if not model:
                    raise Exception(f"No available Gemini model found. Last error: {str(e)}")
            
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                if msg['role'] == 'user':
                    gemini_messages.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    gemini_messages.append(f"Assistant: {msg['content']}")
            
            # Join all messages into a single prompt
            prompt = "\n".join(gemini_messages)
            if not prompt.strip():
                prompt = messages[-1]['content'] if messages else "Hello"
            
            response = model.generate_content(prompt)
            
            # Handle different response formats from Gemini
            if hasattr(response, 'text') and response.text:
                ai_response = response.text
            elif hasattr(response, 'parts') and response.parts:
                ai_response = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'candidates') and response.candidates:
                # Handle candidates format
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    ai_response = ''.join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                else:
                    ai_response = str(candidate)
            else:
                # Fallback: convert response to string
                ai_response = str(response) if response else "No response generated"
        
        elif provider_name == 'groq':
            client = Groq(api_key=api_key_value)
            # Use selected model or default to llama3-70b-8192
            model_name = model_id or "llama3-70b-8192"
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages
            )
            ai_response = completion.choices[0].message.content
        
        elif provider_name == 'openai':
            headers = {
                'Authorization': f'Bearer {api_key_value}',
                'Content-Type': 'application/json'
            }
            # Use selected model or default to gpt-3.5-turbo
            model_name = model_id or 'gpt-3.5-turbo'
            data = {
                'model': model_name,
                'messages': messages
            }
            response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
            response.raise_for_status()
            ai_response = response.json()['choices'][0]['message']['content']
        
        return ai_response, None
    except Exception as e:
        error_message = str(e)
        error_type = 'api_error'
        
        if 'rate limit' in error_message.lower():
            error_type = 'rate_limit'
        elif 'authentication' in error_message.lower() or 'unauthorized' in error_message.lower():
            error_type = 'authentication'
        elif 'timeout' in error_message.lower():
            error_type = 'timeout'
        elif 'server error' in error_message.lower() or '5' in error_message[:3]:
            error_type = 'server_error'
        
        return None, (error_message, error_type)

@login_required
def chat_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages_list = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    if request.method == 'POST':
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            # Simpan pesan pengguna
            user_message = form.save(commit=False)
            user_message.user = request.user
            user_message.api_key = session.api_key
            user_message.role = 'user'
            user_message.save()
            # Tambahkan pesan ke session menggunakan add() untuk many-to-many field
            session.messages.add(user_message)
            
            # Proses file yang diunggah (jika ada)
            if 'attachment' in request.FILES:
                uploaded_file = request.FILES['attachment']
                # Simpan file attachment
                attachment = ChatAttachment.objects.create(
                    user=request.user,
                    chat_message=user_message,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                    file_size=uploaded_file.size,
                    file_type=uploaded_file.content_type
                )
                # Tambahkan informasi file ke konten pesan
                file_info = f"\n[File: {uploaded_file.name} ({attachment.get_file_size_display()})]"
                user_message.content += file_info
                user_message.save()
            
            # Process the message with AI
            try:
                # Get previous messages for context (limit to last 10)
                prev_messages = messages_list.order_by('-timestamp')[:10][::-1]
                
                # Format messages for AI
                message_history = []
                for msg in prev_messages:
                    message_history.append({"role": msg.role, "content": msg.content})
                
                # Add the latest user message
                message_history.append({"role": "user", "content": user_message.content})
                
                # Get AI response using helper function
                ai_response, error = get_ai_response(session, message_history)
                
                # Save AI response
                if ai_response:
                    ai_message = ChatMessage.objects.create(
                        user=request.user,
                        api_key=session.api_key,
                        role='assistant',
                        content=ai_response
                    )
                    # Tambahkan pesan AI ke session menggunakan add() untuk many-to-many field
                    session.messages.add(ai_message)
                    
                    # Update session timestamp
                    session.updated_at = timezone.now()
                    session.save()
                else:
                    # Handle error
                    error_message, error_type = error
                    
                    # Log error
                    ErrorLog.objects.create(
                        user=request.user,
                        api_key=session.api_key,
                        error_type=error_type,
                        error_message=error_message,
                        error_details={'session_id': session.id}
                    )
                    
                    # Create system message about error
                    system_message = ChatMessage.objects.create(
                        user=request.user,
                        api_key=session.api_key,
                        role='system',
                        content=f"Error: {error_message}"
                    )
                    # Tambahkan pesan sistem ke session menggunakan add() untuk many-to-many field
                    session.messages.add(system_message)
            
            except Exception as e:
                error_message = str(e)
                error_type = 'api_error'
                
                # Log error
                ErrorLog.objects.create(
                    user=request.user,
                    api_key=session.api_key,
                    error_type=error_type,
                    error_message=error_message,
                    error_details={'session_id': session.id}
                )
                
                # Create system message about error
                system_message = ChatMessage.objects.create(
                    user=request.user,
                    api_key=session.api_key,
                    role='system',
                    content=f"Error: {error_message}"
                )
                # Tambahkan pesan sistem ke session menggunakan add() untuk many-to-many field
                session.messages.add(system_message)
            
            return redirect('chat_detail', session_id=session.id)
    else:
        form = ChatMessageForm()
    
    return render(request, 'chat/chat_detail.html', {
        'session': session,
        'messages': messages_list,
        'form': form
    })

@login_required
def delete_chat_session(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Sesi chat berhasil dihapus.')
        return redirect('chat_sessions')
    
    # Jika bukan POST, redirect ke chat_sessions
    return redirect('chat_sessions')

@login_required
def error_logs(request):
    error_logs = ErrorLog.objects.filter(user=request.user).order_by('-timestamp')
    
    # Filter berdasarkan form
    filter_form = ErrorLogFilterForm(request.GET)
    if filter_form.is_valid():
        error_type = filter_form.cleaned_data.get('error_type')
        resolved = filter_form.cleaned_data.get('resolved')
        api_key = filter_form.cleaned_data.get('api_key')
        
        if error_type:
            error_logs = error_logs.filter(error_type=error_type)
        
        if resolved is not None:
            error_logs = error_logs.filter(resolved=resolved)
        
        if api_key:
            error_logs = error_logs.filter(api_key=api_key)
    
    # Pagination
    paginator = Paginator(error_logs, 20)  # 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'errors/error_logs.html', {
        'error_logs': page_obj,
        'filter_form': filter_form
    })

@login_required
def resolve_error(request, pk):
    error_log = get_object_or_404(ErrorLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes', '')
        error_log.resolved = True
        error_log.resolution_notes = resolution_notes
        error_log.save()
        
        messages.success(request, 'Error berhasil ditandai sebagai resolved.')
        return redirect('error_logs')
    
    return render(request, 'errors/resolve_error.html', {
        'error_log': error_log
    })

@login_required
def delete_error(request, pk):
    error_log = get_object_or_404(ErrorLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        error_log.delete()
        messages.success(request, 'Log error berhasil dihapus.')
        return redirect('error_logs')
    
    return render(request, 'errors/delete_error.html', {
        'error_log': error_log
    })

@login_required
def view_attachment(request, attachment_id):
    """View untuk menampilkan file attachment"""
    attachment = get_object_or_404(ChatAttachment, pk=attachment_id, user=request.user)
    
    # Buka file
    try:
        file_content = attachment.file.read()
        content_type = attachment.file_type or 'application/octet-stream'
        
        # Untuk gambar, tampilkan langsung
        if content_type.startswith('image/'):
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{attachment.file_name}"'
            return response
        
        # Untuk text files, tampilkan sebagai text
        elif content_type.startswith('text/') or content_type in ['application/json', 'application/xml']:
            try:
                text_content = file_content.decode('utf-8')
                return HttpResponse(f'<pre>{text_content}</pre>', content_type='text/html')
            except UnicodeDecodeError:
                # Jika tidak bisa decode sebagai text, download saja
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
                return response
        
        # Untuk file lainnya, download
        else:
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
            return response
            
    except Exception as e:
        messages.error(request, f'Error membuka file: {str(e)}')
        return redirect('chat_detail', session_id=attachment.chat_message.chatsession_set.first().id)

@login_required
def profile(request):
    """View untuk menampilkan dan mengedit profil pengguna"""
    user = request.user
    
    if request.method == 'POST':
        # Update profil pengguna
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        messages.success(request, 'Profil berhasil diperbarui!')
        return redirect('profile')
    
    # Ambil foto profil dari Google jika tersedia
    google_photo_url = None
    try:
        from social_django.models import UserSocialAuth
        google_social = UserSocialAuth.objects.filter(user=user, provider='google-oauth2').first()
        if google_social and google_social.extra_data:
            google_photo_url = google_social.extra_data.get('picture')
    except ImportError:
        pass
    
    context = {
        'user': user,
        'google_photo_url': google_photo_url,
    }
    
    return render(request, 'auth/profile.html', context)


@login_required
def analytics(request):
    """View untuk halaman analitik"""
    user = request.user
    
    # Data untuk grafik dan statistik
    api_keys = ApiKey.objects.filter(user=user)
    chat_sessions = ChatSession.objects.filter(user=user)
    api_tests = ApiTest.objects.filter(api_key__user=user)
    error_logs = ErrorLog.objects.filter(user=user)
    
    # Statistik per provider
    provider_stats = api_keys.values('provider__name').annotate(
        count=Count('id'),
        tests_count=Count('tests')
    ).order_by('-count')
    
    # Statistik per model (dari chat sessions)
    model_stats = chat_sessions.filter(ai_model__isnull=False).values('ai_model__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Statistik chat per bulan (6 bulan terakhir)
    from datetime import datetime, timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_chats = chat_sessions.filter(
        created_at__gte=six_months_ago
    ).extra(
        select={'month': "strftime('%%Y-%%m', created_at)"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Error rate
    total_tests = api_tests.count()
    failed_tests = error_logs.count()
    success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
    
    context = {
        'total_api_keys': api_keys.count(),
        'total_chat_sessions': chat_sessions.count(),
        'total_api_tests': total_tests,
        'total_errors': failed_tests,
        'success_rate': round(success_rate, 2),
        'provider_stats': provider_stats,
        'model_stats': model_stats,
        'monthly_chats': list(monthly_chats),
    }
    
    return render(request, 'analytics/analytics.html', context)


@login_required
def health_check(request):
    """View untuk halaman tes kesehatan sistem"""
    user = request.user
    health_status = []
    overall_status = 'healthy'
    
    # Cek koneksi database
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status.append({
            'component': 'Database',
            'status': 'healthy',
            'message': 'Koneksi database normal',
            'icon': 'fa-database',
            'color': 'green'
        })
    except Exception as e:
        health_status.append({
            'component': 'Database',
            'status': 'error',
            'message': f'Error koneksi database: {str(e)}',
            'icon': 'fa-database',
            'color': 'red'
        })
        overall_status = 'error'
    
    # Cek API Keys yang aktif
    active_keys = ApiKey.objects.filter(user=user, is_valid=True).count()
    total_keys = ApiKey.objects.filter(user=user).count()
    
    if total_keys == 0:
        health_status.append({
            'component': 'API Keys',
            'status': 'warning',
            'message': 'Tidak ada API Key yang terdaftar',
            'icon': 'fa-key',
            'color': 'yellow'
        })
        if overall_status == 'healthy':
            overall_status = 'warning'
    elif active_keys == 0:
        health_status.append({
            'component': 'API Keys',
            'status': 'warning',
            'message': f'{total_keys} API Key terdaftar, tetapi tidak ada yang aktif',
            'icon': 'fa-key',
            'color': 'yellow'
        })
        if overall_status == 'healthy':
            overall_status = 'warning'
    else:
        health_status.append({
            'component': 'API Keys',
            'status': 'healthy',
            'message': f'{active_keys} dari {total_keys} API Key aktif',
            'icon': 'fa-key',
            'color': 'green'
        })
    
    # Cek error rate dalam 24 jam terakhir
    from datetime import timedelta
    yesterday = timezone.now() - timedelta(days=1)
    recent_errors = ErrorLog.objects.filter(user=user, timestamp__gte=yesterday).count()
    recent_tests = ApiTest.objects.filter(api_key__user=user, test_date__gte=yesterday).count()
    
    if recent_tests == 0:
        health_status.append({
            'component': 'API Tests',
            'status': 'info',
            'message': 'Tidak ada tes API dalam 24 jam terakhir',
            'icon': 'fa-flask',
            'color': 'blue'
        })
    else:
        error_rate = (recent_errors / recent_tests) * 100
        if error_rate > 20:
            health_status.append({
                'component': 'API Tests',
                'status': 'error',
                'message': f'Error rate tinggi: {error_rate:.1f}% ({recent_errors}/{recent_tests})',
                'icon': 'fa-flask',
                'color': 'red'
            })
            overall_status = 'error'
        elif error_rate > 10:
            health_status.append({
                'component': 'API Tests',
                'status': 'warning',
                'message': f'Error rate sedang: {error_rate:.1f}% ({recent_errors}/{recent_tests})',
                'icon': 'fa-flask',
                'color': 'yellow'
            })
            if overall_status == 'healthy':
                overall_status = 'warning'
        else:
            health_status.append({
                'component': 'API Tests',
                'status': 'healthy',
                'message': f'Error rate rendah: {error_rate:.1f}% ({recent_errors}/{recent_tests})',
                'icon': 'fa-flask',
                'color': 'green'
            })
    
    # Cek storage/media
    try:
        import os
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            health_status.append({
                'component': 'Storage',
                'status': 'healthy',
                'message': 'Media storage dapat diakses',
                'icon': 'fa-folder',
                'color': 'green'
            })
        else:
            health_status.append({
                'component': 'Storage',
                'status': 'warning',
                'message': 'Media directory tidak ditemukan',
                'icon': 'fa-folder',
                'color': 'yellow'
            })
            if overall_status == 'healthy':
                overall_status = 'warning'
    except Exception as e:
        health_status.append({
            'component': 'Storage',
            'status': 'error',
            'message': f'Error mengakses storage: {str(e)}',
            'icon': 'fa-folder',
            'color': 'red'
        })
        overall_status = 'error'
    
    context = {
        'health_status': health_status,
        'overall_status': overall_status,
        'last_check': timezone.now(),
    }
    
    return render(request, 'health/health_check.html', context)

@login_required
def delete_api_test(request, test_id):
    """Delete a specific API test record"""
    test = get_object_or_404(ApiTest, pk=test_id, api_key__user=request.user)
    
    if request.method == 'DELETE':
        test.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_test_details(request, test_id):
    """Get detailed information about a specific API test"""
    test = get_object_or_404(ApiTest, pk=test_id, api_key__user=request.user)
    
    data = {
        'id': test.id,
        'api_key_name': test.api_key.key_name,
        'provider': test.api_key.provider.name,
        'status': test.status,
        'test_date': test.test_date.strftime('%Y-%m-%d %H:%M:%S'),
        'response_time': test.response_time,
        'request_data': test.request_data,
        'response_data': test.response_data,
        'error': test.error_message
    }
    
    return JsonResponse(data)

@login_required
def bulk_test_api_keys(request):
    """Run tests on multiple API keys"""
    if request.method == 'POST':
        api_key_ids = request.POST.getlist('api_keys')
        test_message = request.POST.get('test_message', 'Hello, this is a test message.')
        
        if not api_key_ids:
            return JsonResponse({'success': False, 'error': 'No API keys selected'})
        
        results = []
        for key_id in api_key_ids:
            try:
                api_key = get_object_or_404(ApiKey, pk=key_id, user=request.user)
                
                # Create test record
                test = ApiTest.objects.create(
                    api_key=api_key,
                    test_date=timezone.now(),
                    status='testing',
                    request_data=test_message
                )
                
                # Run the actual test
                start_time = time.time()
                try:
                    # Test the API key with the message
                    response = get_ai_response(api_key, [{'role': 'user', 'content': test_message}])
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)
                    
                    test.status = 'success'
                    test.response_time = response_time
                    test.response_data = response[:1000] if response else 'No response'
                    test.save()
                    
                    # Update API key status
                    api_key.is_valid = True
                    api_key.status = 'active'
                    api_key.last_tested = timezone.now()
                    api_key.save()
                    
                    results.append({'key': api_key.key_name, 'status': 'success'})
                    
                except Exception as e:
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)
                    
                    test.status = 'failed'
                    test.response_time = response_time
                    test.error_message = str(e)
                    test.save()
                    
                    # Update API key status
                    api_key.is_valid = False
                    api_key.status = 'expired'
                    api_key.last_tested = timezone.now()
                    api_key.save()
                    
                    results.append({'key': api_key.key_name, 'status': 'failed', 'error': str(e)})
                    
            except Exception as e:
                results.append({'key': f'Key {key_id}', 'status': 'error', 'error': str(e)})
        
        return JsonResponse({'success': True, 'results': results})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
