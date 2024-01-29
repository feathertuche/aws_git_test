from django.urls import path
from .views import mergeTaxRatesList, mergeTaxRatesInfo

urlpatterns = [
    path('taxList/', mergeTaxRatesList.as_view(), name='taxList'),
    path('taxDetails/<str:id>', mergeTaxRatesInfo.as_view(), name='taxDetails'),
]