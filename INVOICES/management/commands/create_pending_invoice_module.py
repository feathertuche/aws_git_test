import json
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
        #auth_token = ""
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.get(
                pending_url,
                # headers={"Authorization": f"Bearer {auth_token}"},
                headers=header,
            )
            if pending_invoice_response.status_code == status.HTTP_200_OK:
                api_payload = pending_invoice_response.json()
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
        for invoice_payload in payload:
            response = self.create_invoice(invoice_payload)
            if response:
                api_log(msg=f"Response in the PROCESS INVOICES function in management command file::: {response}")
                self.handle_invoice_response(invoice_payload)

    def handle_invoice_response(self, invoice_payload: dict):
        if invoice_payload["model"]["problem_type"] == "RATE_LIMITED":
            api_log(msg="setting cron execution time in table for 'RATE_LIMITED'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        elif invoice_payload["model"]["problem_type"] == "MISSING_PERMISSION":
            api_log(msg="setting cron execution time in table for 'MISSING_PERMISSION'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        else:
            api_log(msg=f"Error: Invoice {invoice_payload['model']['kloo_invoice_id']} not in 'RATE_LIMITED' or 'MISSING_PERMISSION'")

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
        retries = CronRetry.objects.filter(cron_execution_time__lte=datetime.now())
        for retry in retries:
            for invoice_payload in payload:
                api_log(msg=f"api payload in retry invoice function:: {invoice_payload}")
                if invoice_payload['model']['kloo_invoice_id'] == retry.kloo_invoice_id:
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