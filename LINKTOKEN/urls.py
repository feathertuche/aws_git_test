from django.urls import path
from .views import LinkToken, webhook_handler

urlpatterns = [
    path('linktoken/', LinkToken.as_view(), name='linktoken'),
    #path('linktoken/webhook/', webhook_handler, name='webhook_handler'),
]
