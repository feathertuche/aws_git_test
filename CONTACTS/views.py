import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge.resources.accounting import ContactsListRequestExpand, ContactsRetrieveRequestExpand
from merge_integration import settings
from merge_integration.helper_functions import api_log


class MergeContactsList(APIView):
    @staticmethod
    def get(_):
        api_log(msg="Processing GET request Merge Accounts list...")
        merg_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            contact_data = merg_client.accounting.contacts.list(
                    expand=ContactsListRequestExpand.ADDRESSES,
                    remote_fields="status",
                    show_enum_origins="status",
            )
        except Exception as e:
            api_log(msg=f"Error retrieving accounts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        formatted_data = []
        for contact in contact_data.results:
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
                "remote_updated_at": contact.remote_updated_at,
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
                        "created_at": addr.created_at,
                        "modified_at": addr.modified_at,
                    }
                    for addr in contact.addresses
                ],
                "phone_numbers": [
                    {
                        "number": phone.number,
                        "type": phone.type,
                        "created_at": phone.created_at,
                        "modified_at": phone.modified_at,
                    }
                    for phone in contact.phone_numbers
                ],
                "remote_was_deleted": contact.remote_was_deleted,
                "created_at": contact.created_at,
                "modified_at": contact.modified_at,
                "field_mappings": contact.field_mappings,
                "remote_data": contact.remote_data,
            }
            formatted_data.append(formatted_entry)

        api_log(msg=f"FORMATTED DATA: {formatted_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergeContactDetails(APIView):
    @staticmethod
    def get(_, id=None):
        api_log(msg="Processing GET request Merge Accounts list...")
        merg_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
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
                } for addr in contact_data.addresses
            ]

            phone_types = [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at,
                    "modified_at": phone.modified_at,
                } for phone in contact_data.phone_numbers
            ]
            field_map = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {}
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
                "remote_data": contact_data.remote_data
            }
            formatted_list.append(format_response)

            api_log(msg=f"FORMATTED DATA: {formatted_list} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
            return Response(formatted_list, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving accounts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
