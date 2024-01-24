from django.urls import path
from .views import LinkToken

urlpatterns = [
    path('linktoken/', LinkToken.as_view(), name='linktoken'),
]
