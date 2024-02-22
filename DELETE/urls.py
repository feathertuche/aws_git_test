from django.urls import path
from .views import deleteAccount

urlpatterns = [
    path('deleteusr/', deleteAccount.as_view(), name='deleteusr'),
]