from django.urls import path

from .views import MergeTrackingCategoriesList, MergePostTrackingCategories

urlpatterns = [
    path(
        "tracking-categories/",
        MergeTrackingCategoriesList.as_view(),
        name="tracking_category",
    ),
    path(
        "post-tracking-category/",
        MergePostTrackingCategories.as_view(),
        name="post_tracking_category",
    ),
]
