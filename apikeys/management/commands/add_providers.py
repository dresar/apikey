from django.core.management.base import BaseCommand
from apikeys.models import ApiProvider

class Command(BaseCommand):
    help = 'Adds initial API providers to the database'

    def handle(self, *args, **options):
        providers = [
            {
                'name': 'Google Gemini',
                'description': 'Google Gemini API untuk model AI generatif termasuk Gemini 1.5 dan Gemini 2.5',
                'website': 'https://aistudio.google.com/',
                'documentation_url': 'https://ai.google.dev/docs',
            },
            {
                'name': 'Groq',
                'description': 'Groq API untuk inferensi cepat model LLM seperti Llama 3, Mixtral, dan Gemma',
                'website': 'https://console.groq.com/',
                'documentation_url': 'https://console.groq.com/docs',
            },
            {
                'name': 'OpenAI',
                'description': 'OpenAI API untuk model GPT-3.5, GPT-4, dan GPT-4o',
                'website': 'https://platform.openai.com/',
                'documentation_url': 'https://platform.openai.com/docs',
            },
            {
                'name': 'Anthropic Claude',
                'description': 'Anthropic Claude API untuk model Claude 3 (Haiku, Sonnet, dan Opus)',
                'website': 'https://console.anthropic.com/',
                'documentation_url': 'https://docs.anthropic.com/claude/docs',
            },
            {
                'name': 'Mistral AI',
                'description': 'Mistral AI API untuk model Mistral dan Mixtral',
                'website': 'https://console.mistral.ai/',
                'documentation_url': 'https://docs.mistral.ai/',
            },
            {
                'name': 'Cohere',
                'description': 'Cohere API untuk model Command dan Embed',
                'website': 'https://dashboard.cohere.com/',
                'documentation_url': 'https://docs.cohere.com/',
            },
            {
                'name': 'Perplexity',
                'description': 'Perplexity API untuk model online-first LLM dengan kemampuan pencarian web',
                'website': 'https://www.perplexity.ai/',
                'documentation_url': 'https://docs.perplexity.ai/',
            },
        ]

        for provider_data in providers:
            provider, created = ApiProvider.objects.get_or_create(
                name=provider_data['name'],
                defaults={
                    'description': provider_data['description'],
                    'website': provider_data['website'],
                    'documentation_url': provider_data['documentation_url'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully added provider: {provider.name}'))
            else:
                self.stdout.write(f'Provider already exists: {provider.name}')

        self.stdout.write(self.style.SUCCESS('Providers setup completed'))