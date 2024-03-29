import traceback

import requests
from merge.client import Merge
from merge.resources.accounting import (
    CompanyInfoListRequestExpand,
    CompanyInfoRetrieveRequestExpand,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL
from merge_integration.utils import create_merge_client


class MergeCompanyInfo(APIView):
    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def get_company_info(self):
        if self.link_token_details is None:
            # Handle the case where link_token_details is None
            print("link_token_details is None")
            return None

        if len(self.link_token_details) == 0:
            # Handle the case where link_token_details is an empty list
            print("link_token_details is an empty list")
            return None

        account_token = self.link_token_details
        comp_client = create_merge_client(account_token)

        try:
            organization_data = comp_client.accounting.company_info.list(
                expand=CompanyInfoListRequestExpand.ADDRESSES,
                page_size=100000,
                include_remote_data=True,
            )
            return organization_data
        except Exception as e:
            api_log(
                msg=f"Error retrieving organizations details: {str(e)} \
                 - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )

    @staticmethod
    def build_response_payload(organization_data):
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
                "created_at": addr.created_at.isoformat(),
                "modified_at": addr.modified_at.isoformat(),
            }
            for addr in organization_data.results[0].addresses
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
                "remote_created_at": organization.remote_created_at.isoformat(),
                "urls": organization.urls,
                "addresses": formatted_addresses,
                "phone_numbers": [
                    {
                        "number": phone.number,
                        "type": phone.type,
                        "created_at": organization.created_at.isoformat(),
                        "modified_at": organization.modified_at.isoformat(),
                    }
                    for phone in organization.phone_numbers
                ],
                "remote_was_deleted": organization.remote_was_deleted,
                "created_at": organization.created_at.isoformat(),
                "modified_at": organization.modified_at.isoformat(),
                "field_mappings": organization.field_mappings,
                "remote_data": None,
            }
            formatted_data.append(formatted_entry)
            kloo_format_json = {"companies": formatted_data}

        return kloo_format_json

    def get(self, request, *args, **kwargs):
        api_log(msg=".....Processing Company GET request bloc.....")

        organization_data = self.get_company_info()
        formatted_data = self.build_response_payload(organization_data)

        api_log(
            msg=f"FORMATTED DATA: {formatted_data} \
             - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
        )
        return Response(formatted_data, status=status.HTTP_200_OK)


class MergeCompanyDetails(APIView):
    @staticmethod
    def get(_, id=None):
        api_log(msg="Processing GET request in MergeCompany...")
        comp_id_client = Merge(
            base_url=settings.BASE_URL,
            account_token=settings.ACCOUNT_TOKEN,
            api_key=settings.API_KEY,
        )

        try:
            organization_data = comp_id_client.accounting.company_info.retrieve(
                id=id, expand=CompanyInfoRetrieveRequestExpand.ADDRESSES
            )

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
                for addr in organization_data.addresses
            ]

            phone_types = [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at,
                    "modified_at": phone.modified_at,
                }
                for phone in organization_data.phone_numbers
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
                "erp_remote_data": organization_data.remote_data,
            }
            formatted_data.append(formatted_entry)

            api_log(
                msg=f"FORMATTED DATA: {formatted_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
            )
            return Response(formatted_data, status=status.HTTP_200_OK)

        except Exception as e:
            api_log(
                msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
            )
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergeKlooCompanyInsert(APIView):
    """
    This class is created for parsing company info data
    """

    def __init__(self, link_token_details=None):
        super().__init__()
        self.link_token_details = link_token_details

    def post(self, request):
        """
        This POST method fetch the company info Merge data
        and send it to the Kloo DB erp_company table.

        request: to fetch merge data
        """
        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")
        merge_company_list = MergeCompanyInfo(
            link_token_details=self.link_token_details
        )
        response = merge_company_list.get(request=request)
        try:
            if response.status_code == status.HTTP_200_OK:
                merge_payload = response.data
                merge_payload["erp_link_token_id"] = erp_link_token_id
                merge_payload["org_id"] = org_id
                kloo_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-companies"

                api_log(msg=f"merge_payload: {kloo_url}")
                kloo_data_insert = requests.post(
                    kloo_url,
                    json=merge_payload,
                )

                if kloo_data_insert.status_code == status.HTTP_201_CREATED:
                    return Response(
                        "successfully inserted the data for COMPANY INFO with "
                    )
                else:
                    return Response(
                        {"error": "Failed to send data to Kloo API"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        except Exception as e:
            error_message = f"Failed to send data to Kloo API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"error": "Authorization header is missing"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
