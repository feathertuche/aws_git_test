from django.urls import path
from .views import ProxySyncAPI

urlpatterns = [
    path('proxy-sync/', ProxySyncAPI.as_view(), name='proxy_sync'),
]
