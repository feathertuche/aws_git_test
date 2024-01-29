from django.urls import path
from .views import LinkToken

urlpatterns = [
    path('linktoken/', LinkToken.as_view(), name='linktoken'),
    path('webhook/', LinkToken.webhook_handler, name='webhook_handler')
]
