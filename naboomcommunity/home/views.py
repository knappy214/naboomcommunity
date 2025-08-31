from django.shortcuts import render
from django.http import HttpResponse

def test_css(request):
    """Test view to verify CSS is loading properly."""
    return render(request, 'home/test_css.html')

def home_view(request):
    """Simple home view for testing."""
    return render(request, 'home/home_page.html')
