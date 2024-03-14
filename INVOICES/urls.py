from django.urls import path
from .views import MergeInvoices, MergeInvoiceCreate

urlpatterns = [
    path("invoicesList/", MergeInvoices.as_view(), name="invoicesList"),
    path("invoicesCreate/", MergeInvoiceCreate.as_view(), name="invoicesCreate"),
]
