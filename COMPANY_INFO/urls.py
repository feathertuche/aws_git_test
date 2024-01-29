from django.urls import path
from .views import MergeCompanyInfo, MergeCompanyDetails

urlpatterns = [
    path('companyList/', MergeCompanyInfo.as_view(), name='companyList'),
    path('companyDetails/<str:id>', MergeCompanyDetails.as_view(), name='companyDetails'),
]