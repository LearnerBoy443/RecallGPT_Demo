from django.contrib import admin
from django.urls import path, include
from api.views import render_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', render_index, name='index'),
    path('', include('api.urls')),
]
