from django.urls import path

from .views import ProxySyncAPI, ProxyReSyncAPI

urlpatterns = [
    path("proxy-sync/", ProxySyncAPI.as_view(), name="proxy_sync"),
    path("proxy-resync", ProxyReSyncAPI.as_view(), name="proxy_resync"),
]
