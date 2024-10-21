from django.urls import path
from .views import MergeTaxRatesList, mergeTaxRatesInfo, MergePostTaxRates, SageFetchTaxDetails

urlpatterns = [
    path("taxList/", MergeTaxRatesList.as_view(), name="taxList"),
    path("taxDetails/<str:id>/", mergeTaxRatesInfo.as_view(), name="taxDetails"),
    path("post-tax_rate/", MergePostTaxRates.as_view(), name="post_tax_rates"),
    path("sage-passthrough-tax-detail", SageFetchTaxDetails.as_view(), name="sage-passthrough-tax-detail")
]
