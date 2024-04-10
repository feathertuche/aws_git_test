"""
Module docstring: This module provides functions related to traceback.
"""

import json
import traceback

import requests
from merge.client import Merge
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL
from merge_integration.utils import create_merge_client


class MergeTrackingCategoriesList(APIView):
    """
    API view for retrieving Merge Tracking_Category list.
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
                page_size=100000,
                include_remote_data=True,
                modified_after=self.last_modified_at,
            )
            all_accounts = []
            while True:
                api_log(
                    msg=f"Adding {len(organization_data.results)} accounts to the list."
                )

                all_accounts.extend(organization_data.results)
                if organization_data.next is None:
                    break

                organization_data = tc_client.accounting.accounts.list(
                    remote_fields="status",
                    show_enum_origins="status",
                    page_size=100000,
                    include_remote_data=True,
                    modified_after=self.last_modified_at,
                    cursor=organization_data.next,
                )

                api_log(
                    msg=f"ACCOUNTS GET:: The length of the next page account data is : {len(organization_data.results)}"
                )
                api_log(msg=f"Length of all_accounts: {len(organization_data.results)}")

            api_log(
                msg=f"ACCOUNTS GET:: The length of all account data is : {len(all_accounts)}"
            )

            return all_accounts
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
        tracking_id_client = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY,
        )

        try:
            tracking_id_data = (
                tracking_id_client.accounting.tracking_categories.retrieve(
                    id=id,
                    expand="company",
                    remote_fields="status",
                    show_enum_origins="status",
                )
            )

            field_mappings = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {},
                }
            ]

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

            api_log(
                msg=f"FORMATTED DATA: {tracking_id_total_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
            )
            return Response(tracking_id_total_data, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        fetch_data = MergeTrackingCategoriesList(
            link_token_details=self.link_token_details,
            last_modified_at=self.last_modified_at,
        )
        tc_data = fetch_data.get(request=request)

        try:
            if tc_data.status_code == status.HTTP_200_OK:
                tc_payload = tc_data.data
                tc_payload["erp_link_token_id"] = erp_link_token_id
                tc_payload["org_id"] = org_id
                api_log(
                    msg=f"Posting tracking_categories data to Kloo: {json.dumps(tc_payload , indent=4)}"
                )
                tc_url = f"{GETKLOO_LOCAL_URL}/organizations/erp-tracking-categories"
                tc_response_data = requests.post(
                    tc_url,
                    json=tc_payload,
                )

                if tc_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(
                        msg="data inserted successfully in the kloo Tracking_Category system"
                    )
                    return Response(
                        {"message": "API Tracking category Info completed successfully"}
                    )

                else:
                    api_log(
                        msg=f"Failed to insert data to the kloo Tracking_Category system "
                        f"- Status Code: {tc_response_data.status_code}"
                    )
                    return Response(
                        {"error": "Failed to send data to Kloo Tracking_Category API"},
                        status=tc_response_data.status_code,
                    )

            if tc_data.status_code == status.HTTP_204_NO_CONTENT:
                return Response(
                    {
                        "message": "No new data found to insert in the kloo tracking category system"
                    },
                    status=status.HTTP_204_NO_CONTENT,
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

        return Response(
            {"error": "Failed to send data to Kloo Tracking_Category API"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
