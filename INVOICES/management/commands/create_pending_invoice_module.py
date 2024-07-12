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


class MockRequest(HttpRequest):
    def __init__(self, data):
        super().__init__()
        self.data = data


class Command(BaseCommand):
    help = 'Process pending invoices and retry failed ones'

    def handle(self, *args, **options):
        self.read_pending_invoice_api()

    def create_invoice(self, payload: list):
        print("this is create invoice block")
        mock_request = MockRequest(data=payload)
        pending_invoice_creator = InvoiceCreate()
        response = pending_invoice_creator.post(mock_request)
        api_log(msg=f"create invoice in mangt:: {response}")
        self.stdout.write(f"invoice pending response:::: {response}")
        return response.data

    def read_pending_invoice_api(self):
        """
        GET API for pending list of invoices
        """
        pending_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/pending_post_invoices_erp"
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.get(
                pending_url,
                headers=header
            )
            if pending_invoice_response.status_code == status.HTTP_200_OK:
                api_payload = pending_invoice_response.json()
                formatted_paylaod = api_payload["result"]
                if isinstance(formatted_paylaod, list):
                    if not formatted_paylaod:
                        self.stdout.write("There is no invoice payload in the API")
                    else:
                        self.retry_invoices_from_api(formatted_paylaod)
                        self.process_invoices(formatted_paylaod)
                else:
                    self.stdout.write("Invalid payload format received from API")
                return pending_invoice_response
            else:
                pending_invoice_response.raise_for_status()
        except Exception as e:
            self.stdout.write(f"Error fetching pending invoices: {str(e)}")

    def process_invoices(self, payload):
        for invoice_payload in payload:
            response = self.create_invoice(invoice_payload)
            if response:
                api_log(msg=f"Response in the PROCESS INVOICES function in management command file::: {response}")
                self.handle_invoice_response(invoice_payload)

    def handle_invoice_response(self, invoice_payload: dict):
        if invoice_payload["model"]["problem_type"] == "RATE_LIMITED":
            api_log(msg="setting cron execution time in table for 'RATE_LIMITED'")
            self.schedule_retry(invoice_payload, timedelta(minutes=2))
        elif invoice_payload["model"]["problem_type"] == "MISSING_PERMISSION":
            api_log(msg="setting cron execution time in table for 'MISSING_PERMISSION'")
            self.schedule_retry(invoice_payload, timedelta(minutes=2))
        else:
            self.stdout.write(f"Error: Invoice {invoice_payload['model']['kloo_invoice_id']} not in 'RATE_LIMITED' or 'TIMEOUT'")

    def schedule_retry(self, invoice_payload: dict, retry_delay):
        retry_at = datetime.now() + retry_delay
        CronRetry.objects.create(
            id=uuid.uuid1(),
            kloo_invoice_id=invoice_payload['model']['kloo_invoice_id'],
            cron_execution_time=retry_at
        )
        self.stdout.write(f"Invoice {invoice_payload['model']['kloo_invoice_id']} will be retried at {retry_at}")

    def retry_invoices_from_api(self, payload: list):
        retries = CronRetry.objects.filter(cron_execution_time__lte=datetime.now())
        for retry in retries:
            for invoice in payload:
                api_log(msg=f"api payload in retry invoice function:: {invoice}")
                if invoice['model']['kloo_invoice_id'] == retry.kloo_invoice_id:
                    try:
                        response = self.create_invoice(invoice)
                        retry.delete()
                        if response:
                            self.handle_invoice_response(invoice, response)
                    except Exception as e:
                        retry.cron_execution_time = datetime.now() + timedelta(hours=1)
                        retry.save()
                        self.stdout.write(f"Error retrying invoice {invoice['model']['kloo_invoice_id']}: {str(e)}")
                    except TimeoutError:
                        retry.cron_execution_time = datetime.now() + timedelta(minutes=15)
                        retry.save()
#
#     # Function to determine status based on problem_type
#     # def determine_status(self, response):
#     #     errors = response.get("errors", [])
#     #     if errors:
#     #         problem_type = errors[0].get("problem_type", "").lower()
#     #         if problem_type in ["RATE_LIMITED", "timeout"]:
#     #             return "pending"
#     #         elif problem_type in ["provider_error", "model_not_found_error", "MISSING_REQUIRED_FIELD"]:
#     #             return "failure"
#     #     return "unknown"
#     #
#     # # Example of posting status to another API
#     # def post_status_to_api(status):
#     #     api_url = "https://example.com/api/status"  # Replace with your API endpoint
#     #     payload = {"status": status}
#     #     headers = {"Content-Type": "application/json"}
#     #     response = requests.post(api_url, data=json.dumps(payload), headers=headers)
#     #     return response
#
#     # # Determine status based on the response
#     # status = determine_status(response)
#     # print(f"Determined status: {status}")
#     #
#     # # Post the status to the API
#     # api_response = post_status_to_api(status)
#     # print(f"API response: {api_response.status_code}, {api_response.text}")

