import polars as pl
from django.core.management.base import BaseCommand
from merge.resources.accounting import (
    ContactsListRequestExpand,
)
from xlsxwriter import Workbook

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

        account_token = "0S4-SlQInQOJhaVQDZpwIxuUbqyyPnPgGHeXXQksafGTZrbRNo9w4A"

        try:
            contacts_client = create_merge_client(account_token)
            contact_data = contacts_client.accounting.contacts.list(
                expand=ContactsListRequestExpand.ADDRESSES,
                remote_fields="status",
                show_enum_origins="status",
                page_size=100,
                include_remote_data=True,
            )

            all_contact_data = []

            sheet_count = 1
            with Workbook("contact_data.xlsx") as wb:
                while True:
                    api_log(
                        msg=f"Adding {len(contact_data.results)} contacts to the list."
                    )

                    # Convert the data to a DataFrame
                    for contact in contact_data.results:
                        contact_df = {
                            "contact_id": contact.id,
                            "contact_name": contact.name,
                        }
                        api_log(msg=f"Contact: {contact_df}")
                        all_contact_data.append(contact_df)

                    df = pl.DataFrame(all_contact_data)

                    # Save the DataFrame to a CSV file
                    df.write_excel(
                        wb,
                        position=f"A{sheet_count}",
                    )

                    if contact_data.next is None:
                        break

                    all_contact_data = []
                    contact_data = contacts_client.accounting.contacts.list(
                        expand=ContactsListRequestExpand.ADDRESSES,
                        remote_fields="status",
                        show_enum_origins="status",
                        page_size=100,
                        include_remote_data=True,
                        cursor=contact_data.next,
                    )

                    sheet_count += 100

            api_log(msg=f"Total Contacts: {len(all_contact_data)}")

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


