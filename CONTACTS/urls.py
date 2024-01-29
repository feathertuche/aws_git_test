from django.urls import path
from .views import MergeContactsList, MergeContactDetails

urlpatterns = [
    path('contact/', MergeContactsList.as_view(), name='contact'),
    path('contactinfo/<str:id>', MergeContactDetails.as_view(), name='contactinfo'),
]