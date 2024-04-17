import os

import requests
from django.core.management.base import BaseCommand
from django.db import connection

from merge_integration.helper_functions import api_log


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts
    """

    help = "Fix invoice issue date for old invoices"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")
        # get all linked account whose status are complete and Invoice Module is not in master sync
        query = """SELECT
                        erp_link_token.id,
                        erp_link_token.org_id,
                        erp_sync_logs.link_token,
                        erp_link_token.account_token
                    FROM erp_link_token
                    JOIN erp_sync_logs
                    ON erp_link_token.id = erp_sync_logs.link_token_id
                    COLLATE utf8mb4_unicode_ci
                    WHERE erp_link_token.status = 'COMPLETE'
                    AND erp_sync_logs.label = 'TAX RATE'
                    """
        # execute the query and get the linked accounts
        with connection.cursor() as cursor:
            cursor.execute(query)
            linked_accounts = cursor.fetchall()
        if len(linked_accounts) == 0:
            print("No linked accounts found")
            return
        api_log(msg=f"Total Linked Accounts: {len(linked_accounts)}")

        for linked_account in linked_accounts:
            url = "https://api-eu.merge.dev/api/accounting/v1/invoices/{id}"
            # Headers including Authorization and X-Account-Token
            auth_token = os.environ.get("API_KEY")
            account_token = ""

            headers = {
                "Authorization": f"Bearer {auth_token}",
                "X-Account-Token": f"{account_token}",
            }

            # Data to be sent in the PATCH request
            data = {
                # Your data here
            }

            # PATCH request with headers
            response = requests.patch(url, json=data, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                print("PATCH request successful")
                # Handle the response data if needed
                print(response.json())
            else:
                print(f"Error: {response.status_code} - {response.text}")
