import json
import logging
import re
import time
import uuid
from datetime import timedelta, datetime
from rest_framework import status
import requests
from django.core.management.base import BaseCommand
from INVOICES.views import InvoiceCreate
from django.http import HttpRequest
from INVOICES.models import CronRetry
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_BASE_URL

logger = logging.getLogger(__name__)


class MockRequest(HttpRequest):
    def __init__(self, data):
        super().__init__()
        self.data = data


class Command(BaseCommand):
    help = 'Process pending invoices and retry failed ones'

    def handle(self, *args, **options):
        self.read_pending_invoice_api()

    def create_invoice(self, payload: list):
        api_log(msg="this is create invoice block")
        mock_request = MockRequest(data=payload)
        pending_invoice_creator = InvoiceCreate()
        response = pending_invoice_creator.post(mock_request)
        api_log(msg=f"create invoice in management command file:: {response}")
        return response.data

    def read_pending_invoice_api(self):
        """
        GET API for pending list of invoices
        """
        pending_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/pending_post_invoices_erp"
        # auth_token = ""
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.get(
                pending_url,
                # headers={"Authorization": f"Bearer {auth_token}"},
                headers=header,
            )
            if pending_invoice_response.status_code == status.HTTP_200_OK:
                api_payload = pending_invoice_response.json()
                time.sleep(3)
                print("sleeping for 3 seconds......")
                formatted_paylaod = api_payload["result"]
                if isinstance(formatted_paylaod, list):
                    if not formatted_paylaod:
                        api_log(msg="There is no invoice payload in the API")
                    else:
                        self.retry_invoices_from_api(formatted_paylaod)
                        self.process_invoices(formatted_paylaod)
                else:
                    api_log(msg="Invalid payload format received from API")
                return pending_invoice_response
            else:
                pending_invoice_response.raise_for_status()
        except Exception as e:
            api_log(msg=f"Error fetching pending invoices: {str(e)}")

    def process_invoices(self, payload):
        invoices = []  # Initialize an empty list to hold the invoice statuses

        pattern = r"'problem_type': '(\w+)'"

        for invoice_payload in payload:
            response = self.create_invoice(invoice_payload)
            if response:
                invoice_id = invoice_payload['model']['kloo_invoice_id']

                # Extract problem_type using regex
                match = re.search(pattern, str(response))
                if match:
                    problem_type = match.group(1)
                    api_log(msg=f"problem_type:: {problem_type}")
                else:
                    problem_type = None
                    api_log(msg=f"problem_type not found")

                # Determine status based on the extracted problem_type
                if problem_type in ['RATE_LIMITED', 'TIMED_OUT']:
                    status = 'pending'
                elif problem_type == 'PROVIDER_ERROR':
                    status = 'failed'
                else:
                    status = 'unknown'  # Handle other cases if necessary

                api_log(msg=f"Response in the PROCESS INVOICES function in management command file::: {response} and "
                            f"Invoice_id is {invoice_id}")

                # Append the status to the invoices list
                invoices.append({
                    'id': invoice_id,
                    'status': status
                })

                self.handle_invoice_response(invoice_payload)

        # Log or return the invoices JSON
        api_log(msg=f"Final invoices JSON: {invoices}")
        self.post_response(invoices)

    def handle_invoice_response(self, invoice_payload: dict):
        if invoice_payload["model"]["problem_type"] == "RATE_LIMITED":
            api_log(msg="setting cron execution time in table for 'RATE_LIMITED'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        elif invoice_payload["model"]["problem_type"] == "MISSING_PERMISSION":
            api_log(msg="setting cron execution time in table for 'MISSING_PERMISSION'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        else:
            api_log(msg=f"Error: Invoice {invoice_payload['model']['kloo_invoice_id']} not in 'RATE_LIMITED' or "
                        f"'MISSING_PERMISSION'")

    def schedule_retry(self, invoice_payload: dict, retry_delay):
        retry_at = datetime.now() + retry_delay
        kloo_invoice_id = invoice_payload['model']['kloo_invoice_id']

        retry_entry, created = CronRetry.objects.update_or_create(
            id=uuid.uuid1(),
            kloo_invoice_id=kloo_invoice_id,
            defaults={'cron_execution_time': retry_at}
        )
        if created:
            api_log(msg=f"New retry scheduled for invoice {kloo_invoice_id} at {retry_at}")
        else:
            api_log(msg=f"Updated retry time for invoice {kloo_invoice_id} to {retry_at}")

    def retry_invoices_from_api(self, payload: list):
        api_log(msg=f"34")
        retries = CronRetry.objects.filter(cron_execution_time__lte=datetime.now())
        for retry in retries:
            for invoice_payload in payload:
                api_log(msg=f"api payload in retry invoice function:: {invoice_payload}")
                if invoice_payload['model']['kloo_invoice_id'] == retry.kloo_invoice_id:
                    t = invoice_payload['model']['kloo_invoice_id']
                    b = retry.kloo_invoice_id
                    api_log(msg=f"this is payload invoice id::{t}")
                    api_log(msg=f"this is DB invoice id::{b}")
                    try:
                        response = self.create_invoice(invoice_payload)
                        retry.delete()
                        if response:
                            self.handle_invoice_response(invoice_payload)
                    except Exception as e:
                        retry.cron_execution_time = datetime.now() + timedelta(minutes=5)
                        retry.save()
                        api_log(msg=f"Error retrying invoice {invoice_payload['model']['kloo_invoice_id']}: {str(e)}")
                    except TimeoutError:
                        retry.cron_execution_time = datetime.now() + timedelta(minutes=5)
                        retry.save()

    def post_response(self, response: list):
        pending_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/update_accounting_portal_status"
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.post(
                pending_url,
                headers=header,
                data=json.dumps(response)  # Convert the response list to JSON format
            )
            if pending_invoice_response.status_code in [200, 201]:
                api_log(msg=f"Successfully posted invoices: {response}")
            else:
                api_log(msg=f"Failed to post invoices: {response}. Status Code: {pending_invoice_response.status_code}")
        except Exception as e:
            api_log(msg=f"Exception occurred while posting invoices: {str(e)}")


def process_pending_invoice():
    print("Started Processing")
    api_log(msg="Started Processing")
    try:
        Command().handle()
    except Exception as e:
        print(e)
        api_log(msg=f"Error while procesing pending invoice {str(e)}")
    print("End Processing")
    api_log(msg="End Processing")