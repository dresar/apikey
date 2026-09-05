# Google OAuth Setup Guide

## Masalah yang Sering Terjadi

Jika Anda mengalami error "redirect_uri_mismatch" saat login dengan Google, ikuti langkah-langkah berikut:

## 1. Konfigurasi Google Cloud Console

### Langkah 1: Buka Google Cloud Console
1. Pergi ke [Google Cloud Console](https://console.cloud.google.com/)
2. Pilih project Anda atau buat project baru

### Langkah 2: Enable Google+ API
1. Pergi ke "APIs & Services" > "Library"
2. Cari "Google+ API" dan enable
3. Cari "Google Identity" dan enable juga

### Langkah 3: Konfigurasi OAuth Consent Screen
1. Pergi ke "APIs & Services" > "OAuth consent screen"
2. Pilih "External" untuk testing
3. Isi informasi aplikasi:
   - App name: AI API Platform
   - User support email: email Anda
   - Developer contact information: email Anda
4. Tambahkan scope yang diperlukan:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`

### Langkah 4: Buat OAuth 2.0 Credentials
1. Pergi ke "APIs & Services" > "Credentials"
2. Klik "Create Credentials" > "OAuth 2.0 Client IDs"
3. Pilih "Web application"
4. Isi nama: "AI API Platform"
5. **PENTING**: Tambahkan Authorized redirect URIs:
   ```
   http://127.0.0.1:8000/social-auth/complete/google-oauth2/
   http://localhost:8000/social-auth/complete/google-oauth2/
   ```
6. Klik "Create"

### Langkah 5: Copy Credentials
1. Copy "Client ID" dan "Client Secret"
2. Paste ke file `.env`:
   ```
   SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_client_id_here
   SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_client_secret_here
   ```

## 2. Verifikasi Konfigurasi Django

Pastikan file `settings.py` memiliki konfigurasi berikut:

```python
# Google OAuth2 Settings
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://127.0.0.1:8000/social-auth/complete/google-oauth2/'

# Google OAuth2 Scope
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
```

## 3. Testing

1. Restart Django server:
   ```bash
   python manage.py runserver
   ```

2. Buka browser dan pergi ke: `http://127.0.0.1:8000/login/`

3. Klik "Continue with Google"

4. Jika masih error, periksa:
   - URL redirect di Google Console harus persis sama
   - Pastikan menggunakan `127.0.0.1` bukan `localhost`
   - Pastikan port 8000 sesuai

## 4. Troubleshooting

### Error: redirect_uri_mismatch
- Periksa kembali Authorized redirect URIs di Google Console
- Pastikan URL persis sama dengan yang dikonfigurasi
- Gunakan `127.0.0.1:8000` bukan `localhost:8000`

### Error: access_denied
- User membatalkan login
- Atau aplikasi belum diverifikasi Google

### Error: invalid_client
- Client ID atau Client Secret salah
- Periksa file `.env`

## 5. Production Setup

Untuk production, ganti:
```python
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://yourdomain.com/social-auth/complete/google-oauth2/'
```

Dan tambahkan domain production ke Authorized redirect URIs di Google Console.