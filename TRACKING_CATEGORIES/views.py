"""
Module docstring: This module provides functions related to traceback.
"""

import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration.helper_functions import api_log
from merge_integration.settings import (
    tax_rate_page_size,
)
from merge_integration.utils import create_merge_client
from services.merge_service import MergeTrackingCategoriesService


class MergeTrackingCategoriesList(APIView):
    """
    API view for retrieving Merge Tracking Category list.
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

    def get_tc(self):
        if self.link_token_details is None:
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details
        tc_client = create_merge_client(account_token)

        try:
            organization_data = tc_client.accounting.tracking_categories.list(
                remote_fields="status",
                show_enum_origins="status",
                page_size=tax_rate_page_size,
                include_remote_data=True,
                modified_after=self.last_modified_at,
            )
            all_tracking_categories = []
            while True:
                api_log(
                    msg=f"Adding {len(organization_data.results)} tracking categories to the list."
                )

                all_tracking_categories.extend(organization_data.results)
                if organization_data.next is None:
                    break

                organization_data = tc_client.accounting.tracking_categories.list(
                    remote_fields="status",
                    show_enum_origins="status",
                    page_size=tax_rate_page_size,
                    include_remote_data=True,
                    modified_after=self.last_modified_at,
                    cursor=organization_data.next,
                )

                api_log(
                    msg=f"tracking categories GET:: The length of the next page tracking categories data is : {len(organization_data.results)}"
                )
                api_log(
                    msg=f"Length of tracking categories array : {len(organization_data.results)}"
                )

            api_log(
                msg=f"tracking categories GET:: The length of all tracking categories data is : {len(all_tracking_categories)}"
            )

            return all_tracking_categories
        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )

    @staticmethod
    def response_payload(organization_data):
        """
        Formats the Merge Tracking_Category data into the required format for Kloo API.

        Args:
            organization_data: The Merge Tracking_Category data to be formatted.

        Returns:
            The formatted Merge Tracking_Category data.
        """
        field_mappings = [
            {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
        ]

        formatted_data = []
        for category in organization_data:
            erp_remote_data = None
            if category.remote_data is not None:
                erp_remote_data = [
                    category_remote_data.data
                    for category_remote_data in category.remote_data
                ]

            formatted_entry = {
                "id": category.id,
                "name": category.name,
                "status": category.status,
                "category_type": category.category_type,
                "parent_category": category.parent_category,
                "company": category.company,
                "remote_was_deleted": category.remote_was_deleted,
                "remote_id": category.remote_id,
                "created_at": category.created_at.isoformat(),
                "updated_at": category.modified_at.isoformat(),
                "field_mappings": field_mappings,
                "remote_data": erp_remote_data,
            }
            formatted_data.append(formatted_entry)
        kloo_format_json = {"tracking_category": formatted_data}

        return kloo_format_json

    def get(self, request, *args, **kwargs):
        api_log(msg="...... Processing GET request in Merge Tracking Categories ......")

        organization_data = self.get_tc()
        if organization_data is None or len(organization_data) == 0:
            return Response(
                {"tracking_category": []}, status=status.HTTP_204_NO_CONTENT
            )
        formatted_data = self.response_payload(organization_data)

        api_log(msg=f" Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergePostTrackingCategories(APIView):
    """
    API view for handling POST requests to insert Merge Tracking_Category data into the Kloo account system.
    """

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")

        merge_tracking_category_api_service = MergeTrackingCategoriesService(
            self.link_token_details, org_id, erp_link_token_id
        )
        tracking_categories_response = (
            merge_tracking_category_api_service.get_tracking_categories(
                self.last_modified_at
            )
        )

        try:
            if tracking_categories_response["status"]:
                api_log(
                    msg=f"TRACKING CATEGORIES : Processing {len(tracking_categories_response['data'])}"
                    f" tracking categories"
                )

                if len(tracking_categories_response["data"]) == 0:
                    return Response(
                        {
                            "message": "No new data found to insert in the kloo Invoice system"
                        },
                        status=status.HTTP_204_NO_CONTENT,
                    )

                api_log(
                    msg="data inserted successfully in the kloo tracking categories system"
                )
                return Response(
                    {"message": "API Tracking category completed successfully"}
                )

            api_log(msg="Failed to send data to Kloo Tracking category API")
            return Response(
                {"error": "Failed to send data to Kloo Tracking category API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            api_log(
                msg=f"Failed to send data to Kloo Tracking_Category API. Error: {str(e)}"
            )
            error_message = (
                f"Failed to send data to Kloo Tracking_Category API. Error: {str(e)}"
            )
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
