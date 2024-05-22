import requests
from django.core.management.base import BaseCommand
from django.db import connection
from rest_framework import status

from TRACKING_CATEGORIES.helper_function import format_tracking_categories_payload
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_BASE_URL
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

    help = "Add Tracking Category Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Tracking Category Module for all completed linked accounts")

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
            tracking_category_client = create_merge_client(account_token)

            tracking_categories = (
                tracking_category_client.accounting.tracking_categories.list(
                    remote_fields="status",
                    show_enum_origins="status",
                    page_size=15,
                    include_remote_data=True,
                )
            )

            while True:
                api_log(
                    msg=f"Adding {len(tracking_categories.results)} tracking to the list."
                )

                formatted_payload = format_tracking_categories_payload(
                    tracking_categories.results
                )

                formatted_payload["erp_link_token_id"] = erp_link_token_id
                formatted_payload["org_id"] = org_id

                tc_url = f"{GETKLOO_BASE_URL}/organizations/erp-tracking-categories"

                tracking_response_data = requests.post(
                    tc_url,
                    json=formatted_payload,
                    headers={"Authorization": f"Bearer {auth_token}"},
                )

                api_log(
                    msg=f"Tracking Status Code: {tracking_response_data.status_code}"
                )

                if tracking_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(msg="data inserted successfully in the kloo Account system")
                else:
                    api_log(msg="Failed to send data to Kloo Tracking API")

                if tracking_categories.next is None:
                    break

                tracking_categories = (
                    tracking_category_client.accounting.tracking_categories.list(
                        remote_fields="status",
                        show_enum_origins="status",
                        page_size=15,
                        include_remote_data=True,
                        cursor=tracking_categories.next,
                    )
                )

        except Exception as e:
            api_log(msg=f"Error in fetching accounts data : {e}")
            return
