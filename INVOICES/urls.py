from django.urls import path
from .views import MergeInvoices

urlpatterns = [
    path('invoicesList/', MergeInvoices.as_view(), name='invoicesList'),
]
