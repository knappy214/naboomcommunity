from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_GET
def block_common_attacks(request: HttpRequest) -> HttpResponse:
    """
    Block common attack patterns and return appropriate responses.
    This view should be placed at the end of URL patterns to catch
    common scanning attempts.
    """
    path = request.path.lower()
    
    # Block common attack patterns
    blocked_patterns = [
        '/.git/',
        '/.env',
        '/wp-admin/',
        '/wp-content/',
        '/wp-includes/',
        '/phpmyadmin/',
        '/adminer/',
        '/geoserver/',
        '/.svn/',
        '/.htaccess',
        '/.htpasswd',
        '/config.php',
        '/backup/',
        '/backups/',
        '/test/',
        '/debug/',
        '/api/v1/',
        '/api/v3/',
        '/api/v4/',
        '/api/v5/',
    ]
    
    for pattern in blocked_patterns:
        if pattern in path:
            return HttpResponse("Not Found", status=404)
    
    # Block requests with suspicious query parameters
    suspicious_params = [
        'cmd', 'exec', 'eval', 'system', 'shell', 'bash',
        'php', 'asp', 'jsp', 'script', 'javascript',
        'union', 'select', 'insert', 'update', 'delete',
        'drop', 'create', 'alter', 'grant', 'revoke'
    ]
    
    for param in suspicious_params:
        if param in request.GET:
            return HttpResponse("Not Found", status=404)
    
    # Default response for unmatched patterns
    return HttpResponse("Not Found", status=404)
