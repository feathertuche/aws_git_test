from django.urls import path

from .views import InvoiceCreate, MergeInvoiceCreate

urlpatterns = [
    path("invoicesCreate/", InvoiceCreate.as_view(), name="invoicesCreate"),
    path(
        "invoicesUpdate/<str:erp_invoice_id>",
        InvoiceCreate.as_view(),
        name="invoicesUpdate",
    ),

]
