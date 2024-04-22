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
    """

    help = "Add Contacts Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = "gka8rp0ImOnFy3JKd9y5v7VNPhZKsGYXShVNSap95c1g_Q2H5lHYWw"
        erp_link_token_id = "cadea3f4-f7f8-11ee-ae1b-0242ac110008"

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

            api_log(msg=f"Total Contacts: {len(all_accounts)}")

            formatted_data = format_account_data(all_accounts)

            account_payload = formatted_data
            account_payload["erp_link_token_id"] = erp_link_token_id
            account_payload["org_id"] = "c9727487-3b7a-11ed-b538-a4fc776c6f93"

            account_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-accounts"

            auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiI1N2U0ZThhZDBhNzRjN2E0MTA0MzIzNjhiZWI1ZTNkNWNjNzE3MmMzNzQxYTAyNGY3N2U0OTJiOGY0ZjA1NjM5ZDUyYjEzOTAxNDIxZWEwNSIsImlhdCI6MTcxMzQzNjg1Mi42MTY0OCwibmJmIjoxNzEzNDM2ODUyLjYxNjQ4MiwiZXhwIjoxNzEzNDM3MTUyLjU5NDk5LCJzdWIiOiIiLCJzY29wZXMiOlsiKiJdLCJjdXN0b21fY2xhaW0iOiJ7XCJ1c2VyXCI6e1wiaWRcIjpcIjliNjEyYjM3LTJmMjYtNGNmYy1iODlkLTY2NmJjYTE2ZjM0NVwiLFwiZmlyc3RfbmFtZVwiOlwiQW5pa2V0XCIsXCJtaWRkbGVfbmFtZVwiOm51bGwsXCJsYXN0X25hbWVcIjpcIktoZXJhbGl5YSBPQSBvbmVcIixcImVtYWlsXCI6XCJhbmlrZXQua2hlcmFsaXlhK29hMUBibGVuaGVpbWNoYWxjb3QuY29tXCIsXCJiaXJ0aF9kYXRlXCI6XCIxOTk0LTEwLTE2XCIsXCJ1c2VyX2NyZWF0ZWRfYnlcIjpudWxsLFwibG9naW5fYXR0ZW1wdHNcIjowLFwic3RhdHVzXCI6XCJ1bmJsb2NrZWRcIixcImNyZWF0ZWRfYXRcIjpcIjIwMjQtMDMtMDdUMDU6MjQ6MzguMDAwMDAwWlwiLFwidXBkYXRlZF9hdFwiOlwiMjAyNC0wMy0wN1QwNToyNjozNy4wMDAwMDBaXCIsXCJ1c2VyX29yZ19pZFwiOlwiZTAxMDlkZTUtYjQzNS00NDlmLWIwZGEtOGY4Y2Y2NmQ2ODYxXCIsXCJvcmdhbml6YXRpb25faWRcIjpcIjBmOTA1NmM0LTk4NGEtNDQzMS1hM2FhLWRiMmNjMTQ3ZDU5N1wiLFwib3JnYW5pemF0aW9uX25hbWVcIjpcIktsb28gUUFcIn0sXCJzY29wZXNcIjpbXCJhbGwtY2FyZHMtcmVhZFwiLFwibXktY2FyZHMtcmVhZFwiLFwiaXNzdWUtY2FyZC1jcmVhdGVcIixcImFjdGl2YXRlLXBoeXNpY2FsLWNhcmQtdXBkYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLWNyZWF0ZVwiLFwidmlydHVhbC1jYXJkcy1yZWFkXCIsXCJ2aXJ0dWFsLWNhcmRzLXVwZGF0ZVwiLFwidmlydHVhbC1jYXJkcy1kZWxldGVcIixcInBoeXNpY2FsLWNhcmRzLWNyZWF0ZVwiLFwicGh5c2ljYWwtY2FyZHMtcmVhZFwiLFwicGh5c2ljYWwtY2FyZHMtdXBkYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1kZWxldGVcIixcImNhcmQtbGltaXQtdXBkYXRlXCIsXCJjYXJkLW5pY2tuYW1lLXVwZGF0ZVwiLFwiY2FuY2VsLWNhcmQtdXBkYXRlXCIsXCJmcmVlemUtY2FyZC11cGRhdGVcIixcInVuZnJlZXplLWNhcmQtdXBkYXRlXCIsXCJjYXJkLXN0YXR1cy11cGRhdGVcIixcImNhcmQtZG93bmxvYWRzLWltcG9ydFwiLFwidXNlcnMtY3JlYXRlXCIsXCJ1c2Vycy1yZWFkXCIsXCJ1c2Vycy11cGRhdGVcIixcInVzZXJzLWRlbGV0ZVwiLFwiaW52aXRhdGlvbi1saW5rLXNlbmRcIixcImhlYWx0aC1jaGVjay1yZWFkXCIsXCJub3RpZmljYXRpb25zLXJlYWRcIixcIm9yZ2FuaXphdGlvbi1jcmVhdGVcIixcIm9yZ2FuaXphdGlvbi1yZWFkXCIsXCJvcmdhbml6YXRpb24tdXBkYXRlXCIsXCJvcmdhbml6YXRpb24tZGVsZXRlXCIsXCJvcmdhbml6YXRpb24tbW9kdWxyLWFjY291bnQtcmVhZFwiLFwidHJhbnNhY3Rpb25zLWNyZWF0ZVwiLFwidHJhbnNhY3Rpb25zLXJlYWRcIixcInRyYW5zYWN0aW9ucy11cGRhdGVcIixcInRyYW5zYWN0aW9ucy1kZWxldGVcIixcInVzZXItdHJhbnNhY3Rpb25zLXJlYWRcIixcIm9yZ2FuaXphdGlvbi10cmFuc2FjdGlvbnMtcmVhZFwiLFwiY3VzdG9tZXItY3JlYXRlXCIsXCJjb21wYW55LXJlYWRcIixcIm9yZ2FuaXphdGlvbi1hbmFseXRpY3MtcmVhZFwiLFwidXNlci1hbmFseXRpY3MtcmVhZFwiLFwiY2FyZC1yZXF1ZXN0cy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXVwZGF0ZVwiLFwiY2FyZC1yZXF1ZXN0cy1kZWxldGVcIixcInRlYW1zLWNyZWF0ZVwiLFwidGVhbXMtcmVhZFwiLFwidGVhbXMtdXBkYXRlXCIsXCJ0ZWFtcy1kZWxldGVcIixcImNoYXJnZWJlZS1jdXN0b21lci1jcmVhdGVcIixcImNoYXJnZWJlZS1zdWJzY3JpcHRpb24tcmVhZFwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWJpbGwtcmVhZFwiLFwiY2hhcmdlYmVlLWludm9pY2UtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1zdWJzY3JpcHRpb25zLXJlYWRcIixcImNoYXJnZWJlZS1vcmdhbml6YXRpb24tcmVhZFwiLFwiYXAtaW52b2ljZS1jcmVhdGVcIixcImFwLWludm9pY2UtcmVhZFwiLFwiYXAtaW52b2ljZS11cGRhdGVcIixcInNldHRpbmctcmVhZFwiLFwic2V0dGluZy1pbnRlZ3JhdGlvbnMtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaWVzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXJlYWRcIixcInNldHRpbmctYWRkcmVzcy1yZWFkXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtY3JlYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtcmVhZFwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLXVwZGF0ZVwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLWRlbGV0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1jcmVhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtcmVhZFwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS11cGRhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtZGVsZXRlXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tY2UtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1hcC1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLXBvLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWNhcmRzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXB1cmNoYXNlLW9yZGVycy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1oaXN0b3J5LXJlYWRcIixcInNldHRpbmctcGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJkYXNoYm9hcmQtcmVhZFwiLFwiYXBwcm92YWxzLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtZG93bmxvYWQtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1tYXJrLWZvci1yZXZpZXctdXBkYXRlXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstYXMtYXBwcm92ZWQtdXBkYXRlXCIsXCJjYXJkLWV4cGVuc2VzLXNhdmUtYXMtZHJhZnQtdXBkYXRlXCIsXCJ4ZXJvLWFuYWx5c2lzLXJlYWRcIixcImtsb28tc3BlbmQtcmVhZFwiLFwicGF5LW5vdy1idXR0b24tcmVhZFwiLFwiYWNjb3VudC1kZXRhaWxzLXJlYWRcIixcImRlYml0LWFjY291bnQtY3JlYXRlXCIsXCJkZWJpdC1hY2NvdW50LXJlYWRcIixcImRlYml0LWFjY291bnQtdXBkYXRlXCIsXCJkZWJpdC1hY2NvdW50LWRlbGV0ZVwiLFwic3RhbmRpbmctb3JkZXItY3JlYXRlXCIsXCJzdGFuZGluZy1vcmRlci1yZWFkXCIsXCJpbW1lZGlhdGUtcGF5bWVudC1jcmVhdGVcIixcImltbWVkaWF0ZS1wYXltZW50LXJlYWRcIixcImJhbmstdHJhbnNmZXItY3JlYXRlXCIsXCJiYW5rLXRyYW5zZmVyLXJlYWRcIixcInNjaGVkdWxlZC1yZWFkXCIsXCJoaXN0b3J5LXJlYWRcIixcInByb2ZpbGUtcmVhZFwiLFwicHJvZmlsZS11cGRhdGVcIixcInN1YnNjcmlwdGlvbi1jcmVhdGVcIixcInN1YnNjcmlwdGlvbi1yZWFkXCIsXCJzdWJzY3JpcHRpb24tdXBkYXRlXCIsXCJzdWJzY3JpcHRpb24tZGVsZXRlXCIsXCJwdXJjaGFzZS1vcmRlci1jcmVhdGVcIixcInB1cmNoYXNlLW9yZGVyLXJlYWRcIixcInB1cmNoYXNlLW9yZGVyLXVwZGF0ZVwiLFwic2NoZWR1bGUtcGF5bWVudC1idXR0b24tcmVhZFwiLFwiY3JlZGl0LW5vdGVzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXBheW1lbnQtcnVucy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1zY2hlZHVsZS1yZWFkXCIsXCJzY2hlZHVsZS10YWItcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtdGF4LWNvZGUtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtcmVhZFwiLFwiZGFzaGJvYXJkLWNhcmQtYW5kLWNhcmQtZXhwZW5zZXMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtb3JnYW5pc2F0aW9uLXJlYWRcIixcInBheWVlLW1hbmFnZW1lbnQtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtc3VwcGxpZXItcmVhZFwiLFwiZGFzaGJvYXJkLWltLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctcG8tcmVhZFwiLFwicGF5bWVudC1ydW5zLWNyZWF0ZVwiLFwicGF5bWVudC1ydW5zLXJlYWRcIixcInBheW1lbnQtcnVucy11cGRhdGVcIixcInBheW1lbnQtcnVucy1kZWxldGVcIixcImRhc2hib2FyZC1wby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1lbnRpdHktcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtY3JlZGl0LW5vdGVzLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWF1dG9tYXRpYy1lbWFpbC1wby1yZWFkXCIsXCJpbnZvaWNlLW1hdGNoaW5nLWltLXJlYWRcIixcInBheWVlLWNvbnRhY3Qtbm8tcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtcHJlZml4LXBvLXJlYWRcIixcInJvbGVzLWNyZWF0ZVwiLFwicm9sZXMtcmVhZFwiLFwicm9sZXMtdXBkYXRlXCIsXCJyb2xlcy1kZWxldGVcIl0sXCJyb2xlXCI6e1wiaWRcIjpcIjIzMjczYzEwLWQ0OGItMTFlZC1iMjZhLTE5ZWRlMDI1YmQyMFwiLFwibmFtZVwiOlwiT3JnYW5pc2F0aW9uIEFkbWluXCJ9fSJ9.IB5oyZgmTM9jzcngVIzdxJOvTjUSt2wQ5J9lnltBpSJDvLbusTvxu8AYiFCJ8YcSDClmD0b1KraDCCIT9p4EYPxHuZRr9SVfKKSRVqp8bncjo9MK8gA4azS7R2SC9LzAsTh69mRq5bS8j8f_6HI4hDxIzjoa1tvu92fglCEMa6RjUib5a6S2rI5yU39xiOoLcwQYkk-Ik5FiSRHZyFgMEE06W0MRnPfI8I66FAhhP1XbC-nqLbKfbxiosMZ2kMxZ9ho-V3V4grL9vUQjAiM-sU2GFt9N0gGHPCvnawO4VmnuR_ZH6MtWlA-4D5h26Rb7mzznUd_NDh7n2agOElNZia8Ylk2w5mdO7X_dMNvvir6JL031aWwa_FMohHLYtYWvzdQ0lQNtGGxASRKwZP_8WHbxrCeuRltLkUKht4UpcQUsnNl_M7jwKIcpFroK5cdudk3d2E2h2ubDjn9IZh2BhOe0qM4FK7O7HrV8t8iUc79tFDtMQjqFbMyl3E9r1AjpV7OSCkbaOrHdqPIewXxO6WrnXG7S29DqQlPsvGMC7BGsKq5dGGV4ZhWaoC-rwKB9WAJc1kxAWaFvPSFKDbKQ4PeZQC3uGhBP7UOu-r2b2qP3F1r1PcEFf_cMohAPhtS0jIGDgWWDccxAKKnRWq4kB2yI2TB1zTNCDFnggKxRWhI"

            #
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
