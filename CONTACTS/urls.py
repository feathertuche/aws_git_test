from django.urls import path
from .views import MergeContactsList, MergeContactDetails # MergePostContacts

urlpatterns = [
    path('contact/', MergeContactsList.as_view(), name='contact'),
    path('contactinfo/<str:id>', MergeContactDetails.as_view(), name='contactinfo'),
    # path('post-contacts/', MergePostContacts.as_view(), name='post_contacts'),
]
