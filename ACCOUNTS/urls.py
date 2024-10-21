from django.urls import path
from .views import MergeAccounts, InsertAccountData

urlpatterns = [
    path("accounts/", MergeAccounts.as_view(), name="accounts"),
    path(
        "accounts/bulk-insert/",
        InsertAccountData.as_view(),
        name="accounts/bulk-insert/",
    ),
]
