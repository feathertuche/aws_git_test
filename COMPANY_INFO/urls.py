from django.urls import path
from .views import MergeCompanyDetails, MergeKlooCompanyInsert, MergeCompanyInfo

urlpatterns = [
    path('companyList/', MergeCompanyInfo.as_view(), name='companyList'),
    path('syncall/<str:org_id>/<str:entity_id>/', MergeCompanyInfo.as_view(), name='syncall'),
    path('companyDetails/<str:id>', MergeCompanyDetails.as_view(), name='companyDetails'),
    path('kloo-insert/', MergeKlooCompanyInsert.as_view(), name='kloo-insert')
]
