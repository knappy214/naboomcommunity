from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
def test_jwt_auth(request):
    """Test endpoint to verify JWT authentication."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'error': 'No Bearer token found',
            'auth_header': auth_header
        })
    
    token = auth_header.split(' ')[1]
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        
        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'token': token[:50] + '...' if len(token) > 50 else token
        })
