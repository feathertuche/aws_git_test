from django.urls import path

from .views import InvoiceCreate, MergeInvoiceCreate

urlpatterns = [
    path("invoicesCreate/", InvoiceCreate.as_view(), name="invoicesCreate"),
    path(
        "invoicesMergeCreate/", MergeInvoiceCreate.as_view(), name="invoicesMergeCreate"
    ),
]
