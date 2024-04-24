from django.urls import path

from .views import InvoiceCreate, MergeInvoiceCreate

urlpatterns = [
    path("invoicesCreate/", InvoiceCreate.as_view(), name="invoicesCreate"),
    path("invoicesUpdate/<str:invoice_id>", InvoiceCreate.as_view(), name="invoicesUpdate"),
    path(
        "invoicesMergeCreate/", MergeInvoiceCreate.as_view(), name="invoicesMergeCreate"
    ),
]
