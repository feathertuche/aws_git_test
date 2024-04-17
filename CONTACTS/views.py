"""
Module docstring: This module provides functions related to traceback.
"""

import json
import traceback

import requests
from merge.client import Merge
from merge.resources.accounting import (
    ContactsListRequestExpand,
    ContactsRetrieveRequestExpand,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL, contacts_batch_size, contacts_page_size
from merge_integration.utils import create_merge_client


class MergeContactsList(APIView):
    """
    API view for retrieving Merge Contacts list.
    """

    def __init__(
        self,
        previous=None,
        results=None,
        link_token_details=None,
        last_modified_at=None,
    ):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at
        self.next = next
        self.previous = previous
        self.results = results

    def get_contacts(self):
        if self.link_token_details is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details
        api_log(msg=f"Account Token: {account_token}")
        contacts_client = create_merge_client(account_token)

        try:
            contact_data = contacts_client.accounting.contacts.list(
                expand=ContactsListRequestExpand.ADDRESSES,
                remote_fields="status",
                show_enum_origins="status",
                page_size=contacts_page_size,
                is_supplier=True,
                include_remote_data=True,
                modified_after=self.last_modified_at,
            )

            all_contact_data = []
            while True:
                api_log(msg=f"Adding {len(contact_data.results)} contacts to the list.")

                all_contact_data.extend(contact_data.results)
                if contact_data.next is None:
                    break

                contact_data = contacts_client.accounting.contacts.list(
                    expand=ContactsListRequestExpand.ADDRESSES,
                    remote_fields="status",
                    show_enum_origins="status",
                    page_size=contacts_page_size,
                    is_supplier=True,
                    include_remote_data=True,
                    modified_after=self.last_modified_at,
                    cursor=contact_data.next,
                )

                api_log(
                    msg=f"CONTACTS GET:: The length of the next page contacts data is : {len(contact_data.results)}"
                )
                api_log(msg=f"Length of all contact data: {len(contact_data.results)}")

            api_log(
                msg=f"CONTACTS GET:: The length of all contact data is : {len(all_contact_data)}"
            )

            return all_contact_data
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )

    @staticmethod
    def response_payload(contact_data):
        """
        Formats the contacts data retrieved from the Merge API into a specific format.

        Args:
            contact_data: Contacts data retrieved from the Merge API.

        Returns:
            Formatted contacts data.
        """
        formatted_data = []

        for contact in contact_data:
            erp_remote_data = None
            if contact.remote_data is not None:
                erp_remote_data = [
                    contact_remote_data.data
                    for contact_remote_data in contact.remote_data
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

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve contacts data.

        Returns:
            Response containing formatted contacts data.
        """
        api_log(msg="Processing GET request in Merge Contacts")

        contact_data = self.get_contacts()
        if contact_data is None or len(contact_data) == 0:
            return Response({"erp_contacts": []}, status=status.HTTP_204_NO_CONTENT)

        formatted_data = self.response_payload(contact_data)

        api_log(msg=f"Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergeContactDetails(APIView):
    """
    API view for retrieving details of a specific Merge Contact.
    """

    @staticmethod
    def get(_, id=None):
        """
        Retrieves details of a specific contact from the Merge API.

        Args:
            id: ID of the contact to retrieve details for.

        Returns:
            Response containing contact details.
        """
        api_log(msg="Processing GET request Merge Contacts list")
        merg_client = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY,
        )
        try:
            contact_data = merg_client.accounting.contacts.retrieve(
                id=id,
                expand=ContactsRetrieveRequestExpand.ADDRESSES,
                remote_fields="status",
                show_enum_origins="status",
            )

            formatted_addresses = [
                {
                    "type": addr.type,
                    "street_1": addr.street_1,
                    "street_2": addr.street_2,
                    "city": addr.city,
                    "state": addr.state,
                    "country_subdivision": addr.country_subdivision,
                    "country": addr.country,
                    "zip_code": addr.zip_code,
                    "created_at": addr.created_at,
                    "modified_at": addr.modified_at,
                }
                for addr in contact_data.addresses
            ]

            phone_types = [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at,
                    "modified_at": phone.modified_at,
                }
                for phone in contact_data.phone_numbers
            ]
            field_map = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {},
                },
            ]

            formatted_list = []
            format_response = {
                "id": contact_data.id,
                "remote_id": contact_data.remote_id,
                "name": contact_data.name,
                "is_supplier": contact_data.is_supplier,
                "is_customer": contact_data.is_customer,
                "email_address": contact_data.email_address,
                "tax_number": contact_data.tax_number,
                "status": contact_data.status,
                "currency": contact_data.currency,
                "remote_updated_at": contact_data.remote_updated_at,
                "company": contact_data.company,
                "addresses": formatted_addresses,
                "phone_numbers": phone_types,
                "remote_was_deleted": contact_data.remote_was_deleted,
                "created_at": contact_data.created_at,
                "modified_at": contact_data.modified_at,
                "field_mappings": field_map,
                "remote_data": contact_data.remote_data,
            }
            formatted_list.append(format_response)

            api_log(
                msg=f"FORMATTED DATA: {formatted_list} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
            )
            return Response(formatted_list, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving Contacts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergePostContacts(APIView):
    """
    API view for inserting Merge Contact data into the Kloo Contacts system.
    """

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        """
        Handles POST requests to insert Merge Contact data into the Kloo Contacts system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")
        fetch_data = MergeContactsList(
            link_token_details=self.link_token_details,
            last_modified_at=self.last_modified_at,
        )
        contact_data = fetch_data.get(request=request)

        try:
            if contact_data.status_code == status.HTTP_200_OK:
                contact_payload = contact_data.data
                contact_payload["erp_link_token_id"] = erp_link_token_id
                contact_payload["org_id"] = org_id

                api_log(
                    msg=f"TOtal contact data from Merge : {json.dumps(contact_payload)}"
                )

                api_log(
                    msg=f"Size of contact data from Merge : {len(json.dumps(contact_payload))}"
                )

                api_log(
                    msg=f"Length of contact data to Kloo: {len(contact_payload)}"
                )

                api_log(
                    msg=f"Total contact data to Kloo: {contact_payload}"
                )

                contact_url = (
                    f"{GETKLOO_LOCAL_URL}/ap/erp-integration/insert-erp-contacts"
                )

                # adding batch size of 100
                batch_size = contacts_batch_size
                api_log(msg=f"[BATCH SIZE]:: {batch_size}")
                for batch in range(0, len(contact_payload), batch_size):
                    api_log(msg=f"[BATCH SIZE]:: {batch_size}")
                    api_log(msg=f"[BATCH]:: {batch}")
                    batch_data = contact_payload[batch:batch + batch_size]
                    api_log(msg=f"[BATCH DATA]:: {batch_data}")

                    contact_response_data = requests.post(
                        contact_url,
                        json=batch_data,
                        # stream=True,
                    )

                if contact_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(
                        msg="data inserted successfully in the kloo Contacts system"
                    )
                    return Response(
                        {"message": "API Contact Info completed successfully"}
                    )

                else:
                    return Response(
                        {"error": "Failed to send data to Kloo Contacts API"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            if contact_data.status_code == status.HTTP_204_NO_CONTENT:
                return Response(
                    {
                        "message": "No new data found to insert in the kloo contact system"
                    },
                    status=status.HTTP_204_NO_CONTENT,
                )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Contacts API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response("Failed to insert data to the kloo Contacts system")
