"""
Module docstring: This module provides functions related to traceback.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration.helper_functions import api_log
from services.merge_service import MergeContactsApiService


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

        merge_invoice_api_service = MergeContactsApiService(
            self.link_token_details, org_id, erp_link_token_id
        )
        contacts_response = merge_invoice_api_service.get_contacts(
            self.last_modified_at
        )

        try:
            if contacts_response["status"]:
                api_log(
                    msg=f"CONTACTS : Processing {len(contacts_response['data'])} invoices"
                )

                if len(contacts_response["data"]) == 0:
                    return Response(
                        {
                            "message": "No new data found to insert in the kloo Invoice system"
                        },
                        status=status.HTTP_204_NO_CONTENT,
                    )

                return Response(
                    {"message": "API Contacts Info completed successfully"},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"error": "Failed to send data to Kloo Contacts API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            error_message = f"Failed to send data to Kloo Contacts API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
