"""
Module docstring: This module provides functions related to traceback.
"""
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge_integration import settings
from merge_integration.helper_functions import api_log


class MergeTrackingCategoriesList(APIView):
    """
        API view for retrieving Merge Tracking_Category list.
    """

    @staticmethod
    def get(_):
        """
                Handle GET request for Merge Tracking_Category list.

                Args:
                    -: HTTP request object.

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
                "name": category.name,
                "status": category.status,
                "category_type": category.category_type,
                "parent_category": category.parent_category,
                "company": category.company,
                "remote_was_deleted": category.remote_was_deleted,
                "id": category.id,
                "remote_id": category.remote_id,
                "created_at": category.created_at,
                "modified_at": category.modified_at,
                "field_mappings": field_mappings,
                "remote_data": category.remote_data,
            }

            list_data.append(total_data)

        api_log(msg=f"FORMATTED DATA: {list_data} - Status Code: {status.HTTP_200_OK}")
        return Response(list_data, status=status.HTTP_200_OK)


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
