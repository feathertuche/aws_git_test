from django.urls import path
from .views import MergePOList, MergePODetails #, MergePostContacts

urlpatterns = [
    path('purchase_orders/', MergePOList.as_view(), name='purchase_orders'),
    path('po_id_info/<str:id>/', MergePODetails.as_view(), name='poinfo'),
    # path('post-contacts/', MergePostContacts.as_view(), name='post_contacts'),
]