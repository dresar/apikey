# API Test AI

Aplikasi untuk menguji API dengan bantuan AI. Mendukung berbagai provider AI seperti Google Gemini, OpenAI, Groq, Anthropic Claude, Mistral AI, Cohere, dan Perplexity.

## Konfigurasi Google OAuth2

Untuk mengaktifkan fitur login dengan Google, Anda perlu mendapatkan Google Client ID dan Client Secret dengan mengikuti langkah-langkah berikut:

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau pilih project yang sudah ada
3. Dari menu navigasi, pilih "APIs & Services" > "Credentials"
4. Klik tombol "Create Credentials" dan pilih "OAuth client ID"
5. Pilih "Web application" sebagai Application type
6. Isi nama aplikasi pada kolom "Name"
7. Pada bagian "Authorized JavaScript origins", tambahkan URL berikut:
   - `http://localhost:8000` (untuk pengembangan lokal)
   - URL domain produksi Anda (jika ada)
8. Pada bagian "Authorized redirect URIs", tambahkan URL berikut dengan tepat (perhatikan setiap karakter):
   - `http://127.0.0.1:8000/social-auth/complete/google-oauth2/` (untuk pengembangan lokal dengan IP)
   - `http://localhost:8000/social-auth/complete/google-oauth2/` (untuk pengembangan lokal dengan localhost)
   - `https://yourdomain.com/social-auth/complete/google-oauth2/` (untuk produksi, ganti dengan domain Anda)
9. Klik "Create"
10. Salin "Client ID" dan "Client Secret" yang dihasilkan

## Konfigurasi .env

Setelah mendapatkan Google Client ID dan Client Secret, tambahkan ke file `.env` di root project:

```
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret
```

Ganti `your_google_client_id` dan `your_google_client_secret` dengan nilai yang Anda dapatkan dari Google Cloud Console.

## Mengatasi Error "redirect_uri_mismatch"

Jika Anda mendapatkan error "redirect_uri_mismatch" saat login dengan Google, pastikan:

1. URL redirect yang dikonfigurasi di Google Cloud Console **persis sama** dengan URL yang digunakan aplikasi
2. Perhatikan penggunaan `localhost` vs `127.0.0.1` - keduanya dianggap berbeda oleh Google OAuth
3. Pastikan tidak ada trailing slash tambahan atau karakter yang berbeda
4. Tambahkan kedua URL berikut di Google Cloud Console:
   - `http://127.0.0.1:8000/social-auth/complete/google-oauth2/`
   - `http://localhost:8000/social-auth/complete/google-oauth2/`
5. Jika menggunakan port yang berbeda (bukan 8000), sesuaikan URL redirect

## Menjalankan Aplikasi

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Jalankan migrasi database:
   ```
   python manage.py migrate
   ```

3. Jalankan server development:
   ```
   python manage.py runserver
    ```

4. Buka browser dan akses `http://localhost:8000`

## Provider AI yang Didukung

Aplikasi ini mendukung berbagai provider AI dengan kemampuan yang berbeda-beda:

### Google Gemini
- **Model**: Gemini 2.5 Pro, Gemini 1.5 Pro, Gemini Pro
- **Cara Mendapatkan API Key**: Kunjungi [Google AI Studio](https://aistudio.google.com/), buat akun dan dapatkan API key gratis
- **Dokumentasi**: [Google AI Documentation](https://ai.google.dev/docs)

### OpenAI
- **Model**: GPT-4o, GPT-4, GPT-3.5 Turbo
- **Cara Mendapatkan API Key**: Daftar di [OpenAI Platform](https://platform.openai.com/), dapatkan API key dengan kredit gratis untuk pengguna baru
- **Dokumentasi**: [OpenAI Documentation](https://platform.openai.com/docs)

### Groq
- **Model**: Llama 3 70B, Llama 3 8B, Mixtral
- **Cara Mendapatkan API Key**: Daftar di [Groq Console](https://console.groq.com/) dan dapatkan API key gratis
- **Dokumentasi**: [Groq Documentation](https://console.groq.com/docs)

### Anthropic Claude
- **Model**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Cara Mendapatkan API Key**: Daftar di [Anthropic Console](https://console.anthropic.com/) dan dapatkan API key dengan kredit gratis
- **Dokumentasi**: [Claude Documentation](https://docs.anthropic.com/claude/docs)

### Mistral AI
- **Model**: Mistral Large, Mistral Medium, Mistral Small
- **Cara Mendapatkan API Key**: Daftar di [Mistral AI Console](https://console.mistral.ai/) dan dapatkan API key gratis
- **Dokumentasi**: [Mistral AI Documentation](https://docs.mistral.ai/)

### Cohere
- **Model**: Command, Command Light, Embed
- **Cara Mendapatkan API Key**: Daftar di [Cohere Dashboard](https://dashboard.cohere.com/) dan dapatkan API key gratis
- **Dokumentasi**: [Cohere Documentation](https://docs.cohere.com/)

### Perplexity
- **Model**: Sonar Medium Online, Sonar Small Online
- **Cara Mendapatkan API Key**: Daftar di [Perplexity AI](https://www.perplexity.ai/) dan dapatkan API key dengan paket berbayar
- **Dokumentasi**: [Perplexity Documentation](https://docs.perplexity.ai/)