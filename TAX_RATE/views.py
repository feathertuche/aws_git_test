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
from django.utils import timezone
from SYNC.models import ERPLogs
from .helper_function import sage_tax_rate
from LINKTOKEN.model import ErpLinkToken
from merge_integration import settings
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL, tax_rate_page_size, tax_rate_batch_size
from merge_integration.utils import create_merge_client
from .queries import Insert_Sage_Tax_Rates, save_tax_rate
from services.merge_service import MergePassthroughApiService


class MergeTaxRatesList(APIView):
    """
    API view for retrieving Merge Tax Rate list.
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
                page_size=tax_rate_page_size,
                include_remote_data=True,
                modified_after=self.last_modified_at,
            )

            all_tax_rates = []
            while True:
                api_log(msg=f"Adding {len(tax_data.results)} tax rates to the list.")

                all_tax_rates.extend(tax_data.results)
                if tax_data.next is None:
                    break

                tax_data = merge_client.accounting.tax_rates.list(
                    page_size=tax_rate_page_size,
                    include_remote_data=True,
                    modified_after=self.last_modified_at,
                    cursor=tax_data.next,
                )

                api_log(
                    msg=f"Tax Rates GET:: The length of the next page account data is : {len(tax_data.results)}"
                )
                api_log(msg=f"Length of all_accounts: {len(tax_data.results)}")

            api_log(
                msg=f"Tax Rates GET:: The length of all account data is : {len(all_tax_rates)}"
            )

            return all_tax_rates

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
        for taxdata in tax_data:
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
                "created_at": taxdata.created_at.isoformat(),
                "modified_at": taxdata.modified_at.isoformat(),
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
        if tax_data is None or len(tax_data) == 0:
            return Response({"taxRates": []}, status=status.HTTP_204_NO_CONTENT)

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
                "created_at": tax_client.created_at.isoformat(),
                "modified_at": tax_client.modified_at.isoformat(),
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

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        """
        Handles POST requests to insert Merge Tax Rate data into the Kloo Tax Rate system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")
        fetch_data = MergeTaxRatesList(
            link_token_details=self.link_token_details,
            last_modified_at=self.last_modified_at,
        )
        tax_data = fetch_data.get(request=request)

        try:
            if tax_data.status_code == status.HTTP_200_OK:
                tax_payload = tax_data.data
                tax_payload["erp_link_token_id"] = erp_link_token_id
                tax_payload["org_id"] = org_id
                api_log(
                    msg=f"Posting tax_rates data to Kloo: {json.dumps(tax_payload)}"
                )
                tax_url = f"{GETKLOO_LOCAL_URL}/organizations/insert-erp-tax-rates"

                # Payload and logic for batch size
                data = tax_payload["taxRates"]
                payload = dict()
                payload["erp_link_token_id"] = erp_link_token_id
                payload["org_id"] = org_id

                batch_size = tax_rate_batch_size
                api_log(msg=f"[BATCH SIZE]:: {batch_size}")
                for batch in range(0, len(data), batch_size):
                    api_log(msg=f"[BATCH SIZE]:: {batch_size}")
                    api_log(msg=f"[BATCH]:: {batch}")
                    batch_data = data[batch:batch + batch_size]
                    payload["taxRates"] = batch_data
                    api_log(msg=f"[PAYLOAD]:: {batch_data}")

                    tax_response_data = requests.post(
                        tax_url,
                        json=payload,
                    )

                    api_log(msg=f"tax_response_data: {tax_response_data}")

                if tax_response_data.status_code == status.HTTP_201_CREATED:
                    api_log(
                        msg="data inserted successfully in the kloo Tax Rate system"
                    )
                    return Response(
                        {"message": "API Tax rate Info completed successfully"}
                    )

                else:
                    return Response(
                        {"error": "Failed to send data to Kloo Tax Rate API"},
                        status=tax_response_data.status_code,
                    )

            if tax_data.status_code == status.HTTP_204_NO_CONTENT:
                return Response(
                    {"message": "No new data found to insert in the kloo tax system"},
                    status=status.HTTP_204_NO_CONTENT,
                )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Tax Rate API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response("Failed to insert data to the kloo Tax Rate system", traceback)


class SageFetchTaxDetails(APIView):
    """
    API view for inserting Merge Tax Rate data into the Kloo Tax Rate system.
    """

    def __init__(self, erp_link_token_id=None):
        super().__init__()
        self.erp_link_token_id = erp_link_token_id

    def post(self, request):
        """
        Handles POST requests to insert Sage Tax Rate data into the Kloo Tax Rate system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        api_log(msg="...............Entering SageFetchTaxDetails POST method.................")

        try:
            # Django ORM query to fetch org_id and account_token
            self.erp_link_token_id = request.data.get("erp_link_token_id")
            api_log(msg=f"erp link token ID in Sage passthrough:: {self.erp_link_token_id}")
            filter_token = ErpLinkToken.objects.filter(id=self.erp_link_token_id)
            lnk_token = filter_token.values_list("account_token", "org_id", flat=False)
            account_token, org_id = lnk_token[0]
            api_log(msg=f"account token and org ID in Sage passthrough:: {account_token} --- {org_id}")

            # Function call to save the Tax rate data to erp_sync_logs table if not present
            # save_tax_rate(org_id, self.erp_link_token_id)
            #
            # erp_log = ERPLogs.objects.get(
            #         link_token_id=self.erp_link_token_id, label="SAGE TAX RATE"
            #     )
            tax_rates_details = MergePassthroughApiService(
                account_token, org_id, self.erp_link_token_id
            )
            response = sage_tax_rate(tax_rates_details)
            if response["status"] is False:
                return Response(
                    {"error": response["error"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            api_log(msg=f"Sage Tax Rate fetched successfully : {response['message']}")

            # fetch "data" key from the passthrough payload
            sage_tax_details = response.get("data")
            api_log(msg=f"Sage Tax Rate payload in API View : {sage_tax_details}")

            # data insertion logic here to DB
            if sage_tax_details:
                for tax_fields in sage_tax_details:
                    tax_fields["erp_link_token_id"] = self.erp_link_token_id
                    tax_fields["organization_id"] = org_id
                    api_log(msg=f"tax_rate_fields : {tax_fields}")
                    Insert_Sage_Tax_Rates(tax_fields)
            else:
                api_log(msg=f"There is no data in Sage passthrough API:=> {status.HTTP_204_NO_CONTENT}")

            # erp_log.sync_status = "success"
            # erp_log.error_message = (
            #     "SAGE TAX RATE completed successfully"
            # )
            # erp_log.sync_end_time = timezone.now()
            # erp_log.save()
            return Response(
                    {"success": response["status"]},
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            api_log(msg=f"Error fetching sage data: {e}")
            raise e