# def handle(self, *args, **options):
#         # get all linked account whose status are complete and daily force sync log is null
#         print("Adding Invoice Module for all completed linked accounts")
#
#         account_token = "0S4-SlQInQOJhaVQDZpwIxuUbqyyPnPgGHeXXQksafGTZrbRNo9w4A"
#         erp_link_token_id = "fcba2790-fc99-11ee-be1b-0242ac110008"
#
#         sql_query = f"""
#         SELECT * FROM erp_link_token
#         WHERE id = '{erp_link_token_id}'
#         """
#
#         with connection.cursor() as cursor:
#             cursor.execute(sql_query)
#             linked_accounts = cursor.fetchall()
#
#         api_log(msg=f"Total Linked Accounts: {linked_accounts}")
#
#         try:
#             contacts_client = create_merge_client(account_token)
#
#             contact_ids = [
#                 "6c0cd780-02e8-429d-bb5f-56cdb0a541cc",
#                 "cb14ebcf-5f26-42cb-b48f-c5a550e4cf24",
#                 "120676f7-85f0-4b15-8eb8-5cf253d34fce",
#                 "e1fc8f9e-4911-41e4-8e50-58c33cad52fb",
#                 "8af47c59-4e13-411b-bbfd-190cb39509a9",
#                 "b0f13273-9536-4f20-879f-9eeaf3e31581",
#                 "1d63af7d-3ebb-45d2-8d09-a23f89af5061",
#                 "9e514d63-ab4b-4803-8abe-ad8e997e5eb2",
#                 "65aed8d5-bb52-4952-8d23-60a7cf9d3048",
#                 "0849cf83-a6ee-4574-8bbe-4a7ab1e7c3b8",
#                 "cc9b4d4a-5b9f-4e03-8ab5-021181f92789",
#                 "40323f7f-7324-4600-ac7f-03859704beb5",
#                 "6905f604-5a48-4e7c-a7cf-55a22dee7021",
#                 "13f94adb-6979-4fcb-8e61-37ea6ce1ffe1",
#                 "8a344797-24ab-4aaa-a51f-1888777ba63f",
#                 "3bb54c9b-2ada-4061-845a-e1a740c8975e",
#                 "9effaac2-1628-488d-bb26-6eac1d9d9ea0",
#                 "6eee0f2e-3280-4529-a15b-3baeb6f7cb65",
#                 "9899841a-d174-4dd5-b4e2-d1384d82c2f0",
#                 "9cf9efc9-8193-4bba-847e-f622382c8591",
#                 "1ab69dce-890a-4f22-af1b-9b1ead3681d8",
#                 "10874edb-175a-4354-a985-062d09229528",
#                 "e91ed038-048f-4adf-beeb-7e7287bc20ec",
#                 "029af166-b251-4020-b43d-8c28f2d25a4c",
#                 "3abdd070-6ded-4962-93c0-00d63673f3d7",
#                 "2774697c-ebac-4f3d-8dbe-39783fdaae86",
#                 "27a6f4a2-e60f-4bc6-9251-37fdb7639c58",
#                 "5f50053f-920f-4a09-a1c7-ed2b2e9ecaf2",
#                 "9293a55d-73e5-42dc-a547-cb600eb27ee2",
#                 "66efc8da-6987-4d88-b9e0-79f163083d46",
#                 "e4ef4a94-62b6-4f30-8a09-4d29ae049ada",
#                 "8cb911a8-5ed1-4f7d-991f-22306c4f27c9",
#                 "e42b2d4c-c349-4636-a642-f091da95dafe",
#                 "9e4f3c31-1412-453b-ac5d-81159b45aa2c",
#                 "d02d87ad-54ea-4c13-8bc3-2070080dfc9d",
#                 "aee8fcb5-e1a4-4019-aeba-c11e5478679e",
#                 "b69c34e3-b9d1-4ce6-b993-b4431e1baf33",
#                 "96edb27e-9d65-4e84-8d0b-1fa06750ef2e",
#                 "b97c7705-5881-455b-9334-14714deb24ab",
#                 "78340090-6aab-4032-99fd-bfa57d7b77d7",
#                 "7d2ddff5-784e-4f2c-968b-9a79b0c5575c",
#                 "af067a7a-07b9-420f-85d4-98dddf1e0d85",
#                 "1bf05150-6c5f-41c1-8711-d11ff72b5c7b",
#                 "cd923064-2436-467c-99f3-e65aa5cbc718",
#                 "d84f6221-db68-4d30-8209-fa4b449f9373",
#                 "8a71d71f-d67c-44fc-bc1b-daddedb29d38",
#                 "fbcc2a7f-e0d3-446b-8f15-fdfa2f429854",
#                 "51e241b7-b021-478d-8497-8a3ba8208bdd",
#                 "6318d21e-8338-4e3c-b0cc-cd21a4b1bb9c",
#                 "e9d34982-762c-4b72-b238-8232ead41244",
#                 "e4db4d67-e615-47a1-a6e5-be17cb057741",
#                 "2bb873b1-af0c-4f27-bb74-70aeb4dd1143",
#                 "a7871ee0-21be-4fb0-89d3-ff5de5eb561e",
#                 "a0c45e6c-4b99-4fdd-b568-f8af6515af0d",
#                 "6d3a762f-b926-4a2e-8d19-f3dc7d7e54fb",
#                 "2bf5d56c-7aa3-4805-9112-adfb39305150",
#                 "f0b256f4-2c36-4182-9871-0ebdb851e55e",
#                 "9683c2f7-06f3-4659-ac4a-4bf22227359f",
#                 "b50e6922-ab48-4d7b-af20-c80cfac32339",
#                 "3d8bf584-951a-481c-8abb-fac9e7ec1cef",
#                 "d9820639-ebc8-4a6f-9051-94222230efdb",
#                 "1a2615d6-c1dc-49ae-93b5-88f9099099ed",
#                 "b36f5a45-e86d-48fa-be1d-ff09ee8392d5",
#                 "55b69dbc-d4d0-45a0-a62c-581ccfc01081",
#                 "3caa5bd9-0b70-4955-8361-24affcfe5eed",
#                 "620eebec-76ea-4614-84c9-937873e257b3",
#                 "4c534d57-1773-4557-a9ce-04038826b13f",
#                 "15db0077-942f-4d70-ab94-bb325bd12a6a",
#                 "feeacce1-a4bc-4f07-81bc-6d5449c6648d",
#                 "aadc564a-034f-4eda-9d07-2e3bb0092959",
#                 "79b17893-cde1-44cb-9909-fceec1b47b37",
#                 "139569ff-55b8-41d1-bbbc-04141356a81d",
#                 "28750bf0-7004-4dc5-a5f0-1d2a45637230",
#                 "3e9fb92d-d23b-46fe-90ad-bf4c723cc4d7",
#                 "56b90d6c-843c-4fa1-a816-6a5c255684de",
#                 "c2d10566-c509-489a-86f4-b79c27bd3eba",
#                 "7f472883-a383-4890-b902-b0a42ce22264",
#                 "41a8c1a7-8901-44a5-85ff-0f48c4d867b8",
#                 "624d58f4-cce8-4020-bba8-c1b1f7096c9d",
#                 "42217d69-abfb-4b30-833d-a56c5ef05cce",
#                 "dca3acad-3f6d-4d4f-9b0b-33a06f7dfdbc",
#                 "6a30bf77-f250-4037-9d64-64a63cd80d48",
#                 "7b6dc18f-2dcb-4ae6-83d8-c4d1a0ba3ac3",
#                 "2dd9e535-6c05-4cc8-8b74-a6d9be755319",
#                 "af5eb0f7-53a3-4497-a504-980eb6371399",
#                 "226129d5-4ce0-4153-aa04-afae7739a240",
#                 "96998040-734b-47a6-912b-0611fedff89b",
#                 "00f1a97c-b1dc-4129-920f-58350ec091e6",
#                 "ce1d7be5-402a-488b-8bd3-5e1fe5147f8b",
#                 "e6f92f99-3a15-4dd2-ae6b-a2704aa362e0",
#                 "8dc59317-745e-486b-b05a-477e6bdc30f8",
#                 "b0af3201-bb5e-48e1-8804-d2d380f9b3f7",
#                 "6270808a-6487-4d02-a893-bdc744b9b0b3",
#                 "bc11db8d-f0b4-4f78-9f97-bf85e709b8d5",
#                 "394f4832-e4c8-46cb-910e-38fdc0bba2b4",
#                 "5845f5b3-93c4-4c5d-aae0-1c003c025210",
#                 "1255f1b5-eb62-4c7a-96e8-df70243be08a",
#                 "22708a96-eb3e-44a8-bbe2-3804c0af8295",
#                 "fa606799-4318-4e8b-a41d-f5c270ed9737",
#                 "fcc6619b-c436-4faf-8337-381254197e46",
#                 "ab910de3-e214-4953-a056-ccc46cf4f866",
#                 "83a06f1f-b570-478c-99e1-cf35068484e8",
#                 "e7cd1dfd-766c-450d-a43e-e9163792aea8",
#                 "73416018-4682-4703-bddd-dbefc536054c",
#                 "149b201e-a9a4-4510-83df-77fbf17b744f",
#                 "7807faf2-c18a-4130-9a5a-76ce47e9c3e4",
#                 "606f27cf-d710-47b3-aebc-7586e5aa97ea",
#                 "8ab38986-5b9e-421a-aacc-74eec410556a",
#                 "cfa4e1ed-1539-45b1-b328-ae52a934ff22",
#                 "4860d2c1-7747-4c55-a0d9-56e57b0db156",
#                 "d112f9ce-7a39-4bd8-85e2-ade855f46731",
#                 "eaae1190-ce6f-42db-bf42-2780df67b159",
#                 "c3338197-9836-416d-aa3c-0b778386482a",
#                 "abd53c6e-9a37-4d14-997c-03271ea00f1e",
#                 "fc7f0f29-5d48-4477-b91e-9a2ea3744230",
#                 "c825772d-e27b-445d-8aa5-8601eb955112",
#                 "6bcee8cf-d1a6-49ec-bd9b-3601b5bf2538",
#                 "b102cb54-39e1-45e1-b3cf-60842f949e26",
#                 "11b86c4e-01aa-4f5b-909f-dfd2803aec57",
#                 "588612cd-040c-4f02-a6cc-e1d24c2657c0",
#             ]
#
#             api_log(msg=f"Total Contacts: {len(contact_ids)}")
#
#             contacts = []
#             for contact_id in contact_ids:
#                 contact = contacts_client.accounting.contacts.retrieve(
#                     id=contact_id,
#                     expand=ContactsRetrieveRequestExpand.ADDRESSES,
#                     remote_fields="status",
#                     show_enum_origins="status",
#                     include_remote_data=True,
#                 )
#                 contacts.append(contact)
#
#                 # api_log(msg=f"Contact: {contact}")
#
#             formatted_data = format_contact_data(contacts)
#             api_log(msg=f"Formatted Data: {len(formatted_data)}")
#
#             # contact_data = contacts_client.accounting.contacts.list(
#             #     expand=ContactsListRequestExpand.ADDRESSES,
#             #     remote_fields="status",
#             #     show_enum_origins="status",
#             #     page_size=100,
#             #     include_remote_data=True,
#             # )
#             #
#             # all_contact_data = []
#             # while True:
#             #     api_log(msg=f"Adding {len(contact_data.results)} contacts to the list.")
#             #
#             #     all_contact_data.extend(contact_data.results)
#             #     if contact_data.next is None:
#             #         break
#             #
#             #     all_contact_data = []
#             #     contact_data = contacts_client.accounting.contacts.list(
#             #         expand=ContactsListRequestExpand.ADDRESSES,
#             #         remote_fields="status",
#             #         show_enum_origins="status",
#             #         page_size=100,
#             #         include_remote_data=True,
#             #         cursor=contact_data.next,
#             #     )
#
#             # api_log(msg=f"Total Contacts: {len(all_contact_data)}")
#             #
#             # formatted_data = format_contact_data(all_contact_data)
#             #
#             contact_payload = formatted_data
#             contact_payload["erp_link_token_id"] = erp_link_token_id
#             contact_payload["org_id"] = "78d87d0e-8dc8-11ee-9a90-0a1c22ac2fa6"
#
#             contact_url = f"{GETKLOO_LOCAL_URL}/ap/erp-integration/insert-erp-contacts"
#
#             auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiIyMDNiOTM2NzY0NDBkYTQ3MTcxZjMzMTZlYjVlZjc2MTc5OTQ1YjA0MDhmM2EwZmFkZWVkZWFmZWFkYjM3ZjBmYzhmMzdmYzkxYzg0NTdlNyIsImlhdCI6MTcxMzUxMDEwNi41OTYwMzEsIm5iZiI6MTcxMzUxMDEwNi41OTYwMzMsImV4cCI6MTcxMzUxMDQwNi41NjczMDYsInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiOWI2MTJiMzctMmYyNi00Y2ZjLWI4OWQtNjY2YmNhMTZmMzQ1XCIsXCJmaXJzdF9uYW1lXCI6XCJBbmlrZXRcIixcIm1pZGRsZV9uYW1lXCI6bnVsbCxcImxhc3RfbmFtZVwiOlwiS2hlcmFsaXlhIE9BIG9uZVwiLFwiZW1haWxcIjpcImFuaWtldC5raGVyYWxpeWErb2ExQGJsZW5oZWltY2hhbGNvdC5jb21cIixcImJpcnRoX2RhdGVcIjpcIjE5OTQtMTAtMTZcIixcInVzZXJfY3JlYXRlZF9ieVwiOm51bGwsXCJsb2dpbl9hdHRlbXB0c1wiOjAsXCJzdGF0dXNcIjpcInVuYmxvY2tlZFwiLFwiY3JlYXRlZF9hdFwiOlwiMjAyNC0wMy0wN1QwNToyNDozOC4wMDAwMDBaXCIsXCJ1cGRhdGVkX2F0XCI6XCIyMDI0LTAzLTA3VDA1OjI2OjM3LjAwMDAwMFpcIixcInVzZXJfb3JnX2lkXCI6XCJlMDEwOWRlNS1iNDM1LTQ0OWYtYjBkYS04ZjhjZjY2ZDY4NjFcIixcIm9yZ2FuaXphdGlvbl9pZFwiOlwiMGY5MDU2YzQtOTg0YS00NDMxLWEzYWEtZGIyY2MxNDdkNTk3XCIsXCJvcmdhbml6YXRpb25fbmFtZVwiOlwiS2xvbyBRQVwifSxcInNjb3Blc1wiOltcImFsbC1jYXJkcy1yZWFkXCIsXCJteS1jYXJkcy1yZWFkXCIsXCJpc3N1ZS1jYXJkLWNyZWF0ZVwiLFwiYWN0aXZhdGUtcGh5c2ljYWwtY2FyZC11cGRhdGVcIixcInZpcnR1YWwtY2FyZHMtY3JlYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLXJlYWRcIixcInZpcnR1YWwtY2FyZHMtdXBkYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLWRlbGV0ZVwiLFwicGh5c2ljYWwtY2FyZHMtY3JlYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1yZWFkXCIsXCJwaHlzaWNhbC1jYXJkcy11cGRhdGVcIixcInBoeXNpY2FsLWNhcmRzLWRlbGV0ZVwiLFwiY2FyZC1saW1pdC11cGRhdGVcIixcImNhcmQtbmlja25hbWUtdXBkYXRlXCIsXCJjYW5jZWwtY2FyZC11cGRhdGVcIixcImZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwidW5mcmVlemUtY2FyZC11cGRhdGVcIixcImNhcmQtc3RhdHVzLXVwZGF0ZVwiLFwiY2FyZC1kb3dubG9hZHMtaW1wb3J0XCIsXCJ1c2Vycy1jcmVhdGVcIixcInVzZXJzLXJlYWRcIixcInVzZXJzLXVwZGF0ZVwiLFwidXNlcnMtZGVsZXRlXCIsXCJpbnZpdGF0aW9uLWxpbmstc2VuZFwiLFwiaGVhbHRoLWNoZWNrLXJlYWRcIixcIm5vdGlmaWNhdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLWNyZWF0ZVwiLFwib3JnYW5pemF0aW9uLXJlYWRcIixcIm9yZ2FuaXphdGlvbi11cGRhdGVcIixcIm9yZ2FuaXphdGlvbi1kZWxldGVcIixcIm9yZ2FuaXphdGlvbi1tb2R1bHItYWNjb3VudC1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtY3JlYXRlXCIsXCJ0cmFuc2FjdGlvbnMtcmVhZFwiLFwidHJhbnNhY3Rpb25zLXVwZGF0ZVwiLFwidHJhbnNhY3Rpb25zLWRlbGV0ZVwiLFwidXNlci10cmFuc2FjdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJjdXN0b21lci1jcmVhdGVcIixcImNvbXBhbnktcmVhZFwiLFwib3JnYW5pemF0aW9uLWFuYWx5dGljcy1yZWFkXCIsXCJ1c2VyLWFuYWx5dGljcy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtdXBkYXRlXCIsXCJjYXJkLXJlcXVlc3RzLWRlbGV0ZVwiLFwidGVhbXMtY3JlYXRlXCIsXCJ0ZWFtcy1yZWFkXCIsXCJ0ZWFtcy11cGRhdGVcIixcInRlYW1zLWRlbGV0ZVwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWNyZWF0ZVwiLFwiY2hhcmdlYmVlLXN1YnNjcmlwdGlvbi1yZWFkXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItYmlsbC1yZWFkXCIsXCJjaGFyZ2ViZWUtaW52b2ljZS1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXN1YnNjcmlwdGlvbnMtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1yZWFkXCIsXCJhcC1pbnZvaWNlLWNyZWF0ZVwiLFwiYXAtaW52b2ljZS1yZWFkXCIsXCJhcC1pbnZvaWNlLXVwZGF0ZVwiLFwic2V0dGluZy1yZWFkXCIsXCJzZXR0aW5nLWludGVncmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3JpZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcmVhZFwiLFwic2V0dGluZy1hZGRyZXNzLXJlYWRcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1jcmVhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1yZWFkXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtZGVsZXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLWNyZWF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1yZWFkXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLXVwZGF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1kZWxldGVcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1jZS1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWFwLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcG8tcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtY2FyZHMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaW52b2ljZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcHVyY2hhc2Utb3JkZXJzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWhpc3RvcnktcmVhZFwiLFwic2V0dGluZy1wYXllZS1tYW5hZ2VtZW50LXJlYWRcIixcImRhc2hib2FyZC1yZWFkXCIsXCJhcHByb3ZhbHMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1kb3dubG9hZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstZm9yLXJldmlldy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtbWFyay1hcy1hcHByb3ZlZC11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtc2F2ZS1hcy1kcmFmdC11cGRhdGVcIixcInhlcm8tYW5hbHlzaXMtcmVhZFwiLFwia2xvby1zcGVuZC1yZWFkXCIsXCJwYXktbm93LWJ1dHRvbi1yZWFkXCIsXCJhY2NvdW50LWRldGFpbHMtcmVhZFwiLFwiZGViaXQtYWNjb3VudC1jcmVhdGVcIixcImRlYml0LWFjY291bnQtcmVhZFwiLFwiZGViaXQtYWNjb3VudC11cGRhdGVcIixcImRlYml0LWFjY291bnQtZGVsZXRlXCIsXCJzdGFuZGluZy1vcmRlci1jcmVhdGVcIixcInN0YW5kaW5nLW9yZGVyLXJlYWRcIixcImltbWVkaWF0ZS1wYXltZW50LWNyZWF0ZVwiLFwiaW1tZWRpYXRlLXBheW1lbnQtcmVhZFwiLFwiYmFuay10cmFuc2Zlci1jcmVhdGVcIixcImJhbmstdHJhbnNmZXItcmVhZFwiLFwic2NoZWR1bGVkLXJlYWRcIixcImhpc3RvcnktcmVhZFwiLFwicHJvZmlsZS1yZWFkXCIsXCJwcm9maWxlLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWNyZWF0ZVwiLFwic3Vic2NyaXB0aW9uLXJlYWRcIixcInN1YnNjcmlwdGlvbi11cGRhdGVcIixcInN1YnNjcmlwdGlvbi1kZWxldGVcIixcInB1cmNoYXNlLW9yZGVyLWNyZWF0ZVwiLFwicHVyY2hhc2Utb3JkZXItcmVhZFwiLFwicHVyY2hhc2Utb3JkZXItdXBkYXRlXCIsXCJzY2hlZHVsZS1wYXltZW50LWJ1dHRvbi1yZWFkXCIsXCJjcmVkaXQtbm90ZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcGF5bWVudC1ydW5zLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXNjaGVkdWxlLXJlYWRcIixcInNjaGVkdWxlLXRhYi1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy10YXgtY29kZS1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1vcmdhbmlzYXRpb24tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1zdXBwbGllci1yZWFkXCIsXCJkYXNoYm9hcmQtaW0tcmVhZFwiLFwiaW52b2ljZS1tYXRjaGluZy1wby1yZWFkXCIsXCJwYXltZW50LXJ1bnMtY3JlYXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwicGF5bWVudC1ydW5zLXVwZGF0ZVwiLFwicGF5bWVudC1ydW5zLWRlbGV0ZVwiLFwiZGFzaGJvYXJkLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXBvLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWVudGl0eS1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jcmVkaXQtbm90ZXMtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtYXV0b21hdGljLWVtYWlsLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiLFwicGF5ZWUtY29udGFjdC1uby1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wcmVmaXgtcG8tcmVhZFwiLFwicm9sZXMtY3JlYXRlXCIsXCJyb2xlcy1yZWFkXCIsXCJyb2xlcy11cGRhdGVcIixcInJvbGVzLWRlbGV0ZVwiXSxcInJvbGVcIjp7XCJpZFwiOlwiMjMyNzNjMTAtZDQ4Yi0xMWVkLWIyNmEtMTllZGUwMjViZDIwXCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.fdKSnX5LqcStch7T59HdjJJ408zeF7Xhdx3qoECdXlDtJi1-An-AXThHFdo1tfC0JCKJRqewZbkrIq6EXOqzLU2FYS6EKEjyZI-u77tW5oLiTyZmF5hD8fh50teBipj8rObmM0shO8-S4WekvD8Jp-_dIPvJQJT0zJzks7AkTbCrq1_ZIyRRwfd2nXTikfl2vc2kpgOASebQLmCjRCjHMdoHg8t6Wtlyh2_6UKlTZkdfkqwlTsAKtBdAAjNix7YqYrN1ReBlLWOQ8V0sqXG4rNmxMbq_F3x9f8k5jM_RDa3HEn27IzEKn04kTXVFe_367SU3AjJk7trFwpVDS1NUrQIFN3xw0wDBPGM72pFwVrgZl4kLC5ZJtjkRZomuQzrTdJLBtgsxmvLZHxvyhbXKDoLi9FvFVpkdUWBSIXH_B1PPzBFH57wz7LMeZ6FR5-0xVxhIFBArXZAO_QgHLKwxCMVOjovSWRI3fL7bBx009YVyzqzFEwLFQEjPIUzgv3cFo0WVYrN-tAAnuxQI5vTSL7jbOTLFsk1ifVbkFlRHNj8VPPw2Mbyi1zV3XBWv_4EHOIRYE-EilZmEWAQJC1Ntv94i_qzvID01qotCW3X7rMEZFd2nCovn8hZn3adbTciMPu_B3eJ8nusn1Cj2B4r7-Je3BmsVjpZko5cYgIRtbXE"
#
#             contact_response_data = requests.post(
#                 contact_url,
#                 json=contact_payload,
#                 headers={"Authorization": f"Bearer {auth_token}"},
#             )
#
#             if contact_response_data.status_code == status.HTTP_201_CREATED:
#                 api_log(msg="data inserted successfully in the kloo Contacts system")
#             else:
#                 api_log(msg="Failed to send data to Kloo Contacts API")
#
#         except Exception as e:
#             api_log(msg=f"Error in fetching contacts data : {e}")
#             return
