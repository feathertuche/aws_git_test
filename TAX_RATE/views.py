from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge.client import Merge
import traceback
from merge_integration.helper_functions import api_log


class mergeTaxRatesList(APIView):
    @staticmethod
    def get(_):
        api_log(msg="_______TAX RATES LIST________")
        tax_data = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)

        try:
            api_log(msg="Fetching list of Tax rates")
            tax_client = tax_data.accounting.tax_rates.list(expand="company")

        except Exception as e:
            api_log(msg=f"Error retrieving accounts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        field_map = [
            {
                "organization_defined_targets": {},
                "linked_account_defined_targets": {}
            },
        ]

        formatted_list = []
        for taxdata in tax_client.results:
            format_response = {
                "description": taxdata.description,
                "total_tax_rate": taxdata.total_tax_rate,
                "effective_tax_rate": taxdata.effective_tax_rate,
                "company": taxdata.company,
                "remote_was_deleted": taxdata.remote_was_deleted,
                "id": taxdata.id,
                "remote_id": taxdata.remote_id,
                "created_at": taxdata.created_at,
                "modified_at": taxdata.modified_at,
                "field_mappings": field_map,
                "remote_data": taxdata.remote_data
            }
            formatted_list.append(format_response)

            api_log(
                msg=f"FORMATTED DATA: {formatted_list} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_list, status=status.HTTP_200_OK)


class mergeTaxRatesInfo(APIView):
    @staticmethod
    def get(_, id=None):
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
                msg=f"Error retrieving accounts details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")

            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
