"""
Module docstring: This module provides functions related to traceback.
"""

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


class MergeTaxRatesList(APIView):
    """
    API view for retrieving Merge Tax Rate list.
    """

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def get_tax_rate(self):
        """
        Retrieves tax rates data from the Merge API.

        Returns:
            Tax rate data retrieved from the Merge API.
        """
        api_log(msg="......... Fetching Tax rates .........")

        if self.link_token_details is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details
        merge_client = create_merge_client(account_token)

        try:
            tax_data = merge_client.accounting.tax_rates.list(
                expand="company", page_size=100000, include_remote_data=True
            )
            return tax_data

        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )

    @staticmethod
    def response_payload(tax_data):
        """
        Formats the tax rate data retrieved from the Merge API into a specific format.

        Args:
            tax_data: Tax rate data retrieved from the Merge API.

        Returns:
            Formatted tax rate data.
        """
        field_map = [
            {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
        ]

        formatted_list = []
        for taxdata in tax_data.results:
            erp_remote_data = None
            if taxdata.remote_data is not None:
                erp_remote_data = [
                    tax_remote_data.data for tax_remote_data in taxdata.remote_data
                ]

            format_response = {
                "description": taxdata.description,
                "total_tax_rate": taxdata.total_tax_rate,
                "effective_tax_rate": taxdata.effective_tax_rate,
                "company": taxdata.company,
                "remote_was_deleted": taxdata.remote_was_deleted,
                "id": taxdata.id,
                "remote_id": taxdata.remote_id,
                "created_at": taxdata.created_at.isoformat() + "Z",
                "modified_at": taxdata.modified_at.isoformat() + "Z",
                "field_mappings": field_map,
                "remote_data": erp_remote_data,
            }
            formatted_list.append(format_response)

        kloo_format_json = {"taxRates": formatted_list}

        return kloo_format_json

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve tax rates data.

        Returns:
            Response containing formatted tax rate data.
        """
        api_log(msg="Processing GET request in MergeTaxRate")

        tax_data = self.get_tax_rate()
        formatted_data = self.response_payload(tax_data)

        api_log(
            msg=f"FORMATTED DATA: {formatted_data} \
         - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
        )
        return Response(formatted_data, status=status.HTTP_200_OK)


class mergeTaxRatesInfo(APIView):
    """
    API view for retrieving Merge Tax Rate information by ID.
    """

    @staticmethod
    def get(_, id=None):
        """
        Retrieves tax rate information for a specific ID from the Merge API.

        Args:
            id: ID of the tax rate to retrieve information for.

        Returns:
            Response containing tax rate information.
        """
        api_log(msg="_______TAX RATES by ID________")
        tax_data = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY,
        )

        try:
            api_log(msg="Fetching list of Tax rates by ID")
            tax_client = tax_data.accounting.tax_rates.retrieve(id=id, expand="company")

            field_map = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {},
                },
            ]

            formatted_list = []
            format_response = {
                "description": tax_client.description,
                "total_tax_rate": tax_client.total_tax_rate,
                "effective_tax_rate": tax_client.effective_tax_rate,
                "company": tax_client.company,
                "remote_was_deleted": tax_client.remote_was_deleted,
                "id": tax_client.id,
                "remote_id": tax_client.remote_id,
                "created_at": tax_client.created_at,
                "modified_at": tax_client.modified_at,
                "field_mappings": field_map,
                "remote_data": tax_client.remote_data,
            }
            formatted_list.append(format_response)

            api_log(
                msg=f"FORMATTED DATA: {formatted_list} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
            )
            return Response(formatted_list, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving Tax Rate details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )

            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergePostTaxRates(APIView):
    """
    API view for inserting Merge Tax Rate data into the Kloo Tax Rate system.
    """

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def post(self, request):
        """
        Handles POST requests to insert Merge Tax Rate data into the Kloo Tax Rate system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        erp_link_token_id = request.data.get("erp_link_token_id")
        fetch_data = MergeTaxRatesList(link_token_details=self.link_token_details)
        tax_data = fetch_data.get(request=request)

        try:
            if tax_data.status_code == status.HTTP_200_OK:
                tax_payload = tax_data.data
                tax_payload["erp_link_token_id"] = erp_link_token_id
                tax_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-tax-rates"
                tax_response_data = requests.post(
                    tax_url,
                    json=tax_payload,
                )

                api_log(msg=f"tax_response_data: {tax_response_data}")

                if tax_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(
                        msg="data inserted successfully in the kloo Tax Rate system"
                    )
                    return Response(
                        f"{tax_response_data} data inserted successfully in kloo Tax Rate system"
                    )

                else:
                    return Response(
                        {"error": "Failed to send data to Kloo Tax Rate API"},
                        status=tax_response_data.status_code,
                    )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Tax Rate API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response("Failed to insert data to the kloo Tax Rate system", traceback)
