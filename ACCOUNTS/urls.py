from django.urls import path
from .views import MergeAccounts

urlpatterns = [
    path('accounts/', MergeAccounts.as_view(), name='accounts'),
]
