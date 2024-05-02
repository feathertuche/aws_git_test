import requests
from django.core.management.base import BaseCommand
from merge.resources.accounting import (
    ContactsListRequestExpand,
    ContactsRetrieveRequestExpand,
)
from rest_framework import status
import tenacity
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL, GETKLOO_BASE_URL
from merge_integration.utils import create_merge_client


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
            contacts_client = create_merge_client(account_token)

            suppliers_name_list = ["Bigbearpromo LTD"]
            contact_ids = []

            contact_data = contacts_client.accounting.contacts.list(
                expand=ContactsListRequestExpand.ADDRESSES,
                remote_fields="status",
                is_supplier=True,
                show_enum_origins="status",
                page_size=100,
                include_remote_data=True,
            )
            while True:
                api_log(msg=f"Adding {len(contact_data.results)} contacts to the list.")
                for contact in contact_data.results:
                    # api_log(msg=f"[CONTACT name LIST] : {contact.name} and {contact.id}")
                    contact_ids.append(contact.id)
                    api_log(msg=f"[after append CONTACT name LIST] : {contact.name} and {contact.id}")
                    #break
                    # else:
                    #     api_log(msg="No Name")

                if contact_data.next is None:
                    break

                contact_data = contacts_client.accounting.contacts.list(
                    expand=ContactsListRequestExpand.ADDRESSES,
                    remote_fields="status",
                    is_supplier=True,
                    show_enum_origins="status",
                    page_size=100,
                    include_remote_data=True,
                    cursor=contact_data.next,
                )

            api_log(msg=f"Total Contacts: {contact_ids}")
            api_log(msg="1")

            contacts = []
            api_log(msg="2")
            for contact_id in contact_ids:
                api_log(msg="3")
                api_log(msg=f"Total Contact ids in retrive bloc: {contact_ids}")
                contact = contacts_client.accounting.contacts.retrieve(
                    id=contact_id,
                    expand=ContactsRetrieveRequestExpand.ADDRESSES,
                    remote_fields="status",
                    show_enum_origins="status",
                    include_remote_data=True,
                )
                api_log(msg="4")
                contacts.append(contact)
                api_log(msg="5")
                api_log(msg=f"[CONTACTS LIST] : {contacts}")
            # api_log(msg=f"[CONTACTS LIST outside for loop] : {contacts}")
            api_log(msg="6")
            formatted_data = format_contact_data(contacts)
            api_log(msg="7")
            api_log(msg=f"[FORMATTED DATA] : {formatted_data}")
            api_log(msg=f"Formatted Data: {len(formatted_data)}")
            api_log(msg="8")
            contact_payload = formatted_data
            api_log(msg="9")
            # api_log(msg=f"[contact payload] : {contact_payload}")
            contact_payload["erp_link_token_id"] = erp_link_token_id
            contact_payload["org_id"] = org_id
            api_log(msg="10")
            api_log(msg=f"After erp link token {contact_payload}")
            api_log(msg="11")
            contact_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/insert-erp-contacts"
            api_log(msg="12")
            contact_response_data = requests.post(
                contact_url,
                json=contact_payload,
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            api_log(msg="13")
            if contact_response_data.status_code == status.HTTP_201_CREATED:
                api_log(msg="14")
                api_log(msg="data inserted successfully in the kloo Contacts system")
            else:
                api_log(msg="15")
                api_log(msg=f"Failed to send data to Kloo Contacts API with status code {contact_response_data.status_code}")
            api_log(msg="16")
        except Exception as e:
            api_log(msg=f"Error in fetching contacts data : {e}")
            return


def format_contact_data(contact_data):
    formatted_data = []

    for contact in contact_data:
        erp_remote_data = None
        if contact.remote_data is not None:
            erp_remote_data = [
                contact_remote_data.data for contact_remote_data in contact.remote_data
            ]

        formatted_entry = {
            "id": contact.id,
            "remote_id": contact.remote_id,
            "name": contact.name,
            "is_supplier": contact.is_supplier,
            "is_customer": contact.is_customer,
            "email_address": contact.email_address,
            "tax_number": contact.tax_number,
            "status": contact.status,
            "currency": contact.currency,
            "remote_updated_at": contact.remote_updated_at.isoformat(),
            "company": contact.company,
            "addresses": [
                {
                    "type": addr.type,
                    "street_1": addr.street_1,
                    "street_2": addr.street_2,
                    "city": addr.city,
                    "state": addr.state,
                    "country_subdivision": addr.country_subdivision,
                    "country": addr.country,
                    "zip_code": addr.zip_code,
                    "created_at": addr.created_at.isoformat(),
                    "modified_at": addr.modified_at.isoformat(),
                }
                for addr in contact.addresses
            ],
            "phone_numbers": [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at.isoformat(),
                    "modified_at": phone.modified_at.isoformat(),
                }
                for phone in contact.phone_numbers
            ],
            "remote_was_deleted": contact.remote_was_deleted,
            "created_at": contact.created_at.isoformat(),
            "modified_at": contact.modified_at.isoformat(),
            "field_mappings": contact.field_mappings,
            "remote_data": erp_remote_data,
        }
        formatted_data.append(formatted_entry)
    kloo_format_json = {"erp_contacts": formatted_data}

    return kloo_format_json
