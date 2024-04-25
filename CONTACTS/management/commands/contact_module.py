from django.core.management.base import BaseCommand
from django.db import connection
from merge.resources.accounting import (
    ContactsRetrieveRequestExpand,
)

from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts
    """

    help = "Add Contacts Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = ""
        erp_link_token_id = ""

        sql_query = f"""
            SELECT * FROM erp_link_token
            WHERE id = '{erp_link_token_id}'
            """

        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            linked_accounts = cursor.fetchall()

        api_log(msg=f"Total Linked Accounts: {linked_accounts}")

        try:
            contacts_client = create_merge_client(account_token)

            contact_ids = [
                "6c0cd780-02e8-429d-bb5f-56cdb0a541cc",
            ]

            api_log(msg=f"Total Contacts: {len(contact_ids)}")

            contacts = []
            for contact_id in contact_ids:
                contact = contacts_client.accounting.contacts.retrieve(
                    id=contact_id,
                    expand=ContactsRetrieveRequestExpand.ADDRESSES,
                    remote_fields="status",
                    show_enum_origins="status",
                    include_remote_data=True,
                )
                contacts.append(contact)

                # api_log(msg=f"Contact: {contact}")

            formatted_data = format_contact_data(contacts)
            api_log(msg=f"Formatted Data: {len(formatted_data)}")

            # contact_data = contacts_client.accounting.contacts.list(
            #     expand=ContactsListRequestExpand.ADDRESSES,
            #     remote_fields="status",
            #     show_enum_origins="status",
            #     page_size=100,
            #     include_remote_data=True,
            # )
            #
            # all_contact_data = []
            # while True:
            #     api_log(msg=f"Adding {len(contact_data.results)} contacts to the list.")
            #
            #     all_contact_data.extend(contact_data.results)
            #     if contact_data.next is None:
            #         break
            #
            #     all_contact_data = []
            #     contact_data = contacts_client.accounting.contacts.list(
            #         expand=ContactsListRequestExpand.ADDRESSES,
            #         remote_fields="status",
            #         show_enum_origins="status",
            #         page_size=100,
            #         include_remote_data=True,
            #         cursor=contact_data.next,
            #     )

            # api_log(msg=f"Total Contacts: {len(all_contact_data)}")
            #
            # formatted_data = format_contact_data(all_contact_data)
            #
            # contact_payload = formatted_data
            # contact_payload["erp_link_token_id"] = erp_link_token_id
            # contact_payload["org_id"] = "78d87d0e-8dc8-11ee-9a90-0a1c22ac2fa6"
            #
            # contact_url = f"{GETKLOO_LOCAL_URL}/ap/erp-integration/insert-erp-contacts"
            #
            # auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiIyMDNiOTM2NzY0NDBkYTQ3MTcxZjMzMTZlYjVlZjc2MTc5OTQ1YjA0MDhmM2EwZmFkZWVkZWFmZWFkYjM3ZjBmYzhmMzdmYzkxYzg0NTdlNyIsImlhdCI6MTcxMzUxMDEwNi41OTYwMzEsIm5iZiI6MTcxMzUxMDEwNi41OTYwMzMsImV4cCI6MTcxMzUxMDQwNi41NjczMDYsInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiOWI2MTJiMzctMmYyNi00Y2ZjLWI4OWQtNjY2YmNhMTZmMzQ1XCIsXCJmaXJzdF9uYW1lXCI6XCJBbmlrZXRcIixcIm1pZGRsZV9uYW1lXCI6bnVsbCxcImxhc3RfbmFtZVwiOlwiS2hlcmFsaXlhIE9BIG9uZVwiLFwiZW1haWxcIjpcImFuaWtldC5raGVyYWxpeWErb2ExQGJsZW5oZWltY2hhbGNvdC5jb21cIixcImJpcnRoX2RhdGVcIjpcIjE5OTQtMTAtMTZcIixcInVzZXJfY3JlYXRlZF9ieVwiOm51bGwsXCJsb2dpbl9hdHRlbXB0c1wiOjAsXCJzdGF0dXNcIjpcInVuYmxvY2tlZFwiLFwiY3JlYXRlZF9hdFwiOlwiMjAyNC0wMy0wN1QwNToyNDozOC4wMDAwMDBaXCIsXCJ1cGRhdGVkX2F0XCI6XCIyMDI0LTAzLTA3VDA1OjI2OjM3LjAwMDAwMFpcIixcInVzZXJfb3JnX2lkXCI6XCJlMDEwOWRlNS1iNDM1LTQ0OWYtYjBkYS04ZjhjZjY2ZDY4NjFcIixcIm9yZ2FuaXphdGlvbl9pZFwiOlwiMGY5MDU2YzQtOTg0YS00NDMxLWEzYWEtZGIyY2MxNDdkNTk3XCIsXCJvcmdhbml6YXRpb25fbmFtZVwiOlwiS2xvbyBRQVwifSxcInNjb3Blc1wiOltcImFsbC1jYXJkcy1yZWFkXCIsXCJteS1jYXJkcy1yZWFkXCIsXCJpc3N1ZS1jYXJkLWNyZWF0ZVwiLFwiYWN0aXZhdGUtcGh5c2ljYWwtY2FyZC11cGRhdGVcIixcInZpcnR1YWwtY2FyZHMtY3JlYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLXJlYWRcIixcInZpcnR1YWwtY2FyZHMtdXBkYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLWRlbGV0ZVwiLFwicGh5c2ljYWwtY2FyZHMtY3JlYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1yZWFkXCIsXCJwaHlzaWNhbC1jYXJkcy11cGRhdGVcIixcInBoeXNpY2FsLWNhcmRzLWRlbGV0ZVwiLFwiY2FyZC1saW1pdC11cGRhdGVcIixcImNhcmQtbmlja25hbWUtdXBkYXRlXCIsXCJjYW5jZWwtY2FyZC11cGRhdGVcIixcImZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwidW5mcmVlemUtY2FyZC11cGRhdGVcIixcImNhcmQtc3RhdHVzLXVwZGF0ZVwiLFwiY2FyZC1kb3dubG9hZHMtaW1wb3J0XCIsXCJ1c2Vycy1jcmVhdGVcIixcInVzZXJzLXJlYWRcIixcInVzZXJzLXVwZGF0ZVwiLFwidXNlcnMtZGVsZXRlXCIsXCJpbnZpdGF0aW9uLWxpbmstc2VuZFwiLFwiaGVhbHRoLWNoZWNrLXJlYWRcIixcIm5vdGlmaWNhdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLWNyZWF0ZVwiLFwib3JnYW5pemF0aW9uLXJlYWRcIixcIm9yZ2FuaXphdGlvbi11cGRhdGVcIixcIm9yZ2FuaXphdGlvbi1kZWxldGVcIixcIm9yZ2FuaXphdGlvbi1tb2R1bHItYWNjb3VudC1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtY3JlYXRlXCIsXCJ0cmFuc2FjdGlvbnMtcmVhZFwiLFwidHJhbnNhY3Rpb25zLXVwZGF0ZVwiLFwidHJhbnNhY3Rpb25zLWRlbGV0ZVwiLFwidXNlci10cmFuc2FjdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJjdXN0b21lci1jcmVhdGVcIixcImNvbXBhbnktcmVhZFwiLFwib3JnYW5pemF0aW9uLWFuYWx5dGljcy1yZWFkXCIsXCJ1c2VyLWFuYWx5dGljcy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtdXBkYXRlXCIsXCJjYXJkLXJlcXVlc3RzLWRlbGV0ZVwiLFwidGVhbXMtY3JlYXRlXCIsXCJ0ZWFtcy1yZWFkXCIsXCJ0ZWFtcy11cGRhdGVcIixcInRlYW1zLWRlbGV0ZVwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWNyZWF0ZVwiLFwiY2hhcmdlYmVlLXN1YnNjcmlwdGlvbi1yZWFkXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItYmlsbC1yZWFkXCIsXCJjaGFyZ2ViZWUtaW52b2ljZS1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXN1YnNjcmlwdGlvbnMtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1yZWFkXCIsXCJhcC1pbnZvaWNlLWNyZWF0ZVwiLFwiYXAtaW52b2ljZS1yZWFkXCIsXCJhcC1pbnZvaWNlLXVwZGF0ZVwiLFwic2V0dGluZy1yZWFkXCIsXCJzZXR0aW5nLWludGVncmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3JpZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcmVhZFwiLFwic2V0dGluZy1hZGRyZXNzLXJlYWRcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1jcmVhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1yZWFkXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtZGVsZXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLWNyZWF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1yZWFkXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLXVwZGF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1kZWxldGVcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1jZS1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWFwLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcG8tcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtY2FyZHMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaW52b2ljZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcHVyY2hhc2Utb3JkZXJzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWhpc3RvcnktcmVhZFwiLFwic2V0dGluZy1wYXllZS1tYW5hZ2VtZW50LXJlYWRcIixcImRhc2hib2FyZC1yZWFkXCIsXCJhcHByb3ZhbHMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1kb3dubG9hZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstZm9yLXJldmlldy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtbWFyay1hcy1hcHByb3ZlZC11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtc2F2ZS1hcy1kcmFmdC11cGRhdGVcIixcInhlcm8tYW5hbHlzaXMtcmVhZFwiLFwia2xvby1zcGVuZC1yZWFkXCIsXCJwYXktbm93LWJ1dHRvbi1yZWFkXCIsXCJhY2NvdW50LWRldGFpbHMtcmVhZFwiLFwiZGViaXQtYWNjb3VudC1jcmVhdGVcIixcImRlYml0LWFjY291bnQtcmVhZFwiLFwiZGViaXQtYWNjb3VudC11cGRhdGVcIixcImRlYml0LWFjY291bnQtZGVsZXRlXCIsXCJzdGFuZGluZy1vcmRlci1jcmVhdGVcIixcInN0YW5kaW5nLW9yZGVyLXJlYWRcIixcImltbWVkaWF0ZS1wYXltZW50LWNyZWF0ZVwiLFwiaW1tZWRpYXRlLXBheW1lbnQtcmVhZFwiLFwiYmFuay10cmFuc2Zlci1jcmVhdGVcIixcImJhbmstdHJhbnNmZXItcmVhZFwiLFwic2NoZWR1bGVkLXJlYWRcIixcImhpc3RvcnktcmVhZFwiLFwicHJvZmlsZS1yZWFkXCIsXCJwcm9maWxlLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWNyZWF0ZVwiLFwic3Vic2NyaXB0aW9uLXJlYWRcIixcInN1YnNjcmlwdGlvbi11cGRhdGVcIixcInN1YnNjcmlwdGlvbi1kZWxldGVcIixcInB1cmNoYXNlLW9yZGVyLWNyZWF0ZVwiLFwicHVyY2hhc2Utb3JkZXItcmVhZFwiLFwicHVyY2hhc2Utb3JkZXItdXBkYXRlXCIsXCJzY2hlZHVsZS1wYXltZW50LWJ1dHRvbi1yZWFkXCIsXCJjcmVkaXQtbm90ZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcGF5bWVudC1ydW5zLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXNjaGVkdWxlLXJlYWRcIixcInNjaGVkdWxlLXRhYi1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy10YXgtY29kZS1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1vcmdhbmlzYXRpb24tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1zdXBwbGllci1yZWFkXCIsXCJkYXNoYm9hcmQtaW0tcmVhZFwiLFwiaW52b2ljZS1tYXRjaGluZy1wby1yZWFkXCIsXCJwYXltZW50LXJ1bnMtY3JlYXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwicGF5bWVudC1ydW5zLXVwZGF0ZVwiLFwicGF5bWVudC1ydW5zLWRlbGV0ZVwiLFwiZGFzaGJvYXJkLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWVudGl0eS1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jcmVkaXQtbm90ZXMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtYXV0b21hdGljLWVtYWlsLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiLFwicGF5ZWUtY29udGFjdC1uby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wcmVmaXgtcG8tcmVhZFwiLFwicm9sZXMtY3JlYXRlXCIsXCJyb2xlcy1yZWFkXCIsXCJyb2xlcy11cGRhdGVcIixcInJvbGVzLWRlbGV0ZVwiXSxcInJvbGVcIjp7XCJpZFwiOlwiMjMyNzNjMTAtZDQ4Yi0xMWVkLWIyNmEtMTllZGUwMjViZDIwXCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.fdKSnX5LqcStch7T59HdjJJ408zeF7Xhdx3qoECdXlDtJi1-An-AXThHFdo1tfC0JCKJRqewZbkrIq6EXOqzLU2FYS6EKEjyZI-u77tW5oLiTyZmF5hD8fh50teBipj8rObmM0shO8-S4WekvD8Jp-_dIPvJQJT0zJzks7AkTbCrq1_ZIyRRwfd2nXTikfl2vc2kpgOASebQLmCjRCjHMdoHg8t6Wtlyh2_6UKlTZkdfkqwlTsAKtBdAAjNix7YqYrN1ReBlLWOQ8V0sqXG4rNmxMbq_F3x9f8k5jM_RDa3HEn27IzEKn04kTXVFe_367SU3AjJk7trFwpVDS1NUrQIFN3xw0wDBPGM72pFwVrgZl4kLC5ZJtjkRZomuQzrTdJLBtgsxmvLZHxvyhbXKDoLi9FvFVpkdUWBSIXH_B1PPzBFH57wz7LMeZ6FR5-0xVxhIFBArXZAO_QgHLKwxCMVOjovSWRI3fL7bBx009YVyzqzFEwLFQEjPIUzgv3cFo0WVYrN-tAAnuxQI5vTSL7jbOTLFsk1ifVbkFlRHNj8VPPw2Mbyi1zV3XBWv_4EHOIRYE-EilZmEWAQJC1Ntv94i_qzvID01qotCW3X7rMEZFd2nCovn8hZn3adbTciMPu_B3eJ8nusn1Cj2B4r7-Je3BmsVjpZko5cYgIRtbXE"
            #
            # contact_response_data = requests.post(
            #     contact_url,
            #     json=contact_payload,
            #     headers={"Authorization": f"Bearer {auth_token}"},
            # )
            #
            # if contact_response_data.status_code == status.HTTP_201_CREATED:
            #     api_log(msg="data inserted successfully in the kloo Contacts system")
            # else:
            #     api_log(msg="Failed to send data to Kloo Contacts API")

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
