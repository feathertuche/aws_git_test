import requests
from django.core.management.base import BaseCommand
from rest_framework import status

from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL
from merge_integration.utils import create_merge_client


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts
    """

    help = "Add Invoice Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        # get all linked account whose status are complete and Invoice Module is not in master sync
        account_token = ""
        tc_client = create_merge_client(account_token)

        try:
            organization_data = tc_client.accounting.tracking_categories.list(
                remote_fields="status",
                show_enum_origins="status",
                page_size=100000,
                include_remote_data=True,
            )
            all_accounts = []
            while True:
                api_log(
                    msg=f"Adding {len(organization_data.results)} accounts to the list."
                )

                all_accounts.extend(organization_data.results)
                if organization_data.next is None:
                    break

                organization_data = tc_client.accounting.accounts.list(
                    remote_fields="status",
                    show_enum_origins="status",
                    page_size=100000,
                    include_remote_data=True,
                    cursor=organization_data.next,
                )

                api_log(
                    msg=f"ACCOUNTS GET:: The length of the next page account data is : {len(organization_data.results)}"
                )
                api_log(msg=f"Length of all_accounts: {len(organization_data.results)}")

            api_log(
                msg=f"ACCOUNTS GET:: The length of all account data is : {len(all_accounts)}"
            )
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                         - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}"
            )

        api_log(
            msg=f"ACCOUNTS GET:: The length of all account data is : {len(all_accounts)}"
        )

        try:
            batch_size = 50
            for i in range(0, len(all_accounts), batch_size):
                batch_data = all_accounts[i : i + batch_size]

                formatted_payload = format_payload(batch_data)

                tc_payload = formatted_payload
                tc_payload["erp_link_token_id"] = "c3922a0a-f742-11ee-9688-0242ac110008"
                tc_payload["org_id"] = "c9727872-3b7a-11ed-b538-a4fc776c6f93"
                tc_url = f"{GETKLOO_LOCAL_URL}/organizations/erp-tracking-categories"
                tc_response_data = requests.post(
                    tc_url,
                    json=tc_payload,
                )

                if tc_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(
                        msg="data inserted successfully in the kloo Tracking_Category system"
                    )
                else:
                    api_log(
                        msg=f"Failed to insert data to the kloo Tracking_Category system "
                        f"- Status Code: {tc_response_data.status_code}"
                    )
        except Exception as e:
            api_log(
                msg=f"Failed to send data to Kloo Tracking_Category API. Error: {str(e)}"
            )


def format_payload(organization_data):
    """
    Format the payload to be sent to the API
    """
    field_mappings = [
        {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
    ]

    formatted_data = []
    for category in organization_data:
        erp_remote_data = None
        if category.remote_data is not None:
            erp_remote_data = [
                category_remote_data.data
                for category_remote_data in category.remote_data
            ]

        formatted_entry = {
            "id": category.id,
            "name": category.name,
            "status": category.status,
            "category_type": category.category_type,
            "parent_category": category.parent_category,
            "company": category.company,
            "remote_was_deleted": category.remote_was_deleted,
            "remote_id": category.remote_id,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.modified_at.isoformat(),
            "field_mappings": field_mappings,
            "remote_data": erp_remote_data,
        }
        formatted_data.append(formatted_entry)
    kloo_format_json = {"tracking_category": formatted_data}

    return kloo_format_json
