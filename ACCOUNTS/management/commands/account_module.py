import requests
from django.core.management.base import BaseCommand
from django.db import connection
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
)
from rest_framework import status

from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL
from merge_integration.utils import create_merge_client


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts

    1. Add user account token
    2. Add erp link token id
    3. Add organization id
    4. Add auth token from the env where you want to send the data ( since we cant use intranet api from outside)
    5. Add the url where you want to send the data

    ** For small amount of data use the script directly without any changes
    But for huge chunks of data above 1000 records, use batching **

    ** You can use the same pattern for other modules also, just change the merge api call
    and other values according to the module **

    """

    help = "Add Contacts Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = ""
        erp_link_token_id = ""
        org_id = ""
        auth_token = ""

        sql_query = f"""
        SELECT * FROM erp_link_token
        WHERE id = '{erp_link_token_id}'
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            linked_accounts = cursor.fetchall()

        api_log(msg=f"Total Linked Accounts: {linked_accounts}")

        try:
            accounts_client = create_merge_client(account_token)
            accounts_data = accounts_client.accounting.accounts.list(
                remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
                page_size=100,
                include_remote_data=True,
            )

            all_accounts = []
            while True:
                api_log(
                    msg=f"Adding {len(accounts_data.results)} accounts to the list."
                )

                all_accounts.extend(accounts_data.results)
                if accounts_data.next is None:
                    break

                accounts_data = accounts_client.accounting.accounts.list(
                    remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                    show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
                    page_size=100,
                    include_remote_data=True,
                    cursor=accounts_data.next,
                )

            api_log(msg=f"Total Account : {len(all_accounts)}")

            formatted_data = format_account_data(all_accounts)

            account_payload = formatted_data
            account_payload["erp_link_token_id"] = erp_link_token_id
            account_payload["org_id"] = org_id

            account_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-accounts"

            account_response_data = requests.post(
                account_url,
                json=account_payload,
                headers={"Authorization": f"Bearer {auth_token}"},
            )

            api_log(msg=f"Account Response Data: {account_response_data.json()}")

            if account_response_data.status_code == status.HTTP_201_CREATED:
                api_log(msg="data inserted successfully in the kloo Account system")
            else:
                api_log(msg="Failed to send data to Kloo Account API")

        except Exception as e:
            api_log(msg=f"Error in fetching accounts data : {e}")
            return


def format_account_data(accounts_data):
    field_list = [
        {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
    ]

    accounts_list = []
    for account in accounts_data:
        erp_remote_data = None
        if account.remote_data is not None:
            erp_remote_data = [
                account_remote_data.data for account_remote_data in account.remote_data
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
            "created_at": account.created_at.isoformat(),
            "modified_at": account.modified_at.isoformat(),
            "field_mappings": field_list,
            "remote_data": erp_remote_data,
        }
        accounts_list.append(account_dict)
    accounts_formatted_data = {"accounts": accounts_list}
    return accounts_formatted_data
