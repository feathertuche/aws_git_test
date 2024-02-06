from django.urls import path
from .views import listErpData, ListAccountTokenView

urlpatterns = [
    path('sync/', listErpData.as_view(), name='sync'),
   path('syncall/<str:org_id>/<str:entity_id>/', ListAccountTokenView.as_view(), name='syncall'),

]
