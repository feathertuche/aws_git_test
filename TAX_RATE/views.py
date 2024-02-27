"""
Module docstring: This module provides functions related to traceback.
"""
import traceback
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge.client import Merge
from merge_integration import settings
from merge_integration.helper_functions import api_log


class MergeTaxRatesList(APIView):
    """
    API view for retrieving Merge Tax Rate list.
    """
    @staticmethod
    def get_tax_rate():
        """
        Retrieves tax rates data from the Merge API.

        Returns:
            Tax rate data retrieved from the Merge API.
        """
        api_log(msg="Fetching list of Tax rates")

        tax_client = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY
        )

        try:
            tax_data = tax_client.accounting.tax_rates.list(
                expand="company",
            )
            return tax_data

        except Exception as e:
            api_log(
                msg=f"Error retrieving details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

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
            {
                "organization_defined_targets": {},
                "linked_account_defined_targets": {}
            }
        ]

        formatted_list = []
        for taxdata in tax_data.results:
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
                "remote_data": taxdata.remote_data
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

        api_log(msg=f"FORMATTED DATA: {formatted_data} \
         - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
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
        tax_data = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN ,api_key=settings.API_KEY)

        try:
            api_log(msg="Fetching list of Tax rates by ID")
            tax_client = tax_data.accounting.tax_rates.retrieve(id=id, expand="company")

            field_map = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {}
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
                "remote_data": tax_client.remote_data
            }
            formatted_list.append(format_response)

            api_log(
                msg=f"FORMATTED DATA: {formatted_list} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
            return Response(formatted_list, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving Tax Rate details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MergePostTaxRates(APIView):
    """
    API view for inserting Merge Tax Rate data into the Kloo Tax Rate system.
    """
    def post(self, request):
        """
        Handles POST requests to insert Merge Tax Rate data into the Kloo Tax Rate system.

        Returns:
            Response indicating success or failure of data insertion.
        """
        fetch_data = MergeTaxRatesList()
        tax_data = fetch_data.get(request=request)

        try:
            if tax_data.status_code == status.HTTP_200_OK:
                tax_payload = tax_data.data
                tax_url = "https://stage.getkloo.com/api/v1/organizations/insert-erp-tax-rates"
                tax_response_data = requests.post(tax_url, json=tax_payload)

                if tax_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(msg=f"data inserted successfully in the kloo Tax Rate system")
                    return Response(f"{tax_response_data} data inserted successfully in kloo Tax Rate system")

                else:
                    return Response({'error': 'Failed to send data to Kloo Tax Rate API'}, status=tax_response_data.status_code)

        except Exception as e:
            error_message = f"Failed to send data to Kloo Tax Rate API. Error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(f"Failed to insert data to the kloo Tax Rate system", traceback)

