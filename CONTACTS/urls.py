from django.urls import path

from .views import MergePostContacts

urlpatterns = [
    path("post-contacts/", MergePostContacts.as_view(), name="post_contacts"),
]
