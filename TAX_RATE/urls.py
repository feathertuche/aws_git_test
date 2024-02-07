from django.urls import path
from .views import MergeTaxRatesList, mergeTaxRatesInfo, MergePostTaxRates

urlpatterns = [
    path('taxList/', MergeTaxRatesList.as_view(), name='taxList'),
    path('taxDetails/<str:id>/', mergeTaxRatesInfo.as_view(), name='taxDetails'),
    path('post-tax_rate/', MergePostTaxRates.as_view(), name='post_tax_rates'),
]