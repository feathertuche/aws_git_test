import re
import uuid
from datetime import timedelta, datetime
from rest_framework import status
import requests
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from merge_integration.helper_functions import api_log


class MockRequest(HttpRequest):
    def __init__(self, data):
        super().__init__()
        self.data = data


class Command(BaseCommand):
    api_log(msg='..........Processing pending invoices through CRON.........')

    def __init__(self):
        super().__init__()
        self.formatted_payload = []

    def handle(self, *args, **options):
        """
        The entry point function for Django management command execution
        """
        self.read_pending_invoice_api()

    def create_invoice(self, payload: list):
        """
            Function to call InvoiceCreate class to execute Invoices

        Parameters:
        payload (dict type): It accepts a single or series objects.

        Returns:
            return_type: Invoice data
        """
        from INVOICES.views import InvoiceCreate
        api_log(msg="this is create invoice block")
        mock_request = MockRequest(data=payload)
        pending_invoice_creator = InvoiceCreate()
        response = pending_invoice_creator.post(mock_request)
        api_log(msg=f"create invoice in management command file:: {response}")
        return response.data

    def read_pending_invoice_api(self):
        """
        GET API for pending list of invoices
        Returns:
            return_type: API response
        """

        from merge_integration.settings import GETKLOO_LOCAL_URL
        api_log(msg="Fetching pending invoices from Back-end api for cron execution....")
        pending_url = f"{GETKLOO_LOCAL_URL}/ap/erp-integration/pending_post_invoices_erp"
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.get(
                pending_url,
                headers=header,
            )
            api_log(msg=f"LARAVEL API response::: {pending_invoice_response}")
            if pending_invoice_response.status_code == status.HTTP_200_OK:
                api_payload = pending_invoice_response.json()
                self.formatted_payload = api_payload["result"]
                if isinstance(self.formatted_payload, list):
                    if not self.formatted_payload:
                        api_log(msg="There is no invoice payload in the API")
                    else:
                        api_log(msg=f"formatted payload in CRON Invoice:: {self.formatted_payload}")
                        self.process_invoices(self.formatted_payload)
                        self.retry_invoices_from_api(self.formatted_payload)
                        self.formatted_payload = []
                else:
                    api_log(msg="Invalid payload format received from API")
                return pending_invoice_response
            else:
                api_log(msg="The error coming from CRON Invoice script: {}".format(
                    pending_invoice_response.raise_for_status()))
        except Exception as e:
            api_log(msg=f"Error fetching pending invoices in CRON script: {str(e)}")

    def process_invoices(self, payload):
        """
        Method to execute all new Invoices and set the cron time if Invoice in Pending state

        Parameters:
        payload (dict type): It accepts a single or series objects.

        Returns:
            return_type: None
        """
        from INVOICES.models import InvoiceAttachmentLogs
        from INVOICES.models import CronRetry

        kloo_invoice_ids = CronRetry.objects.values_list('kloo_invoice_id', flat=True)
        kloo_invoice_ids_list = list(kloo_invoice_ids)

        invoices = []
        pattern = r"'problem_type': '([^']+)'"

        for invoice_payload in payload:
            if invoice_payload['model']['kloo_invoice_id'] not in kloo_invoice_ids_list:
                response = self.create_invoice(invoice_payload)

                api_log(msg=f"string type response:: {str(response)}")
                api_log(msg=f"Original response:: {response}")

                # Extract the status code using regex
                status_code_match = re.search(r'status_code:\s*(\d+)', str(response))
                status_code = int(status_code_match.group(1)) if status_code_match else None
                api_log(msg=f"STATUS CODE in PROCESS INVOICE method:::: {status_code}")

                if status_code:
                    if status_code in [404, 400]:
                        api_log(
                            msg=f"Error creating invoice: status_code: {status_code}, body: {response}")

                        invoice_id = invoice_payload['model']['kloo_invoice_id']
                        api_log(msg=f"invoice ID in process invoice method:: {invoice_id}")

                        # Extract problem_type using regex
                        match = re.search(pattern, response['error'])
                        if match:
                            problem_type = match.group(1)
                            api_log(msg=f"problem type:: {problem_type}")
                        else:
                            problem_type = None
                            api_log(msg=f"problem type not found")

                        # Determine status based on the extracted problem_type
                        if problem_type in ['RATE_LIMITED', 'TIMED_OUT']:
                            error_status = 'pending'
                        else:
                            error_status = 'failed'

                        api_log(
                            msg=f"Response in the PROCESS INVOICES function in management command file::: {response} and "
                                f"Invoice_id is {invoice_id}")

                        # Append the status to the invoices list
                        invoices.append({
                            'id': invoice_id,
                            'status': error_status
                        })

                        # Update problem_type in InvoiceAttachmentLogs
                        update_invoice_id = str(invoice_id)
                        api_log(msg=f"update invoice id: {update_invoice_id}")
                        new_invoice_id = "".join(update_invoice_id.split("-"))
                        api_log(msg=f"new invoice id: {new_invoice_id}")
                        log = InvoiceAttachmentLogs.objects.filter(invoice_id=new_invoice_id).first()
                        if log:
                            log.problem_type = problem_type
                            log.save()
                        api_log(msg=f"log problem type column value::: {log.problem_type}")
                        self.handle_invoice_response(invoice_payload)

        # Log or return the invoices JSON
        final_update = {"invoices": invoices}
        api_log(msg=f"final update JSON: {final_update}")
        self.post_response(final_update)

    def handle_invoice_response(self, invoice_payload: dict):
        """
        helper function to set cron time for different types of exception
        """

        if invoice_payload["model"]["problem_type"] == "RATE_LIMITED":
            api_log(msg="setting cron execution time in table for 'RATE_LIMITED'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        elif invoice_payload["model"]["problem_type"] == "TIMED_OUT":
            api_log(msg="setting cron execution time in table for 'MISSING_PERMISSION'")
            self.schedule_retry(invoice_payload, timedelta(minutes=5))
        else:
            api_log(msg=f"Error: Invoice {invoice_payload['model']['kloo_invoice_id']} not in 'RATE_LIMITED' or "
                        f"'TIMED_OUT'")

    def schedule_retry(self, invoice_payload: dict, retry_delay):
        """
        Helper function to insert the data to erp_pending_invoices_retry table

        Parameters:
        invoice_payload (dict type): It accepts a single or series objects.
        retry_delay (datetime): It accepts the timedelta for cron execution.

        Returns:
            return_type: None
        """

        from INVOICES.models import CronRetry
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
        """
        A method to execute the invoice ID defined in erp_pending_invoices_retry table

        Parameters:
        payload (array type): It accepts a list of objects

        Returns:
            return_type: None
        """
        from INVOICES.models import CronRetry
        retries = CronRetry.objects.filter(cron_execution_time__lte=datetime.now())

        for retry in retries:
            for invoice_payload in payload:
                api_log(msg=f"api payload in retry invoice function:: {invoice_payload}")
                api_log(msg=f"DB table kloo ID:: {retry.kloo_invoice_id}")
                if invoice_payload['model']['kloo_invoice_id'] == retry.kloo_invoice_id:
                    try:
                        response = self.create_invoice(invoice_payload)
                        api_log(msg=f"Response from create invoice in RETRY INVOICES method :=> {response}")
                        api_log(msg=f"Response DATA from create invoice in RETRY INVOICES method :=> {response.data}")
                        retry.delete()
                        api_log(msg="Retry deleted successfully")
                        if response:
                            self.handle_invoice_response(invoice_payload)
                    except Exception as e:
                        retry.cron_execution_time = datetime.now() + timedelta(minutes=5)
                        retry.save()
                        api_log(msg=f"Error retrying invoice {invoice_payload['model']['kloo_invoice_id']}: {str(e)}")
                    except TimeoutError:
                        retry.cron_execution_time = datetime.now() + timedelta(minutes=5)
                        retry.save()

    def post_response(self, response: dict):
        """
        A helper function to accept the request to set failed or pending state for Invoices in invoices table.

        Parameters:
        response (dict type): It accepts a jSON format data

        Returns:
            return_type: None
        """

        from merge_integration.settings import GETKLOO_LOCAL_URL
        pending_url = f"{GETKLOO_LOCAL_URL}/ap/erp-integration/update_accounting_portal_status"
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.post(
                pending_url,
                headers=header,
                json=response
            )
            if pending_invoice_response.status_code in [200, 201]:
                api_log(msg=f"Successfully UPDATED the response code: {response}")
            else:
                api_log(
                    msg=f"Failed to update response code:::: {response}. Status Code:::: {pending_invoice_response.status_code}")
        except Exception as e:
            api_log(msg=f"Exception occurred while posting invoices: {str(e)}")

