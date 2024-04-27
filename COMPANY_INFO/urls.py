from django.urls import path

from .views import MergeKlooCompanyInsert, MergeCompanyInfo

urlpatterns = [
    path("companyList/", MergeCompanyInfo.as_view(), name="companyList"),
    path(
        "syncall/<str:org_id>/<str:entity_id>/",
        MergeCompanyInfo.as_view(),
        name="syncall",
    ),
    path("kloo-insert/", MergeKlooCompanyInsert.as_view(), name="kloo-insert"),
]
