from django.urls import path
from .views import MergeCompanyDetails, MergeKlooCompanyInsert, MergeCompanyInfo

urlpatterns = [
    path('companyList/', MergeCompanyInfo.as_view(), name='companyList'),
    path('companyDetails/<str:id>', MergeCompanyDetails.as_view(), name='companyDetails'),
    path('kloo-insert', MergeKlooCompanyInsert.as_view(), name='kloo-insert')
]
