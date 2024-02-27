"""
Module docstring: This module provides functions related to traceback.
"""
import traceback
import requests
from merge.client import Merge
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class MergeTrackingCategoriesList(APIView):
    """
    API view for retrieving Merge Tracking_Category list.
    """

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def get_tc(self):
        if self.link_token_details is None:
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details[0]
        tc_client = create_merge_client(account_token)

        try:
            organization_data = tc_client.accounting.tracking_categories.list(
                expand="company",
                remote_fields="status",
                show_enum_origins="status",
            )
            return organization_data
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

    @staticmethod
    def response_payload(organization_data):
        """
        Formats the Merge Tracking_Category data into the required format for Kloo API.

        Args:
            organization_data: The Merge Tracking_Category data to be formatted.

        Returns:
            The formatted Merge Tracking_Category data.
        """
        field_mappings = [{
            "organization_defined_targets": {},
            "linked_account_defined_targets": {}}]

        formatted_data = []
        for category in organization_data.results:
            formatted_entry = {
                "id": category.id,
                "name": category.name,
                "status": category.status,
                "category_type": category.category_type,
                "parent_category": category.parent_category,
                "company": category.company,
                "remote_was_deleted": category.remote_was_deleted,
                "remote_id": category.remote_id,
                "created_at": category.created_at.isoformat() + "Z",
                "updated_at": category.modified_at.isoformat() + "Z",
                "field_mappings": field_mappings,
                "remote_data": category.remote_data,
            }
            formatted_data.append(formatted_entry)
            kloo_format_json = {"tracking_category": formatted_data}

        return kloo_format_json

    def get(self, request, *args, **kwargs):
        api_log(msg="Processing GET request in MergeTrackingCategories")

        organization_data = self.get_tc()
        formatted_data = self.response_payload(organization_data)

        api_log(msg=f"FORMATTED DATA: {formatted_data} \
         - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergeTrackingCategoriesDetails(APIView):
    """
        API view for retrieving details of a specific Merge Tracking Category.
    """
    @staticmethod
    def get(_, id=None):
        """
                Handle GET request for retrieving details of a specific Merge Tracking Category.

                Args:
                    -: HTTP request object.
                    id (str): Identifier of the Merge Tracking Category.

                Returns:
                    Response: JSON response containing details of the Merge Tracking Category or error message.
        """
        api_log(msg="Processing GET request in Merge Tracking_Category")
        tracking_id_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN,
                                api_key=settings.API_KEY)

        try:
            tracking_id_data = tracking_id_client.accounting.tracking_categories.retrieve(
                                id=id,
                                expand="company",
                                remote_fields="status",
                                show_enum_origins="status",)

            field_mappings = [{
                "organization_defined_targets": {},
                "linked_account_defined_targets": {},
            }]

            tracking_id_total_data = []
            total_id_data = {
                "name": tracking_id_data.name,
                "status": tracking_id_data.status,
                "category_type": tracking_id_data.category_type,
                "parent_category": tracking_id_data.parent_category,
                "company": tracking_id_data.company,
                "remote_was_deleted": tracking_id_data.remote_was_deleted,
                "id": tracking_id_data.id,
                "remote_id": tracking_id_data.remote_id,
                "created_at": tracking_id_data.created_at,
                "modified_at": tracking_id_data.modified_at,
                "field_mappings": field_mappings,
                "remote_data": tracking_id_data.remote_data,
                }

            tracking_id_total_data.append(total_id_data)

            api_log(msg=f"FORMATTED DATA: {tracking_id_total_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
            return Response(tracking_id_total_data, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MergePostTrackingCategories(APIView):
    """
    API view for handling POST requests to insert Merge Tracking_Category data into the Kloo account system.
    """

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def post(self, request):
        erp_link_token_id = request.data.get('erp_link_token_id')
        authorization_header = request.headers.get('Authorization')
        if authorization_header and authorization_header.startswith('Bearer '):
            token = authorization_header.split(' ')[1]

            fetch_data = MergeTrackingCategoriesList(link_token_details=self.link_token_details)
            tc_data = fetch_data.get(request=request)

            try:
                if tc_data.status_code == status.HTTP_200_OK:
                    tc_payload = tc_data.data

                    tc_payload["erp_link_token_id"] = erp_link_token_id

                    tc_url = "https://stage.getkloo.com/api/v1/organizations/erp-tracking-categories"
                    tc_response_data = requests.post(tc_url, json=tc_payload, headers={'Authorization': f'Bearer {token}'})

                    if tc_response_data.status_code == status.HTTP_201_CREATED:
                        api_log(msg=f"data inserted successfully in the kloo Tracking_Category system")
                        return Response(f"{tc_response_data} data inserted successfully in kloo Tracking_Category system")

                    else:
                        return Response({'error': 'Failed to send data to Kloo Tracking_Category API'}, status=tc_response_data.status_code)

            except Exception as e:
                error_message = f"Failed to send data to Kloo Tracking_Category API. Error: {str(e)}"
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(f"Failed to insert data to the kloo Tracking_Category system", traceback)