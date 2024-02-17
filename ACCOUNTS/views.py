import traceback

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
)
from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class MergeAccounts(APIView):

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def account_source_data(self):

        if self.link_token_details is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details[0]
        merge_client = create_merge_client(account_token)

        try:
            accounts_data = merge_client.accounting.accounts.list(
                expand="company",
                remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
            )
            return accounts_data

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def account_payload(accounts_data):
        field_list = [
            {
                "organization_defined_targets": {},
                "linked_account_defined_targets": {}
            }
        ]

        accounts_list = []
        for account in accounts_data.results:
            account_dict = {
                'id': account.id,
                'remote_id': account.remote_id,
                'name': account.name,
                'description': account.description,
                'classification': account.classification,
                'type': account.type,
                'status': account.status,
                "current_balance": account.current_balance,
                "currency": account.currency,
                'account_number': account.account_number,
                'parent_account': account.parent_account,
                'company': account.company,
                'remote_was_deleted': account.remote_was_deleted,
                'created_at': account.created_at.isoformat() + "Z",
                'modified_at': account.modified_at.isoformat() + "Z",
                'field_mappings': field_list,
                'remote_data': account.remote_data
            }
            accounts_list.append(account_dict)
        accounts_formatted_data = {"accounts": accounts_list}
        return accounts_formatted_data

    def get(self, request, *args, **kwargs):
        api_log(msg="Processing GET request in MergeAccounts...")

        acnt_data = self.account_source_data()
        format_data = self.account_payload(acnt_data)
        api_log(msg=f"FORMATTED DATA: {format_data} \
                     - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(format_data, status=status.HTTP_200_OK)


class InsertAccountData(APIView):

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def post(self, request):
        erp_link_token_id = request.data.get('erp_link_token_id')
        authorization_header = request.headers.get('Authorization')
        if authorization_header and authorization_header.startswith('Bearer '):
            token = authorization_header.split(' ')[1]

            fetch_account_data = MergeAccounts(link_token_details=self.link_token_details)
            request_account_data = fetch_account_data.get(request=request)

            try:
                if request_account_data.status_code == status.HTTP_200_OK:
                    account_payload = request_account_data.data
                    account_payload["erp_link_token_id"] = erp_link_token_id
                    account_url = "https://dev.getkloo.com/api/v1/organizations/insert-erp-accounts"
                    account_response_data = requests.post(account_url, json=account_payload, headers={'Authorization': f'Bearer {token}'})
                    print("ACCOUNT INFO........",account_response_data)

                    if account_response_data.status_code == status.HTTP_201_CREATED:
                        api_log(msg=f"data inserted successfully in the kloo account system")
                        return Response(f"{account_response_data} data inserted successfully in kloo account system")

                    else:
                        return Response({'error': 'Failed to send data to Kloo API'}, status=account_response_data.status_code)

            except Exception as e:
                error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(f"Failed to insert data to the kloo account system", traceback)

