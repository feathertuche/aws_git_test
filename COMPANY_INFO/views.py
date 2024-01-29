from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration import settings
from merge.client import Merge
import traceback
from merge_integration.helper_functions import api_log
from merge.resources.accounting import CompanyInfoListRequestExpand, CompanyInfoRetrieveRequestExpand


class MergeCompanyInfo(APIView):
    @staticmethod
    def get(_):
        api_log(msg="Processing GET request in MergeAccounts...")
        comp_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN, api_key=settings.API_KEY)

        try:
            organization_data = comp_client.accounting.company_info.list(expand=CompanyInfoListRequestExpand.ADDRESSES)
        except Exception as e:
            api_log(
                msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            }
            for addr in organization_data.results[0].addresses
            # Assuming there is at least one organization in the results
        ]

        formatted_data = []
        for organization in organization_data.results:

            formatted_entry = {
                "id": organization.id,
                "remote_id": organization.remote_id,
                "name": organization.name,
                "legal_name": organization.legal_name,
                "tax_number": organization.tax_number,
                "fiscal_year_end_month": organization.fiscal_year_end_month,
                "fiscal_year_end_day": organization.fiscal_year_end_day,
                "currency": organization.currency,
                "remote_created_at": organization.remote_created_at,
                "urls": organization.urls,
                "addresses": formatted_addresses,  # Include the formatted addresses here
                "phone_numbers": [
                    {
                        "number": phone.number,
                        "type": phone.type,
                        "created_at": phone.created_at,
                        "modified_at": phone.modified_at,
                    }
                    for phone in organization.phone_numbers
                ],
                "remote_was_deleted": organization.remote_was_deleted,
                "created_at": organization.created_at,
                "modified_at": organization.modified_at,
                "field_mappings": organization.field_mappings,
                "remote_data": organization.remote_data,
            }
            formatted_data.append(formatted_entry)
        api_log(msg=f"FORMATTED DATA: {formatted_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergeCompanyDetails(APIView):
    @staticmethod
    def get(_, id=None):
        api_log(msg="Processing GET request in MergeAccounts...")
        comp_id_client = Merge(base_url=settings.BASE_URL, account_token=settings.ACCOUNT_TOKEN,
                                api_key=settings.API_KEY)

        try:
            organization_data = comp_id_client.accounting.company_info.retrieve(id=id,
                                                                                 expand=CompanyInfoRetrieveRequestExpand.ADDRESSES)

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
                } for addr in organization_data.addresses
            ]

            phone_types = [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at,
                    "modified_at": phone.modified_at,
                } for phone in organization_data.phone_numbers
            ]

            formatted_data = []
            formatted_entry = {
                "id": organization_data.id,
                "remote_id": organization_data.remote_id,
                "name": organization_data.name,
                "legal_name": organization_data.legal_name,
                "tax_number": organization_data.tax_number,
                "fiscal_year_end_month": organization_data.fiscal_year_end_month,
                "fiscal_year_end_day": organization_data.fiscal_year_end_day,
                "currency": organization_data.currency,
                "remote_created_at": organization_data.remote_created_at,
                "urls": organization_data.urls,
                "addresses": formatted_addresses,
                "phone_numbers": phone_types,
                "remote_was_deleted": organization_data.remote_was_deleted,
                "created_at": organization_data.created_at,
                "modified_at": organization_data.modified_at,
                "field_mappings": organization_data.field_mappings,
                "remote_data": organization_data.remote_data,
            }
            formatted_data.append(formatted_entry)

            api_log(msg=f"FORMATTED DATA: {formatted_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}")
            return Response(formatted_data, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)