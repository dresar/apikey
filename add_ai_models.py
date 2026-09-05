from django.core.wsgi import get_wsgi_application
import os
import sys

# Mengatur environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apitestai.settings')
application = get_wsgi_application()

# Sekarang kita bisa mengimpor model Django
from apikeys.models import ApiProvider, AIModel

def add_models():
    # Mendapatkan semua provider
    providers = ApiProvider.objects.all()
    print(f"Total providers: {providers.count()}")
    
    # Daftar model untuk setiap provider
    models_by_provider = {
        'OpenAI': [
            {'name': 'GPT-3.5 Turbo', 'model_id': 'gpt-3.5-turbo'},
            {'name': 'GPT-4', 'model_id': 'gpt-4'},
            {'name': 'GPT-4 Turbo', 'model_id': 'gpt-4-turbo'},
        ],
        'Google Gemini': [
            {'name': 'Gemini 2.5 Pro', 'model_id': 'gemini-2.5-pro'},
            {'name': 'Gemini 2.5 Flash', 'model_id': 'gemini-2.5-flash'},
            {'name': 'Gemini 2.5 Flash-Lite', 'model_id': 'gemini-2.5-flash-lite'},
            {'name': 'Gemini Live', 'model_id': 'gemini-live'},
            {'name': 'Imagen 3', 'model_id': 'imagen-3.0-generate-001'},

        ],
        'Groq': [
            {'name': 'LLaMA 3 8B', 'model_id': 'llama3-8b-8192'},
            {'name': 'LLaMA 3 70B', 'model_id': 'llama3-70b-8192'},
            {'name': 'Mixtral 8x7B', 'model_id': 'mixtral-8x7b-32768'},
        ],
        'Anthropic Claude': [
            {'name': 'Claude 3 Opus', 'model_id': 'claude-3-opus-20240229'},
            {'name': 'Claude 3 Sonnet', 'model_id': 'claude-3-sonnet-20240229'},
            {'name': 'Claude 3 Haiku', 'model_id': 'claude-3-haiku-20240307'},
        ],
        'Mistral AI': [
            {'name': 'Mistral Small', 'model_id': 'mistral-small-latest'},
            {'name': 'Mistral Medium', 'model_id': 'mistral-medium-latest'},
            {'name': 'Mistral Large', 'model_id': 'mistral-large-latest'},
        ],
        'Cohere': [
            {'name': 'Command', 'model_id': 'command'},
            {'name': 'Command Light', 'model_id': 'command-light'},
            {'name': 'Command R', 'model_id': 'command-r'},
        ],
        'Perplexity': [
            {'name': 'Perplexity Online', 'model_id': 'pplx-online'},
            {'name': 'Perplexity 70B', 'model_id': 'pplx-70b-online'},
            {'name': 'Perplexity 7B', 'model_id': 'pplx-7b-online'},
        ],
    }
    
    # Tambahkan model untuk setiap provider
    for provider in providers:
        print(f"Processing provider: {provider.name}")
        
        # Cek apakah provider ada di daftar model
        if provider.name in models_by_provider:
            models = models_by_provider[provider.name]
            
            for model_data in models:
                # Cek apakah model sudah ada
                existing_model = AIModel.objects.filter(
                    provider=provider,
                    model_id=model_data['model_id']
                ).first()
                
                if not existing_model:
                    # Buat model baru
                    model = AIModel(
                        provider=provider,
                        name=model_data['name'],
                        model_id=model_data['model_id'],
                        is_active=True,
                        capabilities={}
                    )
                    model.save()
                    print(f"  - Added model: {model.name}")
                else:
                    print(f"  - Model already exists: {existing_model.name}")
        else:
            print(f"  - No models defined for {provider.name}")

if __name__ == "__main__":
    add_models()
    print("Done adding AI models.")