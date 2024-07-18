import json
import re
import uuid
from datetime import timedelta, datetime
from rest_framework import status
import requests
from django.core.management.base import BaseCommand
from django.http import HttpRequest

from INVOICES.models import InvoiceAttachmentLogs
from merge_integration.helper_functions import api_log


# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "merge_integration.settings")

# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()


class MockRequest(HttpRequest):
    def __init__(self, data):
        super().__init__()
        self.data = data


class Command(BaseCommand):
    api_log(msg='Process pending invoices and retry failed ones')

    def __init__(self):
        super().__init__()
        self.formatted_payload = []

    def handle(self, *args, **options):
        self.read_pending_invoice_api()

    def create_invoice(self, payload: list):
        from INVOICES.views import InvoiceCreate
        api_log(msg="this is create invoice block")
        mock_request = MockRequest(data=payload)
        pending_invoice_creator = InvoiceCreate()
        response = pending_invoice_creator.post(mock_request)
        api_log(msg=f"create invoice in management command file:: {response}")
        return response.data

    def read_pending_invoice_api(self):
        from merge_integration.settings import GETKLOO_BASE_URL
        """
        GET API for pending list of invoices
        """
        api_log(msg="Fetching pending invoices from Back-end api for cron execution....")
        pending_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/pending_post_invoices_erp"
        auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiJiNGRmMWY3NjEyZGIxYjMzNzQwMzBiMjBhMmU1N2NlNzU1MWYzN2JiNWQ5ZDYxMDE4ZDc0MzlhODU4Mjk3YzhkN2UyYWQzYTIxODFlNDNjOSIsImlhdCI6MTcyMDc4MzY3NC42ODk4NzQsIm5iZiI6MTcyMDc4MzY3NC42ODk4NzcsImV4cCI6MTcyMDc4Mzk3NC42ODA4NjEsInN1YiI6IiIsInNjb3BlcyI6WyIqIl0sImN1c3RvbV9jbGFpbSI6IntcInVzZXJcIjp7XCJpZFwiOlwiODBiMGVjZjktMjE3MS00YzMwLWE2MTItODc4NjQ1MTNlYjA1XCIsXCJmaXJzdF9uYW1lXCI6XCJhbWl0ZXNoXCIsXCJtaWRkbGVfbmFtZVwiOm51bGwsXCJsYXN0X25hbWVcIjpcInNhaGF5XCIsXCJlbWFpbFwiOlwiYW1pdGVzaC5zYWhheUBnZXRrbG9vLmNvbVwiLFwiYmlydGhfZGF0ZVwiOlwiMTk4NC0xMi0zMVwiLFwidXNlcl9jcmVhdGVkX2J5XCI6bnVsbCxcImxvZ2luX2F0dGVtcHRzXCI6MCxcInN0YXR1c1wiOlwidW5ibG9ja2VkXCIsXCJjcmVhdGVkX2F0XCI6XCIyMDIzLTEwLTA1VDExOjA4OjAxLjAwMDAwMFpcIixcInVwZGF0ZWRfYXRcIjpcIjIwMjQtMDItMjJUMDU6NDg6NTAuMDAwMDAwWlwiLFwidXNlcl9vcmdfaWRcIjpcIjFkNzAwZjNjLTMyYzAtNDI1NS05NTZkLTI0ZGRmNTZlNDc4ZlwiLFwib3JnYW5pemF0aW9uX2lkXCI6XCIwYWFiZjVlZS1lMjZlLTRkODYtYTUxOC1lZWNiMDM5YTllNzdcIixcIm9yZ2FuaXphdGlvbl9uYW1lXCI6XCJLbG9vRGV2XCJ9LFwic2NvcGVzXCI6W1wiY2FyZC1leHBlbnNlcy1kb3dubG9hZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstZm9yLXJldmlldy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtbWFyay1hcy1hcHByb3ZlZC11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtc2F2ZS1hcy1kcmFmdC11cGRhdGVcIixcInBheW1lbnQtcnVucy1jcmVhdGVcIixcInBheW1lbnQtcnVucy1yZWFkXCIsXCJwYXltZW50LXJ1bnMtdXBkYXRlXCIsXCJwYXltZW50LXJ1bnMtZGVsZXRlXCIsXCJzdWJzY3JpcHRpb24tY3JlYXRlXCIsXCJzdWJzY3JpcHRpb24tcmVhZFwiLFwic3Vic2NyaXB0aW9uLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWRlbGV0ZVwiLFwidGVzdC1tb2R1bGUtYTEtY3JlYXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMS1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMS11cGRhdGVcIixcInRlc3QtbW9kdWxlLWExLWRlbGV0ZVwiLFwiaW52b2ljZS1wby1tYXRjaGluZy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jYXJkcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1wdXJjaGFzZS1vcmRlcnMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaGlzdG9yeS1yZWFkXCIsXCJzZXR0aW5nLXBheWVlLW1hbmFnZW1lbnQtcmVhZFwiLFwidXBkYXRlLXBlcm1pc3Npb24tcmV0b29sLXRlc3QtY3JlYXRlXCIsXCJ1cGRhdGUtcGVybWlzc2lvbi1yZXRvb2wtdGVzdC1yZWFkXCIsXCJkYXNoYm9hcmQtcG8tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJwYXktdmlhLXlhcGlseS1yZWFkXCIsXCJzY2hlZHVsZS10YWItcmVhZFwiLFwidXBkYXRlLXBlcm1pc3Npb24tcmV0b29sLXRlc3QtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtY3JlYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtcmVhZFwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLXVwZGF0ZVwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLWRlbGV0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1jcmVhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtcmVhZFwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS11cGRhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtZGVsZXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwic2V0dGluZy1uZXctcGF5ZWUtY29udGFjdC1yZWFkXCIsXCJpbnZvaWNlLW1hdGNoaW5nLXJlYWRcIixcInRlc3QtbW9kdWxlLWEyLWNyZWF0ZVwiLFwidGVzdC1tb2R1bGUtYTItcmVhZFwiLFwidGVzdC1tb2R1bGUtYTItdXBkYXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMi1kZWxldGVcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLWludm9pY2VzLXNjaGVkdWxlLXJlYWRcIixcInBheS1ub3ctYnV0dG9uLXJlYWRcIixcInNldHRpbmctaW50ZWdyYXRpb25zLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmllcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1yZWFkXCIsXCJzZXR0aW5nLWFkZHJlc3MtcmVhZFwiLFwiZGFzaGJvYXJkLXJlYWRcIixcImFwcHJvdmFscy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1zdXBwbGllci1yZWFkXCIsXCJhY2NvdW50LWRldGFpbHMtcmVhZFwiLFwiZGViaXQtYWNjb3VudC1jcmVhdGVcIixcImRlYml0LWFjY291bnQtcmVhZFwiLFwiZGViaXQtYWNjb3VudC11cGRhdGVcIixcImRlYml0LWFjY291bnQtZGVsZXRlXCIsXCJzdGFuZGluZy1vcmRlci1jcmVhdGVcIixcInN0YW5kaW5nLW9yZGVyLXJlYWRcIixcImltbWVkaWF0ZS1wYXltZW50LWNyZWF0ZVwiLFwiaW1tZWRpYXRlLXBheW1lbnQtcmVhZFwiLFwiYmFuay10cmFuc2Zlci1jcmVhdGVcIixcImJhbmstdHJhbnNmZXItcmVhZFwiLFwic2NoZWR1bGVkLXJlYWRcIixcImhpc3RvcnktcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcGF5bWVudC1ydW5zLXJlYWRcIixcImFsbC1jYXJkcy1yZWFkXCIsXCJteS1jYXJkcy1yZWFkXCIsXCJ2aXJ0dWFsLWNhcmRzLWNyZWF0ZVwiLFwidmlydHVhbC1jYXJkcy1yZWFkXCIsXCJ2aXJ0dWFsLWNhcmRzLXVwZGF0ZVwiLFwidmlydHVhbC1jYXJkcy1kZWxldGVcIixcInBoeXNpY2FsLWNhcmRzLWNyZWF0ZVwiLFwicGh5c2ljYWwtY2FyZHMtcmVhZFwiLFwicGh5c2ljYWwtY2FyZHMtdXBkYXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1kZWxldGVcIixcImNhcmQtbGltaXQtdXBkYXRlXCIsXCJjYXJkLW5pY2tuYW1lLXVwZGF0ZVwiLFwiY2FuY2VsLWNhcmQtdXBkYXRlXCIsXCJmcmVlemUtY2FyZC11cGRhdGVcIixcInVuZnJlZXplLWNhcmQtdXBkYXRlXCIsXCJjYXJkLXN0YXR1cy11cGRhdGVcIixcImNhcmQtZG93bmxvYWRzLWltcG9ydFwiLFwidXNlcnMtY3JlYXRlXCIsXCJ1c2Vycy1yZWFkXCIsXCJ1c2Vycy11cGRhdGVcIixcInVzZXJzLWRlbGV0ZVwiLFwiaW52aXRhdGlvbi1saW5rLXNlbmRcIixcImhlYWx0aC1jaGVjay1yZWFkXCIsXCJub3RpZmljYXRpb25zLXJlYWRcIixcIm9yZ2FuaXphdGlvbi1yZWFkXCIsXCJvcmdhbml6YXRpb24tbW9kdWxyLWFjY291bnQtcmVhZFwiLFwidHJhbnNhY3Rpb25zLWNyZWF0ZVwiLFwidHJhbnNhY3Rpb25zLXJlYWRcIixcInRyYW5zYWN0aW9ucy11cGRhdGVcIixcInRyYW5zYWN0aW9ucy1kZWxldGVcIixcInVzZXItdHJhbnNhY3Rpb25zLXJlYWRcIixcIm9yZ2FuaXphdGlvbi10cmFuc2FjdGlvbnMtcmVhZFwiLFwiY3VzdG9tZXItY3JlYXRlXCIsXCJjb21wYW55LXJlYWRcIixcIm9yZ2FuaXphdGlvbi1hbmFseXRpY3MtcmVhZFwiLFwidXNlci1hbmFseXRpY3MtcmVhZFwiLFwiY2FyZC1yZXF1ZXN0cy1yZWFkXCIsXCJjYXJkLXJlcXVlc3RzLXVwZGF0ZVwiLFwiY2FyZC1yZXF1ZXN0cy1kZWxldGVcIixcImNhcmQtZXhwZW5zZXMtY3JlYXRlXCIsXCJjYXJkLWV4cGVuc2VzLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtdXBkYXRlXCIsXCJjYXJkLWV4cGVuc2VzLWRlbGV0ZVwiLFwidGVhbXMtY3JlYXRlXCIsXCJ0ZWFtcy1yZWFkXCIsXCJ0ZWFtcy11cGRhdGVcIixcInRlYW1zLWRlbGV0ZVwiLFwiY29uZmlndXJhdGlvbnMtcG8tcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1jZS1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3Jpc2F0aW9uLWFwLXJlYWRcIixcInBheWVlLWNvbnRhY3Qtbm8tcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1wby1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMS1leHBvcnRcIixcInhlcm8tYW5hbHlzaXMtcmVhZFwiLFwia2xvby1zcGVuZC1yZWFkXCIsXCJpc3N1ZS1jYXJkLWNyZWF0ZVwiLFwiYWN0aXZhdGUtcGh5c2ljYWwtY2FyZC11cGRhdGVcIixcImFuYWx5dGljcy1kYXNoYm9hcmQtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMS1pbXBvcnRcIixcImRhc2hib2FyZC1pbS1yZWFkXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItY3JlYXRlXCIsXCJjaGFyZ2ViZWUtc3Vic2NyaXB0aW9uLXJlYWRcIixcImNoYXJnZWJlZS1jdXN0b21lci1iaWxsLXJlYWRcIixcImNoYXJnZWJlZS1pbnZvaWNlLXJlYWRcIixcImNoYXJnZWJlZS1vcmdhbml6YXRpb24tc3Vic2NyaXB0aW9ucy1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXJlYWRcIixcImFwLWludm9pY2UtY3JlYXRlXCIsXCJhcC1pbnZvaWNlLXJlYWRcIixcImFwLWludm9pY2UtdXBkYXRlXCIsXCJzZXR0aW5nLXJlYWRcIixcIm5ldy1wYXllZS1jb250YWN0LXJlYWRcIixcImNvbmZpZ3VyYXRpb25zLWF1dG9tYXRpYy1lbWFpbC1wby1yZWFkXCIsXCJzY2hlZHVsZS1wYXltZW50LWJ1dHRvbi1yZWFkXCIsXCJvcmdhbml6YXRpb24tY3JlYXRlXCIsXCJvcmdhbml6YXRpb24tdXBkYXRlXCIsXCJvcmdhbml6YXRpb24tZGVsZXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMy1jcmVhdGVcIixcInJvbGVzLXJlYWRcIixcInJvbGVzLXVwZGF0ZVwiLFwicm9sZXMtZGVsZXRlXCIsXCJ0aHJlc2hvbGQtcmVhZFwiLFwicHVyY2hhc2Utb3JkZXItY3JlYXRlXCIsXCJwdXJjaGFzZS1vcmRlci1yZWFkXCIsXCJwdXJjaGFzZS1vcmRlci11cGRhdGVcIixcInBheWVlLW1hbmFnZW1lbnQtcmVhZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXJlYWRcIixcImNhcmQtZXhwZW5zZXMtdXBkYXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMy1yZWFkXCIsXCJwcm9maWxlLXJlYWRcIixcInByb2ZpbGUtdXBkYXRlXCIsXCJpbnZvaWNlLW1hdGNoaW5nLXBvLXJlYWRcIixcImludm9pY2UtbWF0Y2hpbmctaW0tcmVhZFwiXSxcInJvbGVcIjp7XCJpZFwiOlwiNWE3Y2NjOTItZWEzMC00ODM0LTg1OTQtNTEzMmI4MjU2NjA3XCIsXCJuYW1lXCI6XCJPcmdhbmlzYXRpb24gQWRtaW5cIn19In0.jTQIg3-GGE-tkTPmtVzFf__30nO9pN7fR4wnkK6k6zhYxpWEqg-L0GbBDdJ2aQIpo0mJVRFCDKYOyDQa7qu5F3GXndr9BG_bFwg5ZyuOOx779fffQoUXz8oSlQiNtY_rmP9SnmDpkiOR1mhljXUXPzmTe7w-ih8p9wS0QvRhuGlNZEB38Z1ybgFkopAUxDWJ6slhe2LxIRRvNB0OLqPePa-bmFPzBugMEyn11VQhYK2hhdL13RyHwTYzz-uFSj4-bmqMYGco-aDJ4S45xYa6QvGykRQoBI3_F8ogMZApxq4XF37Cxd0n5J-QfviWQ6owjn0cKr1Cf8ql_RGGP0D0EFrzdEKYOkyZW9eOsquzCi2DmdfkRTjyAdgz-qdozwQ4BTfSA-wVYz8_7dIEYDZudvaKmQnIe5ZX1KU0at-VcK26r-ebB3WzNCF8IsIajCNb6uzrMFw801VKNgaiCgJFPur-DwFaY3fhW3kzlLtIjeAgMl5BgZMIsobsQ4lUGtQfV-8skI6PelGM0qqD9CTZ7fh3PK1BPBA_a72_UIyRDzQtGU-s0UvCx_96B-4g1-db6nWoWP9Jl4oSvaHApJcye3w_fPHAIo2yQPO04xnTX0C3mxGotVJSaRJLd5izEqw1caPhX7y3Y9ToiIo5fQ620l3ITHR9J4iThtprxnn0_OE"
        # header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.get(
                pending_url,
                headers={"Authorization": f"Bearer {auth_token}"},
                # headers=header,
            )
            api_log(msg=f"LARAVEL API response::: {pending_invoice_response}")
            if pending_invoice_response.status_code == status.HTTP_200_OK:
                api_payload = pending_invoice_response.json()
                self.formatted_payload = api_payload["result"]
                if isinstance(self.formatted_payload, list):
                    if not self.formatted_payload:
                        api_log(msg="There is no invoice payload in the API")
                    else:
                        api_log(msg=f"formatted_paylaod in CRON Invoice:: {self.formatted_payload}")
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
        from INVOICES.models import CronRetry
        kloo_invoice_ids = CronRetry.objects.values_list('kloo_invoice_id', flat=True)
        kloo_invoice_ids_list = list(kloo_invoice_ids)

        invoices = []
        pattern = r"'problem_type': '([^']+)'"

        for invoice_payload in payload:
            if invoice_payload['model']['kloo_invoice_id'] not in kloo_invoice_ids_list:
                response = self.create_invoice(invoice_payload)
                api_log(msg=f"response_str:: {str(response)}")
                api_log(msg=f"Original response:: {response}")

                # Extract the status code using regex
                status_code_match = re.search(r'status_code:\s*(\d+)', str(response))
                status_code = int(status_code_match.group(1)) if status_code_match else None
                api_log(msg=f"STATUS CODE in PROCESS INVOICE:::: {status_code}")

                if status_code:
                    if status_code in [404, 400]:
                        api_log(
                            msg=f"Error creating invoice: status_code: {status_code}, body: {response}")

                        invoice_id = invoice_payload['model']['kloo_invoice_id']
                        api_log(msg=f"invoice ID after retry failed:: {invoice_id}")

                        # Extract problem_type using regex
                        match = re.search(pattern, response['error'])
                        if match:
                            problem_type = match.group(1)
                            api_log(msg=f"problem_type:: {problem_type}")
                        else:
                            problem_type = None
                            api_log(msg=f"problem_type not found")

                        # Determine status based on the extracted problem_type
                        if problem_type in ['RATE_LIMITED', 'TIMED_OUT', "MISSING_PERMISSION"]:
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
                        api_log(msg=f"update_invoice_id: {update_invoice_id}")
                        new_invoice_id = "".join(update_invoice_id.split("-"))
                        api_log(msg=f"new_invoice_id: {new_invoice_id}")
                        log = InvoiceAttachmentLogs.objects.filter(invoice_id=new_invoice_id).first()
                        if log:
                            log.problem_type = invoice_payload['model']['problem_type']
                            log.save()
                        api_log(msg=f"log prob type::: {log.problem_type}")
                        self.handle_invoice_response(invoice_payload)

        # Log or return the invoices JSON
        final_update = {"invoices": invoices}
        api_log(msg=f"final_update JSON: {final_update}")
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
        from INVOICES.models import CronRetry
        retry_at = datetime.now() + retry_delay
        kloo_invoice_id = invoice_payload['model']['kloo_invoice_id']
        # problem_type = invoice_payload['model']['problem_type']
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
                        # if success, then  check for the status code in response and delete the row from table.
                        # elif self.handle_invoice_response(invoice_payload)( already done below)
                        # else(failure then delete in DB)
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

    def post_response(self, response: list):
        from merge_integration.settings import GETKLOO_LOCAL_URL
        pending_url = f"{GETKLOO_LOCAL_URL}/ap/erp-integration/update_accounting_portal_status"
        # auth_token = ""
        header = {'Content-type': 'application/json'}
        try:
            pending_invoice_response = requests.post(
                pending_url,
                # headers={"Authorization": f"Bearer {auth_token}"},
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

