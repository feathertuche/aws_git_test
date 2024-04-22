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

        account_token = "Q5RVdNwNDrSpLWS2CnWwAIq6aIL4glTACNPoIc1jMKLEnIYLG7pz_w"
        erp_link_token_id = "edd20d10-f7f8-11ee-ac52-0242ac110008"
        org_id = "c9727487-3b7a-11ed-b538-a4fc776c6f93"
        auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiI1NTAwNTM1Y2JiNmE2ZjEzZjBkYWY4MmQyODg1Nzc5MmMwOWFmMmFlODU3MmZkZmI1M2ZmYmVkOTE3NTZlYWI1MmIzZmYzNjVhODdmYTVlYSIsImlhdCI6MTcxMzc4MDIyNy4yNjExNDEsIm5iZiI6MTcxMzc4MDIyNy4yNjExNDQsImV4cCI6MTcxMzc4MDUyNy4yMzczMzksInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiOWI2MTJiMzctMmYyNi00Y2ZjLWI4OWQtNjY2YmNhMTZmMzQ1XCIsXCJmaXJzdF9uYW1lXCI6XCJBbmlrZXRcIixcIm1pZGRsZV9uYW1lXCI6bnVsbCxcImxhc3RfbmFtZVwiOlwiS2hlcmFsaXlhIE9BIG9uZVwiLFwiZW1haWxcIjpcImFuaWtldC5raGVyYWxpeWErb2ExQGJsZW5oZWltY2hhbGNvdC5jb21cIixcImJpcnRoX2RhdGVcIjpcIjE5OTQtMTAtMTZcIixcInVzZXJfY3JlYXRlZF9ieVwiOm51bGwsXCJsb2dpbl9hdHRlbXB0c1wiOjAsXCJzdGF0dXNcIjpcInVuYmxvY2tlZFwiLFwiY3JlYXRlZF9hdFwiOlwiMjAyNC0wMy0wN1QwNToyNDozOC4wMDAwMDBaXCIsXCJ1cGRhdGVkX2F0XCI6XCIyMDI0LTAzLTA3VDA1OjI2OjM3LjAwMDAwMFpcIixcInVzZXJfb3JnX2lkXCI6XCJlMDEwOWRlNS1iNDM1LTQ0OWYtYjBkYS04ZjhjZjY2ZDY4NjFcIixcIm9yZ2FuaXphdGlvbl9pZFwiOlwiMGY5MDU2YzQtOTg0YS00NDMxLWEzYWEtZGIyY2MxNDdkNTk3XCIsXCJvcmdhbml6YXRpb25fbmFtZVwiOlwiS2xvbyBRQVwifSxcInNjb3Blc1wiOltcImFsbC1jYXJkcy1yZWFkXCIsXCJteS1jYXJkcy1yZWFkXCIsXCJpc3N1ZS1jYXJkLWNyZWF0ZVwiLFwiYWN0aXZhdGUtcGh5c2ljYWwtY2FyZC11cGRhdGVcIixcInZpcnR1YWwtY2FyZHMtY3JlYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLXJlYWRcIixcInZpcnR1YWwtY2FyZHMtdXBkYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLWRlbGV0ZVwiLFwicGh5c2ljYWwtY2FyZHMtY3JlYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1yZWFkXCIsXCJwaHlzaWNhbC1jYXJkcy11cGRhdGVcIixcInBoeXNpY2FsLWNhcmRzLWRlbGV0ZVwiLFwiY2FyZC1saW1pdC11cGRhdGVcIixcImNhcmQtbmlja25hbWUtdXBkYXRlXCIsXCJjYW5jZWwtY2FyZC11cGRhdGVcIixcImZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwidW5mcmVlemUtY2FyZC11cGRhdGVcIixcImNhcmQtc3RhdHVzLXVwZGF0ZVwiLFwiY2FyZC1kb3dubG9hZHMtaW1wb3J0XCIsXCJ1c2Vycy1jcmVhdGVcIixcInVzZXJzLXJlYWRcIixcInVzZXJzLXVwZGF0ZVwiLFwidXNlcnMtZGVsZXRlXCIsXCJpbnZpdGF0aW9uLWxpbmstc2VuZFwiLFwiaGVhbHRoLWNoZWNrLXJlYWRcIixcIm5vdGlmaWNhdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLWNyZWF0ZVwiLFwib3JnYW5pemF0aW9uLXJlYWRcIixcIm9yZ2FuaXphdGlvbi11cGRhdGVcIixcIm9yZ2FuaXphdGlvbi1kZWxldGVcIixcIm9yZ2FuaXphdGlvbi1tb2R1bHItYWNjb3VudC1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtY3JlYXRlXCIsXCJ0cmFuc2FjdGlvbnMtcmVhZFwiLFwidHJhbnNhY3Rpb25zLXVwZGF0ZVwiLFwidHJhbnNhY3Rpb25zLWRlbGV0ZVwiLFwidXNlci10cmFuc2FjdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJjdXN0b21lci1jcmVhdGVcIixcImNvbXBhbnktcmVhZFwiLFwib3JnYW5pemF0aW9uLWFuYWx5dGljcy1yZWFkXCIsXCJ1c2VyLWFuYWx5dGljcy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtdXBkYXRlXCIsXCJjYXJkLXJlcXVlc3RzLWRlbGV0ZVwiLFwidGVhbXMtY3JlYXRlXCIsXCJ0ZWFtcy1yZWFkXCIsXCJ0ZWFtcy11cGRhdGVcIixcInRlYW1zLWRlbGV0ZVwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWNyZWF0ZVwiLFwiY2hhcmdlYmVlLXN1YnNjcmlwdGlvbi1yZWFkXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItYmlsbC1yZWFkXCIsXCJjaGFyZ2ViZWUtaW52b2ljZS1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXN1YnNjcmlwdGlvbnMtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1yZWFkXCIsXCJhcC1pbnZvaWNlLWNyZWF0ZVwiLFwiYXAtaW52b2ljZS1yZWFkXCIsXCJhcC1pbnZvaWNlLXVwZGF0ZVwiLFwic2V0dGluZy1yZWFkXCIsXCJzZXR0aW5nLWludGVncmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3JpZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcmVhZFwiLFwic2V0dGluZy1hZGRyZXNzLXJlYWRcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1jcmVhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1yZWFkXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtZGVsZXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLWNyZWF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1yZWFkXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLXVwZGF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1kZWxldGVcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1jZS1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWFwLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcG8tcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtY2FyZHMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaW52b2ljZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcHVyY2hhc2Utb3JkZXJzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWhpc3RvcnktcmVhZFwiLFwic2V0dGluZy1wYXllZS1tYW5hZ2VtZW50LXJlYWRcIixcImRhc2hib2FyZC1yZWFkXCIsXCJhcHByb3ZhbHMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1kb3dubG9hZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstZm9yLXJldmlldy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtbWFyay1hcy1hcHByb3ZlZC11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtc2F2ZS1hcy1kcmFmdC11cGRhdGVcIixcInhlcm8tYW5hbHlzaXMtcmVhZFwiLFwia2xvby1zcGVuZC1yZWFkXCIsXCJwYXktbm93LWJ1dHRvbi1yZWFkXCIsXCJhY2NvdW50LWRldGFpbHMtcmVhZFwiLFwiZGViaXQtYWNjb3VudC1jcmVhdGVcIixcImRlYml0LWFjY291bnQtcmVhZFwiLFwiZGViaXQtYWNjb3VudC11cGRhdGVcIixcImRlYml0LWFjY291bnQtZGVsZXRlXCIsXCJzdGFuZGluZy1vcmRlci1jcmVhdGVcIixcInN0YW5kaW5nLW9yZGVyLXJlYWRcIixcImltbWVkaWF0ZS1wYXltZW50LWNyZWF0ZVwiLFwiaW1tZWRpYXRlLXBheW1lbnQtcmVhZFwiLFwiYmFuay10cmFuc2Zlci1jcmVhdGVcIixcImJhbmstdHJhbnNmZXItcmVhZFwiLFwic2NoZWR1bGVkLXJlYWRcIixcImhpc3RvcnktcmVhZFwiLFwicHJvZmlsZS1yZWFkXCIsXCJwcm9maWxlLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWNyZWF0ZVwiLFwic3Vic2NyaXB0aW9uLXJlYWRcIixcInN1YnNjcmlwdGlvbi11cGRhdGVcIixcInN1YnNjcmlwdGlvbi1kZWxldGVcIixcInB1cmNoYXNlLW9yZGVyLWNyZWF0ZVwiLFwicHVyY2hhc2Utb3JkZXItcmVhZFwiLFwicHVyY2hhc2Utb3JkZXItdXBkYXRlXCIsXCJzY2hlZHVsZS1wYXltZW50LWJ1dHRvbi1yZWFkXCIsXCJjcmVkaXQtbm90ZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcGF5bWVudC1ydW5zLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXNjaGVkdWxlLXJlYWRcIixcInNjaGVkdWxlLXRhYi1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy10YXgtY29kZS1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1vcmdhbmlzYXRpb24tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1zdXBwbGllci1yZWFkXCIsXCJkYXNoYm9hcmQtaW0tcmVhZFwiLFwiaW52b2ljZS1tYXRjaGluZy1wby1yZWFkXCIsXCJwYXltZW50LXJ1bnMtY3JlYXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwicGF5bWVudC1ydW5zLXVwZGF0ZVwiLFwicGF5bWVudC1ydW5zLWRlbGV0ZVwiLFwiZGFzaGJvYXJkLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWVudGl0eS1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jcmVkaXQtbm90ZXMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtYXV0b21hdGljLWVtYWlsLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiLFwicGF5ZWUtY29udGFjdC1uby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wcmVmaXgtcG8tcmVhZFwiLFwicm9sZXMtY3JlYXRlXCIsXCJyb2xlcy1yZWFkXCIsXCJyb2xlcy11cGRhdGVcIixcInJvbGVzLWRlbGV0ZVwiXSxcInJvbGVcIjp7XCJpZFwiOlwiMjMyNzNjMTAtZDQ4Yi0xMWVkLWIyNmEtMTllZGUwMjViZDIwXCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.eKc-lGkpz45So8SwjOmsj9oLAvpbWAWCnoSfQ3F8r9UDw2EtNDzXFzH5k30HyJ6kiWJcATg9_o3rA3Ysmnh2jxrd9fEgBgXaIoA7l-TL-syw_m3hqxQshj5adg2ZF06JjVMdz3OgRwHHsVbdn48OvQsW9H0jOIs_myXQgESJOoGqIx40XtYsAzyFw1e4umF4OHvbgSAjFvXNi1uRNLRo6xPF4YrjcZgURfNXrKSCl9djstq9Ba0LL3L6Af3-gpGKYdevDNEinGHvfCOg-qngrszKUqXMgVM-8L2zIcQrtqKvDmrG8_XfnDH4SPcphW6s9xzQbAQTxUHEEcQ_mWYooQnkFsmU9crdceVWK7Ui2vfTcpB2S2hl35SMe69WmTTxqDc1m-_a5yYS1-ILyEMIy8f_HLFPTKRDkCQYmWSRDrTh6N4XQUT2kaHST-OuoKrC9UZAfsEGLfMtUvYcfsgr7HZtUGYQs-Zoqtz-NpLcks3LgovdvQBUCsSSFD9Gn2DIMfy2mhtYLtbxAJhEoYxS1pgG2DviHGyzZNlZOcAQA4vIFsHepNePQnZEfQf7LhvRGEY2eHY5LI--DB_affDRsqxh6MQ4hDbLJjaliCkuc8zwkJolpKnvUW5HaqBJJROSfnVUQeYiVT3fK2H_O4MLATdonydXrmEuMAnW-VhDFwQ"

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
