from django.urls import path
from .views import MergeTrackingCategoriesList, MergeTrackingCategoriesDetails, MergePostTrackingCategories

urlpatterns = [
    path('tracking-categories/', MergeTrackingCategoriesList.as_view(), name='tracking_category'),
    path('tracking_category/<str:id>', MergeTrackingCategoriesDetails.as_view(), name='tracking_category_id'),
    path('post-tracking-category/', MergePostTrackingCategories.as_view(), name='post_tracking_category'),
]
