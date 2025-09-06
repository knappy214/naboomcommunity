from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from home.models import UserProfile

User = get_user_model()

@csrf_exempt
def test_user_profiles(request):
    """Test endpoint that mimics the Wagtail API v2 ViewSet."""
    print(f"DEBUG: test_user_profiles called")
    print(f"DEBUG: Method: {request.method}")
    print(f"DEBUG: Path: {request.path}")
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    print(f"DEBUG: Authorization header: {auth_header}")
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'meta': {'total_count': 0},
            'items': [],
            'error': 'No Bearer token found'
        })
    
    token = auth_header.split(' ')[1]
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        print(f"DEBUG: Authenticated user {user.username} (ID: {user.id})")
        
        # Get or create the current user's profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        print(f"DEBUG: Profile {'created' if created else 'found'}: {profile.id}")
        
        # Create a simple response
        profile_data = {
            'id': profile.id,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': profile.phone,
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
        }
        
        return JsonResponse({
            'meta': {
                'total_count': 1
            },
            'items': [profile_data]
        })
        
    except Exception as e:
        print(f"DEBUG: Error: {e}")
        return JsonResponse({
            'meta': {'total_count': 0},
            'items': [],
            'error': str(e)
        })
