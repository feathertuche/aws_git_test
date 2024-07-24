import requests
from django.core.management.base import BaseCommand
from merge.resources.accounting import (
    ContactsListRequestExpand,
)
from rest_framework import status

from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_BASE_URL
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

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = ""
        erp_link_token_id = ""
        org_id = ""
        auth_token = ""

        try:
            contacts_client = create_merge_client(account_token)

            contacts = []

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

                contacts.extend(contact_data.results)

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

            api_log(msg=f"Total Contacts: {len(contacts)}")

            formatted_data = format_contact_data(contacts)
            contact_payload = formatted_data
            contact_payload["erp_link_token_id"] = erp_link_token_id
            contact_payload["org_id"] = org_id
            contact_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/insert-erp-contacts"
            contact_response_data = requests.post(
                contact_url,
                json=contact_payload,
                headers={"Authorization": f"Bearer {auth_token}"},
            )

            if contact_response_data.status_code == status.HTTP_201_CREATED:
                api_log(msg="14")
                api_log(msg="data inserted successfully in the kloo Contacts system")
            else:
                api_log(msg="15")
                api_log(
                    msg=f"Failed to send data to Kloo Contacts API with status code {contact_response_data.status_code}"
                )
            api_log(msg="16")
        except Exception as e:
            api_log(msg=f"Error in fetching contacts data : {e}")
            return


def format_contact_data(contact_data: list):
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
