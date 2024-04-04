from django.urls import path

from .views import LinkToken, WebHook

urlpatterns = [
    path("linktoken/", LinkToken.as_view(), name="linktoken"),
    path("linktoken/webhook/", WebHook.as_view(), name="webhook_handler"),
]
