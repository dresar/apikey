from social_django.models import UserSocialAuth

def google_photo(request):
    """Context processor untuk menambahkan foto profil Google ke semua template"""
    google_photo_url = None
    
    if request.user.is_authenticated:
        try:
            google_social = UserSocialAuth.objects.filter(
                user=request.user, 
                provider='google-oauth2'
            ).first()
            
            if google_social and google_social.extra_data:
                google_photo_url = google_social.extra_data.get('picture')
        except Exception:
            pass
    
    return {
        'google_photo_url': google_photo_url
    }