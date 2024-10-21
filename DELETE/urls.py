from django.urls import path

from .views import DeleteAccount

urlpatterns = [
    path("deleteusr/", DeleteAccount.as_view(), name="deleteusr"),
]
