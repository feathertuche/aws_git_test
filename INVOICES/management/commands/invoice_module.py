import uuid

import requests
from django.core.management.base import BaseCommand
from merge.resources.accounting import (
    ContactsListRequestExpand,
    ContactsRetrieveRequestExpand, InvoicesRetrieveRequestExpand,
)
from rest_framework import status
import tenacity

from INVOICES.helper_functions import format_line_item
from INVOICES.queries import get_currency_id
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL, GETKLOO_BASE_URL
from merge_integration.utils import create_merge_client
from merge.core import ApiError
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
    CompanyInfoListRequestExpand,
    ContactsListRequestExpand,
    InvoiceRequest,
    AccountingAttachmentRequest,
    InvoicesListRequestExpand,
)
from rest_framework import status
from rest_framework.response import Response

from INVOICES.exceptions import MergeApiException
from INVOICES.models import InvoiceAttachmentLogs


class Command(BaseCommand):
    """
    Search and add matching suppliers from the list to Kloo Contacts

    1. Add user account token
    2. Add erp link token id
    3. Add organization id
    4. Add auth token from the env where you want to send the data ( since we cant use intranet api from outside)


    * First add the list of suppliers names in the variable suppliers_name_list
    * Then fetch the contacts data from the merge api , you must do it in batch of 100 records
    * First get 100 records search for matching suppliers , if any match found store that supplier merge id variable contact_ids
    * Then fetch the next 100 records and do the same until all the records are fetched
    * Then send the contact_ids to Merge retrieve api to get the contact data
    * Then format the data in the required format and send it to the Kloo Contacts API

    """

    help = "Add Matching suppliers from list to Kloo Contacts"

    @tenacity.retry(wait=tenacity.wait_exponential(min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = "kBiLLll5Orn3xpmJBfs0HQpPvZBjtmz46FtICY5xIUWKjJDpq0pm1g"
        erp_link_token_id = "937d3f70-0701-11ef-83c9-0242ac110004"
        auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiJiYmVjZTgzMGE3NjJjOGM2NjI3YTViYzNjNDg4YjllNmZmYTI5OTY3NjEzMDhhZTI5ZGU2OTJhMDU5MzZiMDVkYzE4MDk2MWU5NjQ2NDVjYyIsImlhdCI6MTcxNDYzMzAzMy41NDUzNDcsIm5iZiI6MTcxNDYzMzAzMy41NDUzNDksImV4cCI6MTcxNDYzMzMzMy41MTU4OTIsInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiNmYwNTliODctNjM3Ni00ZjgzLTg3OTktNGNhNzdlYjM5NTIxXCIsXCJmaXJzdF9uYW1lXCI6XCJhbWl0ZXNoXCIsXCJtaWRkbGVfbmFtZVwiOm51bGwsXCJsYXN0X25hbWVcIjpcInNhaGF5XCIsXCJlbWFpbFwiOlwiYW1pdGVzaC5zYWhheUBnZXRrbG9vLmNvbVwiLFwiYmlydGhfZGF0ZVwiOlwiMTk4NC0xMi0zMVwiLFwidXNlcl9jcmVhdGVkX2J5XCI6bnVsbCxcImxvZ2luX2F0dGVtcHRzXCI6MCxcInN0YXR1c1wiOlwidW5ibG9ja2VkXCIsXCJjcmVhdGVkX2F0XCI6XCIyMDI0LTA1LTAyVDA2OjE4OjQ4LjAwMDAwMFpcIixcInVwZGF0ZWRfYXRcIjpcIjIwMjQtMDUtMDJUMDY6NTc6MTEuMDAwMDAwWlwiLFwidXNlcl9vcmdfaWRcIjpcIjZkZWQ1MjUxLWQ2YzAtNGFjZi04MjJkLWRhMDJmYTE4MmI0OVwiLFwib3JnYW5pemF0aW9uX2lkXCI6XCIwZjkwNTZjNC05ODRhLTQ0MzEtYTNhYS1kYjJjYzE0N2Q1OTdcIixcIm9yZ2FuaXphdGlvbl9uYW1lXCI6XCJLbG9vIFFBXCJ9LFwic2NvcGVzXCI6W1wiYWxsLWNhcmRzLXJlYWRcIixcIm15LWNhcmRzLXJlYWRcIixcImlzc3VlLWNhcmQtY3JlYXRlXCIsXCJhY3RpdmF0ZS1waHlzaWNhbC1jYXJkLXVwZGF0ZVwiLFwidmlydHVhbC1jYXJkcy1jcmVhdGVcIixcInZpcnR1YWwtY2FyZHMtcmVhZFwiLFwidmlydHVhbC1jYXJkcy11cGRhdGVcIixcInZpcnR1YWwtY2FyZHMtZGVsZXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1jcmVhdGVcIixcInBoeXNpY2FsLWNhcmRzLXJlYWRcIixcInBoeXNpY2FsLWNhcmRzLXVwZGF0ZVwiLFwicGh5c2ljYWwtY2FyZHMtZGVsZXRlXCIsXCJjYXJkLWxpbWl0LXVwZGF0ZVwiLFwiY2FyZC1uaWNrbmFtZS11cGRhdGVcIixcImNhbmNlbC1jYXJkLXVwZGF0ZVwiLFwiZnJlZXplLWNhcmQtdXBkYXRlXCIsXCJ1bmZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwiY2FyZC1zdGF0dXMtdXBkYXRlXCIsXCJjYXJkLWRvd25sb2Fkcy1pbXBvcnRcIixcInVzZXJzLWNyZWF0ZVwiLFwidXNlcnMtcmVhZFwiLFwidXNlcnMtdXBkYXRlXCIsXCJ1c2Vycy1kZWxldGVcIixcImludml0YXRpb24tbGluay1zZW5kXCIsXCJoZWFsdGgtY2hlY2stcmVhZFwiLFwibm90aWZpY2F0aW9ucy1yZWFkXCIsXCJvcmdhbml6YXRpb24tY3JlYXRlXCIsXCJvcmdhbml6YXRpb24tcmVhZFwiLFwib3JnYW5pemF0aW9uLXVwZGF0ZVwiLFwib3JnYW5pemF0aW9uLWRlbGV0ZVwiLFwib3JnYW5pemF0aW9uLW1vZHVsci1hY2NvdW50LXJlYWRcIixcInRyYW5zYWN0aW9ucy1jcmVhdGVcIixcInRyYW5zYWN0aW9ucy1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtdXBkYXRlXCIsXCJ0cmFuc2FjdGlvbnMtZGVsZXRlXCIsXCJ1c2VyLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJvcmdhbml6YXRpb24tdHJhbnNhY3Rpb25zLXJlYWRcIixcImN1c3RvbWVyLWNyZWF0ZVwiLFwiY29tcGFueS1yZWFkXCIsXCJvcmdhbml6YXRpb24tYW5hbHl0aWNzLXJlYWRcIixcInVzZXItYW5hbHl0aWNzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtcmVhZFwiLFwiY2FyZC1yZXF1ZXN0cy11cGRhdGVcIixcImNhcmQtcmVxdWVzdHMtZGVsZXRlXCIsXCJ0ZWFtcy1jcmVhdGVcIixcInRlYW1zLXJlYWRcIixcInRlYW1zLXVwZGF0ZVwiLFwidGVhbXMtZGVsZXRlXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItY3JlYXRlXCIsXCJjaGFyZ2ViZWUtc3Vic2NyaXB0aW9uLXJlYWRcIixcImNoYXJnZWJlZS1jdXN0b21lci1iaWxsLXJlYWRcIixcImNoYXJnZWJlZS1pbnZvaWNlLXJlYWRcIixcImNoYXJnZWJlZS1vcmdhbml6YXRpb24tc3Vic2NyaXB0aW9ucy1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXJlYWRcIixcImFwLWludm9pY2UtY3JlYXRlXCIsXCJhcC1pbnZvaWNlLXJlYWRcIixcImFwLWludm9pY2UtdXBkYXRlXCIsXCJzZXR0aW5nLXJlYWRcIixcInNldHRpbmctaW50ZWdyYXRpb25zLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmllcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1yZWFkXCIsXCJzZXR0aW5nLWFkZHJlc3MtcmVhZFwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLWNyZWF0ZVwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLXJlYWRcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC11cGRhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1kZWxldGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtY3JlYXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLXJlYWRcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtdXBkYXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLWRlbGV0ZVwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWNlLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tYXAtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1wby1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jYXJkcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1wdXJjaGFzZS1vcmRlcnMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaGlzdG9yeS1yZWFkXCIsXCJzZXR0aW5nLXBheWVlLW1hbmFnZW1lbnQtcmVhZFwiLFwiZGFzaGJvYXJkLXJlYWRcIixcImFwcHJvdmFscy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtdXBkYXRlXCIsXCJjYXJkLWV4cGVuc2VzLWRvd25sb2FkLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtbWFyay1mb3ItcmV2aWV3LXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1tYXJrLWFzLWFwcHJvdmVkLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1zYXZlLWFzLWRyYWZ0LXVwZGF0ZVwiLFwieGVyby1hbmFseXNpcy1yZWFkXCIsXCJrbG9vLXNwZW5kLXJlYWRcIixcInBheS1ub3ctYnV0dG9uLXJlYWRcIixcImFjY291bnQtZGV0YWlscy1yZWFkXCIsXCJkZWJpdC1hY2NvdW50LWNyZWF0ZVwiLFwiZGViaXQtYWNjb3VudC1yZWFkXCIsXCJkZWJpdC1hY2NvdW50LXVwZGF0ZVwiLFwiZGViaXQtYWNjb3VudC1kZWxldGVcIixcInN0YW5kaW5nLW9yZGVyLWNyZWF0ZVwiLFwic3RhbmRpbmctb3JkZXItcmVhZFwiLFwiaW1tZWRpYXRlLXBheW1lbnQtY3JlYXRlXCIsXCJpbW1lZGlhdGUtcGF5bWVudC1yZWFkXCIsXCJiYW5rLXRyYW5zZmVyLWNyZWF0ZVwiLFwiYmFuay10cmFuc2Zlci1yZWFkXCIsXCJzY2hlZHVsZWQtcmVhZFwiLFwiaGlzdG9yeS1yZWFkXCIsXCJwcm9maWxlLXJlYWRcIixcInByb2ZpbGUtdXBkYXRlXCIsXCJzdWJzY3JpcHRpb24tY3JlYXRlXCIsXCJzdWJzY3JpcHRpb24tcmVhZFwiLFwic3Vic2NyaXB0aW9uLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWRlbGV0ZVwiLFwicHVyY2hhc2Utb3JkZXItY3JlYXRlXCIsXCJwdXJjaGFzZS1vcmRlci1yZWFkXCIsXCJwdXJjaGFzZS1vcmRlci11cGRhdGVcIixcInNjaGVkdWxlLXBheW1lbnQtYnV0dG9uLXJlYWRcIixcImNyZWRpdC1ub3Rlcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1wYXltZW50LXJ1bnMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtaW0tcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaW52b2ljZXMtc2NoZWR1bGUtcmVhZFwiLFwic2NoZWR1bGUtdGFiLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXRheC1jb2RlLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWF1dG9tYXRpYy1saS1pbS1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1vcmdhbmlzYXRpb24tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1zdXBwbGllci1yZWFkXCIsXCJkYXNoYm9hcmQtaW0tcmVhZFwiLFwiaW52b2ljZS1tYXRjaGluZy1wby1yZWFkXCIsXCJwYXltZW50LXJ1bnMtY3JlYXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwicGF5bWVudC1ydW5zLXVwZGF0ZVwiLFwicGF5bWVudC1ydW5zLWRlbGV0ZVwiLFwiZGFzaGJvYXJkLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWVudGl0eS1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jcmVkaXQtbm90ZXMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtYXV0b21hdGljLWVtYWlsLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiLFwicGF5ZWUtY29udGFjdC1uby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wcmVmaXgtcG8tcmVhZFwiLFwicm9sZXMtY3JlYXRlXCIsXCJyb2xlcy1yZWFkXCIsXCJyb2xlcy11cGRhdGVcIixcInJvbGVzLWRlbGV0ZVwiXSxcInJvbGVcIjp7XCJpZFwiOlwiMjMyNzNjMTAtZDQ4Yi0xMWVkLWIyNmEtMTllZGUwMjViZDIwXCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.MeY2JD2LgsQcQqjZabBs4mogS1J8FNNlPTQNs3iRWePet_NzS3XfIucorCsQQQ_TrY3JbVwBMvC5BUH2K0Y7DPighJEa6d57vWvmE3UwOW-zgh1JbAkXJoWRKQ76NegEPw56EnqVQ7Tn5fA7z0wjVhL38GrDzy7beOJA4wPO_CzIHdNj5cYfWd1yrEqcem-Txhz83l3ThwWAWR8j9e-q31WXbLKCYhqMHx0tQVQpyPOKyWRYs8RXunq9I6ywEVQAH9o81HB9cqTWWWn_TDMqwNKS_LepEmOg1bs1qy8B-7wPiQinuFBOmBPOoN3kFRMQUIEbluhAiptynga_SgtADrUjKXD2lMLUuqK5djvOwRbg3lQydLFZ6NU2oZbU5AWLleoo7zgKd5BOOpadqsTbunlPLF_U2N2f-pbRK4isSmQ8jkCUymd_NJVlI_ZP7ZFCC_eIC5wN06dcrw35lth27nw7hmxhZM-7vPwJdQa8Hzp1_MJBwMud6V-fKxxMPBGvX7OoSgjTEu7aWSJHHNYpQRNlQMiv9I2Z5ey9phXDxXwpTf8wEvdq62eWK6rUDp_wfbXKQ1ywaVkplpMLI5iLoqsQKQuKX0ZPwRWaaYMDON_I3I3efhcyX907fICuEYIOfLVOV-A2trOyoBd2FyCBy68rT3o_7XinXWB8NVYYRhU"
        org_id = "c97276d0-3b7a-11ed-b538-a4fc776c6f93"

        try:
            invoice_client = create_merge_client(account_token)

            # suppliers_name_list = ["Bigbearpromo LTD"]
            contact_ids = []

            invoice_data = invoice_client.accounting.invoices.list(
                expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                remote_fields="type",
                show_enum_origins="type",
                page_size=100,
                include_remote_data=True,
            )
            while True:
                api_log(msg=f"Adding {len(invoice_data.results)} contacts to the list.")
                for invoice in invoice_data.results:
                    contact_ids.append(invoice.id)
                    api_log(msg=f"[after append CONTACT name LIST] : {invoice.contact} and {invoice.id}")
                    #break

                if invoice_data.next is None:
                    break

                invoice_data = invoice_client.accounting.invoices.list(
                    expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                    remote_fields="type",
                    show_enum_origins="type",
                    page_size=100,
                    include_remote_data=True,
                    cursor=invoice_data.next,
                )

            api_log(msg=f"Total Contacts: {contact_ids}")
            api_log(msg="1")

            contacts = []
            api_log(msg="2")
            for invoice_id in contact_ids:
                api_log(msg="3")
                api_log(msg=f"Total Invoice ids b4 retrive bloc: {contact_ids}")
                contact = invoice_client.accounting.invoices.retrieve(
                        id=invoice_id,
                        expand=InvoicesRetrieveRequestExpand.ACCOUNTING_PERIOD,
                        remote_fields="type",
                        show_enum_origins="type",
                )
                api_log(msg="4")
                contacts.append(contact)
                api_log(msg="5")
                api_log(msg=f"[CONTACTS LIST] : {contacts}")
            # api_log(msg=f"[CONTACTS LIST outside for loop] : {contacts}")
            api_log(msg="6")
            formatted_data = format_merge_invoice_data(contacts, erp_link_token_id, org_id)
            api_log(msg="7")
            api_log(msg=f"[FORMATTED DATA] : {formatted_data}")
            api_log(msg=f"Formatted Data: {len(formatted_data)}")
            api_log(msg="8")
            invoice_payload = formatted_data
            api_log(msg="9")
            api_log(msg=f"[contact payload] : {invoice_payload}")
            # invoice_payload["erp_link_token_id"] = erp_link_token_id
            # invoice_payload["org_id"] = org_id
            api_log(msg="10")
            # api_log(msg=f"After erp link token {invoice_payload}")
            api_log(msg="11")
            # invoice_url = f"{self.KLOO_URL}/ap/erp-integration/insert-erp-invoices"
            # api_log(msg="12")
            #
            # invoice_response_data = requests.post(
            #     invoice_url,
            #     json=invoice_payload,
            #     stream=True,
            #     headers={"Authorization": f"Bearer {self.auth_token}"},
            # )
            # api_log(msg="13")
            # if invoice_response_data.status_code == status.HTTP_201_CREATED:
            #     api_log(msg="14")
            #     api_log(msg="data inserted successfully in the kloo Contacts system")
            # else:
            #     api_log(msg="15")
            #     api_log(msg=f"Failed to send data to Kloo Contacts API with status code {invoice_response_data.status_code}")
            # api_log(msg="16")
        except Exception as e:
            api_log(msg=f"Error in fetching contacts data : {e}")
            return


def format_merge_invoice_data(invoice_response, erp_link_token_id, org_id):
    """
    Format the merge invoice data
    """
    try:
        invoices_json = []
        for invoice in invoice_response["data"]:
            invoices_data = {
                "id": str(uuid.uuid4()),
                "erp_id": invoice.id,
                "organization_id": org_id,
                "erp_link_token_id": str(erp_link_token_id),
                "contact": invoice.contact,
                "number": invoice.number,
                "issue_date": (
                    invoice.issue_date.isoformat() if invoice.issue_date else None
                ),
                "due_date": (
                    invoice.due_date.isoformat() if invoice.due_date else None
                ),
                "paid_on_date": (
                    invoice.paid_on_date.isoformat() if invoice.paid_on_date else None
                ),
                "memo": invoice.memo,
                "company": invoice.company,
                "currency": (
                    get_currency_id(invoice.currency)[0] if invoice.currency else None
                ),
                "exchange_rate": invoice.exchange_rate,
                "total_discount": invoice.total_discount,
                "sub_total": invoice.sub_total,
                "erp_status": invoice.status,
                "total_tax_amount": invoice.total_tax_amount,
                "total_amount": invoice.total_amount,
                "balance": invoice.balance,
                "tracking_categories": (
                    [category for category in invoice.tracking_categories]
                    if invoice.tracking_categories is not None
                    else None
                ),
                "payments": (
                    [payment for payment in invoice.payments]
                    if invoice.payments is not None
                    else None
                ),
                "applied_payments": (
                    [applied_payment for applied_payment in invoice.applied_payments]
                    if invoice.applied_payments is not None
                    else None
                ),
                "line_items": (
                    [format_line_item(line_item) for line_item in invoice.line_items]
                    if invoice.line_items is not None
                    else None
                ),
                "accounting_period": invoice.accounting_period,
                "purchase_orders": (
                    [purchase_order for purchase_order in invoice.purchase_orders]
                    if invoice.purchase_orders is not None
                    else None
                ),
                "erp_created_at": (
                    invoice.created_at.isoformat() if invoice.created_at else None
                ),
                "erp_modified_at": (
                    invoice.modified_at.isoformat() if invoice.modified_at else None
                ),
                "erp_field_mappings": invoice.field_mappings,
                "erp_remote_data": (
                    [
                        invoice_remote_data.data
                        for invoice_remote_data in invoice.remote_data
                    ]
                    if invoice.remote_data is not None
                    else None
                ),
            }
            invoices_json.append(invoices_data)

        api_log(msg=f"Formatted merge invoice data: {invoices_json}")
        return invoices_json
    except Exception as e:
        api_log(msg=f"Error formatting merge invoice data: {e}")