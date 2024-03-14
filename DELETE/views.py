import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_BASE_URL
from merge_integration.utils import create_merge_client


class DeleteAccount(APIView):
    def __init__(self):
        super().__init__()
        self.org_id = None
        self.erp_link_token_id = None

    def get_queryset(self):
        erp_link_token_id = self.erp_link_token_id
        filter_token = ErpLinkToken.objects.filter(id=erp_link_token_id)
        if filter_token.exists():
            lnk_token = filter_token.values_list("account_token", flat=True)
            return lnk_token

        return None

    def post(self, request, *args, **kwargs):
        api_log(msg="Processing GET request in MergeInvoice...")
        self.org_id = request.data.get("org_id")
        self.erp_link_token_id = request.data.get("erp_link_token_id")

        if self.org_id is None or self.erp_link_token_id is None:
            return Response(
                "Need both attributes to fetch account token",
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()

        if queryset is None:
            print("link_token_details is None")
            return None

        if len(queryset) == 0:
            print("link_token_details is an empty list")
            return None

        account_token = queryset[0]
        try:
            comp_client = create_merge_client(account_token)
            account_del_response = comp_client.accounting.delete_account.delete()
            if account_del_response is None:
                erp_link_token_id = request.data.get("erp_link_token_id")
                authorization_header = request.headers.get("Authorization")
                if authorization_header and authorization_header.startswith("Bearer "):
                    token = authorization_header.split(" ")[1]
                    disconnect_url = f"{GETKLOO_BASE_URL}/accounting-integrations/erp-disconnect/{erp_link_token_id}"
                    disconnect_execute = requests.delete(
                        disconnect_url, headers={"Authorization": f"Bearer {token}"}
                    )
                    if disconnect_execute.status_code == status.HTTP_204_NO_CONTENT:
                        return Response(
                            {"message": "Data deleted successfully"},
                            status=status.HTTP_200_OK,
                        )
                    else:
                        return Response(
                            {"error": "Failed to delete data"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

        except Exception as e:
            api_log(msg=f"Failed to send data to Kloo API. Error: {str(e)}")
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
