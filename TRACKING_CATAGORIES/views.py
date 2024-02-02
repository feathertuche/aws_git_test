"""
Module docstring: This module provides functions related to traceback.
"""
import traceback
import requests
from merge.client import Merge
from merge_integration import settings
from merge_integration.helper_functions import api_log
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import json


class MergeTrackingCategoriesList(APIView):
    """
        API view for retrieving Merge Tracking_Category list.
    """

    @staticmethod
    def get(_):
        """
                Handle GET request for Merge Tracking_Category list.

                Args:
                    _: HTTP request object.

                Returns:
                    Response: JSON response containing Merge Tracking_Category list or error message.
        """
        api_log(msg="Processing GET request Merge Tracking_Category list...")

        tracking_client = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY
        )

        try:
            tracking_data = tracking_client.accounting.tracking_categories.list(
                expand="company",
                remote_fields="status",
                show_enum_origins="status",
            )
        except Exception as e:
            error_msg = f"Error retrieving tracking category details: {str(e)} \
            - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()} "
            api_log(msg=error_msg)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        field_mappings = [{
            "organization_defined_targets": {},
            "linked_account_defined_targets": {}}]

        list_data = []
        for category in tracking_data.results:
            total_data = {
                "id": category.id,
                "name": category.name,
                "status": category.status,
                "category_type": category.category_type,
                "parent_category": category.parent_category,
                "company": category.company,
                "remote_was_deleted": category.remote_was_deleted,
                "remote_id": category.remote_id,
                "created_at": category.created_at,
                "updated_at": category.modified_at,
                "field_mappings": field_mappings,
                "remote_data": category.remote_data,
            }

            list_data.append(total_data)
        formatted_response = {"tracking_category": list_data}

        api_log(msg=f"FORMATTED DATA: {formatted_response} - Status Code: {status.HTTP_200_OK}")
        return Response(formatted_response, status=status.HTTP_200_OK)


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
                msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MergePostTrackingCategories(APIView):
    """
    API endpoint for merging and posting tracking categories to the Kloo API.

    This class handles the POST request to merge and send tracking category data to the Kloo API.

    Attributes:
    - KLOO_API_URL (str): The URL of the Kloo API endpoint for tracking categories.
    """
    
    KLOO_API_URL = 'https://dev.getkloo.com/api/v1/organizations/erp-tracking-categories'

    def post(self, request):
        """
        Handle POST requests.

        This method processes the POST request, merges tracking category data, and sends it to the Kloo API.

        Args:
        - request (HttpRequest): The HTTP request object containing data to be processed.

        Returns:
        - Response: The HTTP response indicating the success or failure of the operation.
        """
        
        try:
            merge_tracking_categories = MergeTrackingCategoriesList()
            response = MergeTrackingCategoriesList.get(request)

            if response.status_code == status.HTTP_200_OK:
                merge_payload = response.data

                def default_serializer(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f'Type {type(obj)} is not serializable')

                merge_payload_json = merge_payload
                tracking_categories = merge_payload_json['tracking_category']

                # Extract the data you want to post from the request
                post_data = request.data.get('tracking_category', [])

                payload_list = []

                for post_category in post_data:
                    matching_category = next(
                        (category for category in tracking_categories if category['id'] == post_category['id']),
                        None
                    )

                    if matching_category:
                        created_at_str = matching_category["created_at"]
                        updated_at_str = matching_category["updated_at"]
                        id1 = matching_category["id"]
                        name = matching_category["name"]
                        status1 = matching_category["status"]
                        category_type = matching_category["category_type"]
                        parent_category = matching_category["parent_category"]
                        company = matching_category["company"]
                        remote_was_deleted = matching_category["remote_was_deleted"]
                        remote_id = matching_category["remote_id"]
                        field_mappings = matching_category["field_mappings"]
                        remote_data = matching_category["remote_data"]

                        tracking_category_dict = {
                            "id": id1,
                            "name": name,
                            "status": status1,
                            "category_type": category_type,
                            "parent_category": parent_category,
                            "company": company,
                            "remote_was_deleted": remote_was_deleted,
                            "remote_id": remote_id,
                            "field_mappings": field_mappings,
                            "remote_data": remote_data,
                            "created_at": created_at_str,
                            "updated_at": updated_at_str
                        }

                        payload_list.append(tracking_category_dict)

                response_data = {
                    'merge_tracking_categories': merge_tracking_categories,
                    'payload': {
                        "tracking_category": payload_list
                    }
                }

                headers = {'Content-Type': 'application/json'}
                kloo_data_insert = requests.post(
                    self.KLOO_API_URL,
                    json=response_data['payload'],
                    headers=headers,
                    data=json.dumps(response_data['payload'], default=default_serializer)
                )

                if kloo_data_insert.status_code == status.HTTP_201_CREATED:
                    return Response("Successfully inserted the data", status=status.HTTP_201_CREATED)

                return Response({'error': f'Failed to send data to Kloo API. Status Code: {kloo_data_insert.status_code}'},
                                status=kloo_data_insert.status_code)

        except Exception as e:
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'error': 'Failed to retrieve company information'}, status=response.status_code)

