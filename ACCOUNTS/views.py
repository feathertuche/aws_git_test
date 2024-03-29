import traceback

import requests
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL
from merge_integration.utils import create_merge_client


class MergeAccounts(APIView):
    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def account_source_data(self):
        if self.link_token_details is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details
        api_log(msg=f"ACCOUNTS GET:: The account token is : {account_token}")
        merge_client = create_merge_client(account_token)

        try:
            accounts_data = merge_client.accounting.accounts.list(
                remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
                page_size=100000,
                include_remote_data=True,
                modified_after=self.last_modified_at,
            )
            api_log(msg=f"Data coming from MERGE API is : {accounts_data}")
            return accounts_data

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def account_payload(accounts_data):
        field_list = [
            {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
        ]

        accounts_list = []
        for account in accounts_data.results:
            erp_remote_data = None
            if account.remote_data is not None:
                erp_remote_data = [
                    account_remote_data.data
                    for account_remote_data in account.remote_data
                ]

            account_dict = {
                "id": account.id,
                "remote_id": account.remote_id,
                "name": account.name,
                "description": account.description,
                "classification": account.classification,
                "type": account.type,
                "status": account.status,
                "current_balance": account.current_balance,
                "currency": account.currency,
                "account_number": account.account_number,
                "parent_account": account.parent_account,
                "company": account.company,
                "remote_was_deleted": account.remote_was_deleted,
                "created_at": account.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "modified_at": account.modified_at.strftime("%Y-%m-%d %H:%M:%S"),
                "field_mappings": field_list,
                "remote_data": erp_remote_data,
            }
            accounts_list.append(account_dict)
        accounts_formatted_data = {"accounts": accounts_list}
        return accounts_formatted_data

    def get(self, request, *args, **kwargs):
        api_log(msg="........Processing 'Accounts' GET request bloc.......")

        acnt_data = self.account_source_data()
        if acnt_data.results is None or acnt_data.results == []:
            return Response({"accounts": []}, status=status.HTTP_404_NOT_FOUND)

        format_data = self.account_payload(acnt_data)
        api_log(
            msg=f"FORMATTED DATA: {format_data} \
                     - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
        )
        return Response(format_data, status=status.HTTP_200_OK)


class InsertAccountData(APIView):
    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")

        fetch_account_data = MergeAccounts(
            link_token_details=self.link_token_details,
            last_modified_at=self.last_modified_at,
        )
        api_log(msg=f"ACCOUNTS POST: TOKEN is : {fetch_account_data}")
        request_account_data = fetch_account_data.get(request=request)

        try:
            if request_account_data.status_code == status.HTTP_200_OK:
                account_payload = request_account_data.data
                account_payload["erp_link_token_id"] = erp_link_token_id
                account_payload["org_id"] = org_id
                account_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-accounts"
                account_response_data = requests.post(
                    account_url,
                    json=account_payload,
                )

                if account_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(msg="data inserted successfully in the kloo account system")
                    return Response(
                        {"message": "API Account Info completed successfully"}
                    )

                else:
                    api_log(
                        msg=f"Failed to send data to Kloo API. Error: {account_response_data}"
                    )
                    return Response(
                        {"error": "Failed to send data to Kloo API"},
                        status=account_response_data.status_code,
                    )

            if request_account_data.status_code == status.HTTP_404_NOT_FOUND:
                return Response(
                    {
                        "message": "No new data found to insert in the kloo account system"
                    }
                )

        except Exception as e:
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response("Failed to insert data to the kloo account system", traceback)
