from django.urls import path
from .views import MergeTrackingCategoriesList, MergeTrackingCategoriesDetails

urlpatterns = [
    path('tracking_categories/', MergeTrackingCategoriesList.as_view(), name='tracking_category'),
    path('tracking_category/<str:id>', MergeTrackingCategoriesDetails.as_view(), name='tracking_category_id'),
]
