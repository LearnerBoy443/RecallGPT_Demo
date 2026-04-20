from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('auth/me/', views.get_me, name='get_me'),
    path('auth/login/', csrf_exempt(views.login), name='login'),
    path('auth/logout/', csrf_exempt(views.logout), name='logout'),
    path('sessions/', csrf_exempt(views.handle_sessions), name='sessions'),
    path('sessions/<int:session_id>/messages/', views.get_messages, name='get_messages'),
    path('chat/', csrf_exempt(views.chat), name='chat'),
]
