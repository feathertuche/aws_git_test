"""
Module docstring: This module provides functions related to traceback.
"""
import json
from datetime import datetime
import traceback
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge.resources.accounting import ContactsListRequestExpand, ContactsRetrieveRequestExpand
from merge_integration import settings
from merge_integration.helper_functions import api_log


class MergeContactsList(APIView):
    """
    API view for retrieving Merge Contacts list.
    """
    @staticmethod
    def get_contacts():
        """
        Retrieves contacts data from the Merge API.

        Returns:
            Contacts data retrieved from the Merge API.
        """
        api_log(msg="Processing GET request Merge Contacts list")
        contacts_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)
        try:
            contact_data = contacts_client.accounting.contacts.list(
                    expand=ContactsListRequestExpand.ADDRESSES,
                    remote_fields="status",
                    show_enum_origins="status",
            )
            return contact_data
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

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
                "remote_updated_at": contact.remote_updated_at.isoformat() + "Z",
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
                        "created_at": addr.created_at.isoformat() + "Z",
                        "modified_at": addr.modified_at.isoformat() + "Z",
                    }
                    for addr in contact.addresses
                ],
                "phone_numbers": [
                    {
                        "number": phone.number,
                        "type": phone.type,
                        "created_at": phone.created_at.isoformat() + "Z",
                        "modified_at": phone.modified_at.isoformat() + "Z",
                    }
                    for phone in contact.phone_numbers
                ],
                "remote_was_deleted": contact.remote_was_deleted,
                "created_at": contact.created_at.isoformat() + "Z",
                "modified_at": contact.modified_at.isoformat() + "Z",
                "field_mappings": contact.field_mappings,
                "remote_data": contact.remote_data,
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
        api_log(msg="Processing GET request in MergeContacts")

        contact_data = self.get_contacts()
        formatted_data = self.response_payload(contact_data)

        api_log(msg=f"FORMATTED DATA: {formatted_data} \
         - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
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
                msg=f"Error retrieving Contacts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MergePostContacts(APIView):
    """
    API view for inserting Merge Contact data into the Kloo Contacts system.
    """
    def post(self, request):
        """
        Handles POST requests to insert Merge Contact data into the Kloo Contacts system.

        Returns:
            Response indicating success or failure of data insertion.
        """
        fetch_data = MergeContactsList()
        contact_data = fetch_data.get(request=request)

        try:
            if contact_data.status_code == status.HTTP_200_OK:
                contact_payload = contact_data.data
                contact_url = "https://dev.getkloo.com/api/v1/ap/erp-integration/insert-erp-contacts"

                headers = {
                    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiI1Y2M1ZjE4YjRhMzUyNWMyNTIwNzZhZmJkYzE5M2U1MzlmNzYxOGVhNDIyNGNmYWUxZGZkMDA5OTNmN2I5YzE1ZTk0YzcwMzllMWZjZjNmYiIsImlhdCI6MTcwNzI4MjUzNC43NjA5OTcsIm5iZiI6MTcwNzI4MjUzNC43NjA5OTksImV4cCI6MTcwNzI4MjgzNC43NDQ4NDUsInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiOTJlZjgzYzEtMmVjMi00NTA1LWEzNjMtZDEwMGM4NjlhNjllXCIsXCJmaXJzdF9uYW1lXCI6XCJWYXJzaGFcIixcIm1pZGRsZV9uYW1lXCI6XCJBZ2F0cmFtXCIsXCJsYXN0X25hbWVcIjpcIlNhaHVcIixcImVtYWlsXCI6XCJWYXJzaGEuU2FodUBibGVuaGVpbWNoYWxjb3QuY29tXCIsXCJiaXJ0aF9kYXRlXCI6XCIyMDA0LTEwLTA2XCIsXCJ1c2VyX2NyZWF0ZWRfYnlcIjpudWxsLFwibG9naW5fYXR0ZW1wdHNcIjowLFwic3RhdHVzXCI6XCJ1bmJsb2NrZWRcIixcImNyZWF0ZWRfYXRcIjpcIjIwMjItMDgtMDhUMTI6MDk6MDQuMDAwMDAwWlwiLFwidXBkYXRlZF9hdFwiOlwiMjAyMy0wNC0wN1QwNjo1ODo1OC4wMDAwMDBaXCIsXCJ1c2VyX29yZ19pZFwiOlwiMDIzYTFhYmEtYzdhMi00YWE0LTllNmEtOGZhMzEwNTQwYTllXCIsXCJvcmdhbml6YXRpb25faWRcIjpcIjBhYWJmNWVlLWUyNmUtNGQ4Ni1hNTE4LWVlY2IwMzlhOWU3N1wiLFwib3JnYW5pemF0aW9uX25hbWVcIjpcIktsb29EZXZcIn0sXCJzY29wZXNcIjpbXCJjYXJkLWV4cGVuc2VzLWRvd25sb2FkLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtbWFyay1mb3ItcmV2aWV3LXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1tYXJrLWFzLWFwcHJvdmVkLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1zYXZlLWFzLWRyYWZ0LXVwZGF0ZVwiLFwicGF5bWVudC1ydW5zLWNyZWF0ZVwiLFwicGF5bWVudC1ydW5zLXJlYWRcIixcInBheW1lbnQtcnVucy11cGRhdGVcIixcInBheW1lbnQtcnVucy1kZWxldGVcIixcInN1YnNjcmlwdGlvbi1jcmVhdGVcIixcInN1YnNjcmlwdGlvbi1yZWFkXCIsXCJzdWJzY3JpcHRpb24tdXBkYXRlXCIsXCJzdWJzY3JpcHRpb24tZGVsZXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMS1jcmVhdGVcIixcInRlc3QtbW9kdWxlLWExLXJlYWRcIixcInRlc3QtbW9kdWxlLWExLXVwZGF0ZVwiLFwidGVzdC1tb2R1bGUtYTEtZGVsZXRlXCIsXCJpbnZvaWNlLXBvLW1hdGNoaW5nLXJlYWRcIixcImRhc2hib2FyZC1jYXJkLWFuZC1jYXJkLWV4cGVuc2VzLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWNhcmRzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXB1cmNoYXNlLW9yZGVycy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1oaXN0b3J5LXJlYWRcIixcInNldHRpbmctcGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJ1cGRhdGUtcGVybWlzc2lvbi1yZXRvb2wtdGVzdC1jcmVhdGVcIixcInVwZGF0ZS1wZXJtaXNzaW9uLXJldG9vbC10ZXN0LXJlYWRcIixcImRhc2hib2FyZC1wby1yZWFkXCIsXCJwYXllZS1tYW5hZ2VtZW50LXJlYWRcIixcInBheS12aWEteWFwaWx5LXJlYWRcIixcInNjaGVkdWxlLXRhYi1yZWFkXCIsXCJ1cGRhdGUtcGVybWlzc2lvbi1yZXRvb2wtdGVzdC11cGRhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1jcmVhdGVcIixcInNldHRpbmctZXhwZW5zZS1maWVsZC1yZWFkXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtZGVsZXRlXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLWNyZWF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1yZWFkXCIsXCJzZXR0aW5nLWN1c3RvbS1leHBlbnNlLXVwZGF0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1kZWxldGVcIixcImNvbmZpZ3VyYXRpb25zLW9yZ2FuaXNhdGlvbi1yZWFkXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwic2V0dGluZy1uZXctcGF5ZWUtY29udGFjdC1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMi1jcmVhdGVcIixcInRlc3QtbW9kdWxlLWEyLXJlYWRcIixcInRlc3QtbW9kdWxlLWEyLXVwZGF0ZVwiLFwidGVzdC1tb2R1bGUtYTItZGVsZXRlXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1zY2hlZHVsZS1yZWFkXCIsXCJwYXktbm93LWJ1dHRvbi1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1wcmVmaXgtcG8tcmVhZFwiLFwic2V0dGluZy1pbnRlZ3JhdGlvbnMtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaWVzLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXJlYWRcIixcInNldHRpbmctYWRkcmVzcy1yZWFkXCIsXCJkYXNoYm9hcmQtcmVhZFwiLFwiYXBwcm92YWxzLXJlYWRcIixcIi1jb25maWd1cmF0aW9ucy1lbnRpdHktLXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXN1cHBsaWVyLXJlYWRcIixcImFjY291bnQtZGV0YWlscy1yZWFkXCIsXCJkZWJpdC1hY2NvdW50LWNyZWF0ZVwiLFwiZGViaXQtYWNjb3VudC1yZWFkXCIsXCJkZWJpdC1hY2NvdW50LXVwZGF0ZVwiLFwiZGViaXQtYWNjb3VudC1kZWxldGVcIixcInN0YW5kaW5nLW9yZGVyLWNyZWF0ZVwiLFwic3RhbmRpbmctb3JkZXItcmVhZFwiLFwiaW1tZWRpYXRlLXBheW1lbnQtY3JlYXRlXCIsXCJpbW1lZGlhdGUtcGF5bWVudC1yZWFkXCIsXCJiYW5rLXRyYW5zZmVyLWNyZWF0ZVwiLFwiYmFuay10cmFuc2Zlci1yZWFkXCIsXCJzY2hlZHVsZWQtcmVhZFwiLFwiaGlzdG9yeS1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1wYXltZW50LXJ1bnMtcmVhZFwiLFwiYWxsLWNhcmRzLXJlYWRcIixcIm15LWNhcmRzLXJlYWRcIixcInZpcnR1YWwtY2FyZHMtY3JlYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLXJlYWRcIixcInZpcnR1YWwtY2FyZHMtdXBkYXRlXCIsXCJ2aXJ0dWFsLWNhcmRzLWRlbGV0ZVwiLFwicGh5c2ljYWwtY2FyZHMtY3JlYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1yZWFkXCIsXCJwaHlzaWNhbC1jYXJkcy11cGRhdGVcIixcInBoeXNpY2FsLWNhcmRzLWRlbGV0ZVwiLFwiY2FyZC1saW1pdC11cGRhdGVcIixcImNhcmQtbmlja25hbWUtdXBkYXRlXCIsXCJjYW5jZWwtY2FyZC11cGRhdGVcIixcImZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwidW5mcmVlemUtY2FyZC11cGRhdGVcIixcImNhcmQtc3RhdHVzLXVwZGF0ZVwiLFwiY2FyZC1kb3dubG9hZHMtaW1wb3J0XCIsXCJ1c2Vycy1jcmVhdGVcIixcInVzZXJzLXJlYWRcIixcInVzZXJzLXVwZGF0ZVwiLFwidXNlcnMtZGVsZXRlXCIsXCJpbnZpdGF0aW9uLWxpbmstc2VuZFwiLFwiaGVhbHRoLWNoZWNrLXJlYWRcIixcIm5vdGlmaWNhdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLXJlYWRcIixcIm9yZ2FuaXphdGlvbi1tb2R1bHItYWNjb3VudC1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtY3JlYXRlXCIsXCJ0cmFuc2FjdGlvbnMtcmVhZFwiLFwidHJhbnNhY3Rpb25zLXVwZGF0ZVwiLFwidHJhbnNhY3Rpb25zLWRlbGV0ZVwiLFwidXNlci10cmFuc2FjdGlvbnMtcmVhZFwiLFwib3JnYW5pemF0aW9uLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJjdXN0b21lci1jcmVhdGVcIixcImNvbXBhbnktcmVhZFwiLFwib3JnYW5pemF0aW9uLWFuYWx5dGljcy1yZWFkXCIsXCJ1c2VyLWFuYWx5dGljcy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtdXBkYXRlXCIsXCJjYXJkLXJlcXVlc3RzLWRlbGV0ZVwiLFwiY2FyZC1leHBlbnNlcy1jcmVhdGVcIixcImNhcmQtZXhwZW5zZXMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtZGVsZXRlXCIsXCJ0ZWFtcy1jcmVhdGVcIixcInRlYW1zLXJlYWRcIixcInRlYW1zLXVwZGF0ZVwiLFwidGVhbXMtZGVsZXRlXCIsXCJjb25maWd1cmF0aW9ucy1wby1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWNlLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tYXAtcmVhZFwiLFwicGF5ZWUtY29udGFjdC1uby1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLXBvLXJlYWRcIixcInRlc3QtbW9kdWxlLWExLWV4cG9ydFwiLFwieGVyby1hbmFseXNpcy1yZWFkXCIsXCJrbG9vLXNwZW5kLXJlYWRcIixcImlzc3VlLWNhcmQtY3JlYXRlXCIsXCJhY3RpdmF0ZS1waHlzaWNhbC1jYXJkLXVwZGF0ZVwiLFwiYW5hbHl0aWNzLWRhc2hib2FyZC1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLXJlYWRcIixcInRlc3QtbW9kdWxlLWExLWltcG9ydFwiLFwiZGFzaGJvYXJkLWltLXJlYWRcIixcImNoYXJnZWJlZS1jdXN0b21lci1jcmVhdGVcIixcImNoYXJnZWJlZS1zdWJzY3JpcHRpb24tcmVhZFwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWJpbGwtcmVhZFwiLFwiY2hhcmdlYmVlLWludm9pY2UtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1zdWJzY3JpcHRpb25zLXJlYWRcIixcImNoYXJnZWJlZS1vcmdhbml6YXRpb24tcmVhZFwiLFwiYXAtaW52b2ljZS1jcmVhdGVcIixcImFwLWludm9pY2UtcmVhZFwiLFwiYXAtaW52b2ljZS11cGRhdGVcIixcInNldHRpbmctcmVhZFwiLFwibmV3LXBheWVlLWNvbnRhY3QtcmVhZFwiLFwiY29uZmlndXJhdGlvbnMtYXV0b21hdGljLWVtYWlsLXBvLXJlYWRcIixcInNjaGVkdWxlLXBheW1lbnQtYnV0dG9uLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLXRheC1jb2RlLXJlYWRcIixcIm9yZ2FuaXphdGlvbi1jcmVhdGVcIixcIm9yZ2FuaXphdGlvbi11cGRhdGVcIixcIm9yZ2FuaXphdGlvbi1kZWxldGVcIixcInRlc3QtbW9kdWxlLWEzLWNyZWF0ZVwiLFwicm9sZXMtcmVhZFwiLFwicm9sZXMtdXBkYXRlXCIsXCJyb2xlcy1kZWxldGVcIixcInRocmVzaG9sZC1yZWFkXCIsXCJwdXJjaGFzZS1vcmRlci1jcmVhdGVcIixcInB1cmNoYXNlLW9yZGVyLXJlYWRcIixcInB1cmNoYXNlLW9yZGVyLXVwZGF0ZVwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy11cGRhdGVcIixcInRlc3QtbW9kdWxlLWEzLXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWVudGl0eS1yZWFkXCIsXCJwcm9maWxlLXJlYWRcIixcInByb2ZpbGUtdXBkYXRlXCIsXCJpbnZvaWNlLW1hdGNoaW5nLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiXSxcInJvbGVcIjp7XCJpZFwiOlwiNWE3Y2NjOTItZWEzMC00ODM0LTg1OTQtNTEzMmI4MjU2NjA3XCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.KxF5FgwdAizuvlX69APhvpVM5iBRJNf-VOFzG3j3SvJtJiHMkZCy30D1T5N5eVvsTszn8F7CRRz9lAwuWW5dH8RlEQ7wHRQw0c9vcnmEVgj-702v-NvPpUiWzxeODRyJIM9Wr0-P3ivl9ct9F1S5Hsu_HOboUlv19ZhQADAocwEEghDyeR-TEh9ZUgaLW16mipEwT5qoq2KLOOoRoRVJegHOvrHVFD6dX1h66xY37ieue-2hoyQkWhISxhOBNhDXqimKZJTsJzEV4IpAoJStBEZr27dil41n_FqkegEgPTVDbrT5xiKmqkzAm16V0S7aNbERQBKjwTBS9fD1bXTrk_YuwsjGMH3Q6XGvUWW9LM6pprNxzp8ebVRrVwWCs2L5i7TBVOdFSU5xdXspMxnXUo6iAWJdBVaUcZxbzdPaylBspJeo3_6Zs7hqpywWqB5pdSaMoIs2bjiLdRT2j7vr1yMJCQtE0loJN8hwNm2d2DsLqPS4wAK7sYJ2KnWVee6jAfR3Bdu8DSCKUYbUySg8GAOkj4sJGi5OjZVFkN_icJYY4hL3To6_jLBnrSckqXfO_f5wUarQsf7-622HvK_Sx8bEmtiuKDAVL_3C5tx3MsvCAsL1uqMYjoFI7FWIKbS9LCbVHqc9BBFjJVBpRJ2eiLI1r-aCBU9xIUU8GBYs1Ws'
                    }

                contact_response_data = requests.post(contact_url, json=contact_payload, headers=headers)

                if contact_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(msg=f"data inserted successfully in the kloo Contacts system")
                    return Response(f"{contact_response_data} data inserted successfully in kloo Contacts system")

                else:
                    return Response({'error': 'Failed to send data to Kloo Contacts API'}, status=contact_response_data.status_code)

        except Exception as e:
            error_message = f"Failed to send data to Kloo Contacts API. Error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(f"Failed to insert data to the kloo Contacts system", traceback)

