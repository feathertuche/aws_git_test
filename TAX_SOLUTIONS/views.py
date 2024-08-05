import json
import traceback

import requests
from merge.client import Merge
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
import logging
from merge_integration import settings
import uuid
from django.utils import timezone
from datetime import datetime
from merge_integration.utils import create_merge_client
from .models import PassthroughTaxSolution
from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from merge_integration.settings import (
    invoices_page_size,
    contacts_page_size,
    tax_rate_page_size,
    API_KEY,
    MERGE_BASE_URL,
    items_rate_page_size,
)

logger = logging.getLogger(__name__)
class TaxSolutions(APIView):

    def generate_session_data(self):
        # Generate temp_session_id
        temp_session_id = str(uuid.uuid4())
        # Generate timestamp
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        # Generate guid
        guid = str(uuid.uuid4())
        return temp_session_id, timestamp, guid

    def get(self, request, org_id=None, link_token_id=None):

        if org_id is None or link_token_id is None:
            api_log(msg="SYNC view2: Missing org_id or link_token_id")
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters: org_id or link_token_id.'
            }, status=400)

        account_token = ErpLinkToken.get_account_token_by_id(link_token_id)
        api_log(msg=f"SYNC view2: account_token{account_token}")

        api_log(msg=f"SYNC view2: org id {org_id}")

        try:
            # Extract necessary data from request or use default values
            passthrough_url = f"{MERGE_BASE_URL}/api/accounting/v1/passthrough"
            api_log(msg=f"passthrough_url {passthrough_url}")

            payload = {
                "method": "POST",
                "path": "/ia/xml/xmlgw.phtml",
                "request_format": "XML",
                "headers": {
                    "Content-Type": "application/xml"
                },
                "data": (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<request>"
                    "<control>"
                    "<senderid>{sender_id}</senderid>"
                    "<password>{sender_password}</password>"
                    "<controlid>{timestamp}</controlid>"
                    "<uniqueid>false</uniqueid>"
                    "<dtdversion>3.0</dtdversion>"
                    "<includewhitespace>false</includewhitespace>"
                    "</control>"
                    "<operation>"
                    "<authentication>"
                    "<sessionid>{temp_session_id}</sessionid>"
                    "</authentication>"
                    "<content>"
                    "<function controlid='{guid}'>"
                    "<readByQuery>"
                    "<object>TAXSOLUTION</object>"
                    "<fields>*</fields>"
                    "<query></query>"
                    "<pagesize>100</pagesize>"
                    "</readByQuery>"
                    "</function>"
                    "</content>"
                    "</operation>"
                    "</request>"
                )
            }

            headers = {
                'X-Account-Token': account_token,
                'Content-Type': 'application/json',
                'Authorization':  f'Bearer {API_KEY}',
            }

            api_log(msg=f"SYNC view2: account_token{account_token}")
            response = requests.post(passthrough_url, headers=headers, json=payload)
            # Extract and print specific parts of the response
            response_data = response.json()

            if response.status_code == 200:
                response_data = response.json()  # Assuming response data needs to be parsed from JSON

                # Inserting or updating the tax solutions into the database
                for tax_solution in response_data['response']['response']['operation']['result']['data']['taxsolution']:
                    solutionid = tax_solution.get('SOLUTIONID')
                    recordno = tax_solution.get('RECORDNO')

                    # Use `update_or_create` to handle insert or update
                    obj, created = PassthroughTaxSolution.objects.update_or_create(
                        linktoken_id=link_token_id,
                        recordno=recordno,
                        org_id=org_id,
                        defaults={
                            'solutionid': solutionid,
                            'description': tax_solution.get('DESCRIPTION'),
                            'taxmethod': tax_solution.get('TAXMETHOD'),
                            'status': tax_solution.get('STATUS'),
                            'type': tax_solution.get('TYPE'),
                            'startdate': datetime.strptime(tax_solution.get('STARTDATE'),
                                                           '%m/%d/%Y').date() if tax_solution.get(
                                'STARTDATE') else timezone.now(),
                            'showmultilinetax': tax_solution.get('SHOWMULTILINETAX') == 'true',
                            'aradvanceoffsetacct': tax_solution.get('ARADVANCEOFFSETACCT'),
                            'aradvanceoffsetaccttitle': tax_solution.get('ARADVANCEOFFSETACCTTITLE'),
                            'aradvanceoffsetacctkey': tax_solution.get('ARADVANCEOFFSETACCTKEY'),
                            'glaccountpurchase': tax_solution.get('GLACCOUNTPURCHASE'),
                            'glaccountpurchasetitle': tax_solution.get('GLACCOUNTPURCHASETITLE'),
                            'glaccountpurchasekey': tax_solution.get('GLACCOUNTPURCHASEKEY'),
                            'glaccountsale': tax_solution.get('GLACCOUNTSALE'),
                            'glaccountsaletitle': tax_solution.get('GLACCOUNTSALETITLE'),
                            'glaccountsalekey': tax_solution.get('GLACCOUNTSALEKEY'),
                            'altsetup': tax_solution.get('ALTSETUP') == 'false',
                            'lastupdate': timezone.now()  # Replace with the actual `LASTUPDATE` if available
                        }
                    )

                # Return success response
                return JsonResponse({
                    'status': 'success',
                    'message': 'Data inserted or updated successfully.'
                }, status=200)
            else:
                # Handle error
                return JsonResponse({
                    'status': 'error',
                    'message': f"Request failed with status code {response.status_code}"
                }, status=500)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f"An unexpected error occurred: {str(e)}"
            }, status=500)


