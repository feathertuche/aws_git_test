"""
URL configuration for merge_integration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from .views import health_check


def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/erp/account-info/", include("ACCOUNTS.urls")),
    path("api/erp/contact-info/", include("CONTACTS.urls")),
    path("api/erp/comp-info/", include("COMPANY_INFO.urls")),
    path("api/v1/erp/invoice-info/", include("INVOICES.urls")),
    path("api/erp/tax-info/", include("TAX_RATE.urls")),
    path("api/erp/health/", health_check, name="health_check"),
    path("api/erp/", include("LINKTOKEN.urls")),
    path("api/erp/tracking-info/", include("TRACKING_CATEGORIES.urls")),
    path("api/erp/sync-data/", include("SYNC.urls")),
    path("po-info/", include("PURCHASE_ORDERS.urls")),
    path("api/erp/delete-info/", include("DELETE.urls")),
]
