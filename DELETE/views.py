import requests
from LINKTOKEN.model import ErpLinkToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class deleteAccount(APIView):
    def __init__(self):
        super().__init__()
        self.org_id = None
        self.entity_id = None

    def get_queryset(self):
        if self.org_id is None:
            return ErpLinkToken.objects.none()
        else:
            filter_token = ErpLinkToken.objects.filter(org_id=self.org_id)
            lnk_token = filter_token.values_list('account_token', flat=1)

        return lnk_token

    def post(self, request, *args, **kwargs):
        api_log(msg="Processing GET request in MergeInvoice...")
        self.org_id = request.data.get("org_id")

        if self.org_id is None:
            return Response(f"Need both attributes to fetch account token")

        queryset = self.get_queryset()

        if queryset is None:
            print("link_token_details is None")
            return None

        if len(queryset) == 0:
            print("link_token_details is an empty list")
            return None

        account_token = queryset[0]
        comp_client = create_merge_client(account_token)
        try:
            account_del_response = comp_client.accounting.delete_account.delete()
            if account_del_response is None:
                erp_link_token_id = request.data.get("erp_link_token_id")
                authorization_header = request.headers.get('Authorization')
                if authorization_header and authorization_header.startswith('Bearer '):
                    token = authorization_header.split(' ')[1]
                    disconnect_url = f"https://dev.getkloo.com/api/v1/accounting-integrations/erp-disconnect/{erp_link_token_id}"
                    disconnect_execute = requests.post(disconnect_url, headers={'Authorization': f'Bearer {token}'})
                    if disconnect_execute.status_code == status.HTTP_201_CREATED:
                        return Response(f"successfully deleted")
                    else:
                        return Response({'error': 'Failed to delete data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
