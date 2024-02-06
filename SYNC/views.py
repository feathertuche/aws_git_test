from rest_framework.generics import ListAPIView

# from COMPANY_INFO.views import MergeCompanyDetails, MergeKlooCompanyInsert
from LINKTOKEN.models import ErpLinkToken
from .serializers import AccountTokenSerializers


class ListAccountTokenView(ListAPIView):
    serializer_class = AccountTokenSerializers

    def get_queryset(self):
        org_id = self.kwargs.get('org_id')
        entity_id = self.kwargs.get('entity_id')
        queryset = ErpLinkToken.objects.filter(org_id=org_id, entity_id=entity_id)
        return queryset


class listErpData(ListAPIView):
    queryset = ErpLinkToken.objects.all()
    serializer_class = AccountTokenSerializers


# class syncdata:
#     def post(self. request):
#         try:
#             app1 = MergeKlooCompanyInsert.post()
#             app2 =