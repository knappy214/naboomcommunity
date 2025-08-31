from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('test-css/', views.test_css, name='test_css'),
    path('home/', views.home_view, name='home_view'),
]
