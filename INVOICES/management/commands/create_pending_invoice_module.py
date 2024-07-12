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
        auth_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NmQyZDIwMS1hMDNjLTQ1NjUtOTA2NC1kOWRmOTEzOWVhZjAiLCJqdGkiOiIzYWRiZmIxNWQ3YWRlNWUzNzRjZTliZWE5YmViM2M4MzBiOTNhMWUyM2FhODAyMGZmODQzOWM5N2RmYTc3ODhlOGRhODI5YzM1ZGM3YjRjOCIsImlhdCI6MTcyMDc2NTgwNC42MjcxMiwibmJmIjoxNzIwNzY1ODA0LjYyNzEyMSwiZXhwIjoxNzIwNzY2MTA0LjYxOTI2OCwic3ViIjoiIiwic2NvcGVzIjpbIioiXSwiY3VzdG9tX2NsYWltIjoie1widXNlclwiOntcImlkXCI6XCI4MGIwZWNmOS0yMTcxLTRjMzAtYTYxMi04Nzg2NDUxM2ViMDVcIixcImZpcnN0X25hbWVcIjpcImFtaXRlc2hcIixcIm1pZGRsZV9uYW1lXCI6bnVsbCxcImxhc3RfbmFtZVwiOlwic2FoYXlcIixcImVtYWlsXCI6XCJhbWl0ZXNoLnNhaGF5QGdldGtsb28uY29tXCIsXCJiaXJ0aF9kYXRlXCI6XCIxOTg0LTEyLTMxXCIsXCJ1c2VyX2NyZWF0ZWRfYnlcIjpudWxsLFwibG9naW5fYXR0ZW1wdHNcIjowLFwic3RhdHVzXCI6XCJ1bmJsb2NrZWRcIixcImNyZWF0ZWRfYXRcIjpcIjIwMjMtMTAtMDVUMTE6MDg6MDEuMDAwMDAwWlwiLFwidXBkYXRlZF9hdFwiOlwiMjAyNC0wMi0yMlQwNTo0ODo1MC4wMDAwMDBaXCIsXCJ1c2VyX29yZ19pZFwiOlwiODI4ZTVmMWQtMDJjMC00MDNkLTg2MjAtOWVmMDAwYWRkM2FhXCIsXCJvcmdhbml6YXRpb25faWRcIjpcIjQ1Nzg5M2IzLTliNGEtNDA0NS04NmFkLTY5N2ZmZjdiMzFmOVwiLFwib3JnYW5pemF0aW9uX25hbWVcIjpcIkRldiBJbnRlZ3JhdGlvblwifSxcInNjb3Blc1wiOltcImludm9pY2UtbWF0Y2hpbmctcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1kb3dubG9hZC1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLW1hcmstZm9yLXJldmlldy11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtbWFyay1hcy1hcHByb3ZlZC11cGRhdGVcIixcImNhcmQtZXhwZW5zZXMtc2F2ZS1hcy1kcmFmdC11cGRhdGVcIixcInBheW1lbnQtcnVucy1jcmVhdGVcIixcInBheW1lbnQtcnVucy1yZWFkXCIsXCJwYXltZW50LXJ1bnMtdXBkYXRlXCIsXCJwYXltZW50LXJ1bnMtZGVsZXRlXCIsXCJzdWJzY3JpcHRpb24tY3JlYXRlXCIsXCJzdWJzY3JpcHRpb24tcmVhZFwiLFwic3Vic2NyaXB0aW9uLXVwZGF0ZVwiLFwic3Vic2NyaXB0aW9uLWRlbGV0ZVwiLFwidGVzdC1tb2R1bGUtYTEtY3JlYXRlXCIsXCJ0ZXN0LW1vZHVsZS1hMS1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMS11cGRhdGVcIixcInRlc3QtbW9kdWxlLWExLWRlbGV0ZVwiLFwiaW52b2ljZS1wby1tYXRjaGluZy1yZWFkXCIsXCJkYXNoYm9hcmQtY2FyZC1hbmQtY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1jYXJkcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1yZWFkXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1wdXJjaGFzZS1vcmRlcnMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtaGlzdG9yeS1yZWFkXCIsXCJzZXR0aW5nLXBheWVlLW1hbmFnZW1lbnQtcmVhZFwiLFwidXBkYXRlLXBlcm1pc3Npb24tcmV0b29sLXRlc3QtY3JlYXRlXCIsXCJ1cGRhdGUtcGVybWlzc2lvbi1yZXRvb2wtdGVzdC1yZWFkXCIsXCJkYXNoYm9hcmQtcG8tcmVhZFwiLFwicGF5ZWUtbWFuYWdlbWVudC1yZWFkXCIsXCJwYXktdmlhLXlhcGlseS1yZWFkXCIsXCJzY2hlZHVsZS10YWItcmVhZFwiLFwidXBkYXRlLXBlcm1pc3Npb24tcmV0b29sLXRlc3QtdXBkYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtY3JlYXRlXCIsXCJzZXR0aW5nLWV4cGVuc2UtZmllbGQtcmVhZFwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLXVwZGF0ZVwiLFwic2V0dGluZy1leHBlbnNlLWZpZWxkLWRlbGV0ZVwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS1jcmVhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtcmVhZFwiLFwic2V0dGluZy1jdXN0b20tZXhwZW5zZS11cGRhdGVcIixcInNldHRpbmctY3VzdG9tLWV4cGVuc2UtZGVsZXRlXCIsXCJwYXltZW50LXJ1bnMtcmVhZFwiLFwic2V0dGluZy1uZXctcGF5ZWUtY29udGFjdC1yZWFkXCIsXCJ0ZXN0LW1vZHVsZS1hMi1jcmVhdGVcIixcInRlc3QtbW9kdWxlLWEyLXJlYWRcIixcInRlc3QtbW9kdWxlLWEyLXVwZGF0ZVwiLFwidGVzdC1tb2R1bGUtYTItZGVsZXRlXCIsXCJzZXR0aW5nLXNtYXJ0LWFwcHJvdmFscy1pbnZvaWNlcy1zY2hlZHVsZS1yZWFkXCIsXCJwYXktbm93LWJ1dHRvbi1yZWFkXCIsXCJzZXR0aW5nLWludGVncmF0aW9ucy1yZWFkXCIsXCJzZXR0aW5nLWNhdGVnb3JpZXMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtcmVhZFwiLFwic2V0dGluZy1hZGRyZXNzLXJlYWRcIixcImRhc2hib2FyZC1yZWFkXCIsXCJhcHByb3ZhbHMtcmVhZFwiLFwic2V0dGluZy1zbWFydC1hcHByb3ZhbHMtc3VwcGxpZXItcmVhZFwiLFwiYWNjb3VudC1kZXRhaWxzLXJlYWRcIixcImRlYml0LWFjY291bnQtY3JlYXRlXCIsXCJkZWJpdC1hY2NvdW50LXJlYWRcIixcImRlYml0LWFjY291bnQtdXBkYXRlXCIsXCJkZWJpdC1hY2NvdW50LWRlbGV0ZVwiLFwic3RhbmRpbmctb3JkZXItY3JlYXRlXCIsXCJzdGFuZGluZy1vcmRlci1yZWFkXCIsXCJpbW1lZGlhdGUtcGF5bWVudC1jcmVhdGVcIixcImltbWVkaWF0ZS1wYXltZW50LXJlYWRcIixcImJhbmstdHJhbnNmZXItY3JlYXRlXCIsXCJiYW5rLXRyYW5zZmVyLXJlYWRcIixcInNjaGVkdWxlZC1yZWFkXCIsXCJoaXN0b3J5LXJlYWRcIixcInNldHRpbmctc21hcnQtYXBwcm92YWxzLXBheW1lbnQtcnVucy1yZWFkXCIsXCJhbGwtY2FyZHMtcmVhZFwiLFwibXktY2FyZHMtcmVhZFwiLFwidmlydHVhbC1jYXJkcy1jcmVhdGVcIixcInZpcnR1YWwtY2FyZHMtcmVhZFwiLFwidmlydHVhbC1jYXJkcy11cGRhdGVcIixcInZpcnR1YWwtY2FyZHMtZGVsZXRlXCIsXCJwaHlzaWNhbC1jYXJkcy1jcmVhdGVcIixcInBoeXNpY2FsLWNhcmRzLXJlYWRcIixcInBoeXNpY2FsLWNhcmRzLXVwZGF0ZVwiLFwicGh5c2ljYWwtY2FyZHMtZGVsZXRlXCIsXCJjYXJkLWxpbWl0LXVwZGF0ZVwiLFwiY2FyZC1uaWNrbmFtZS11cGRhdGVcIixcImNhbmNlbC1jYXJkLXVwZGF0ZVwiLFwiZnJlZXplLWNhcmQtdXBkYXRlXCIsXCJ1bmZyZWV6ZS1jYXJkLXVwZGF0ZVwiLFwiY2FyZC1zdGF0dXMtdXBkYXRlXCIsXCJjYXJkLWRvd25sb2Fkcy1pbXBvcnRcIixcInVzZXJzLWNyZWF0ZVwiLFwidXNlcnMtcmVhZFwiLFwidXNlcnMtdXBkYXRlXCIsXCJ1c2Vycy1kZWxldGVcIixcImludml0YXRpb24tbGluay1zZW5kXCIsXCJoZWFsdGgtY2hlY2stcmVhZFwiLFwibm90aWZpY2F0aW9ucy1yZWFkXCIsXCJvcmdhbml6YXRpb24tcmVhZFwiLFwib3JnYW5pemF0aW9uLW1vZHVsci1hY2NvdW50LXJlYWRcIixcInRyYW5zYWN0aW9ucy1jcmVhdGVcIixcInRyYW5zYWN0aW9ucy1yZWFkXCIsXCJ0cmFuc2FjdGlvbnMtdXBkYXRlXCIsXCJ0cmFuc2FjdGlvbnMtZGVsZXRlXCIsXCJ1c2VyLXRyYW5zYWN0aW9ucy1yZWFkXCIsXCJvcmdhbml6YXRpb24tdHJhbnNhY3Rpb25zLXJlYWRcIixcImN1c3RvbWVyLWNyZWF0ZVwiLFwiY29tcGFueS1yZWFkXCIsXCJvcmdhbml6YXRpb24tYW5hbHl0aWNzLXJlYWRcIixcInVzZXItYW5hbHl0aWNzLXJlYWRcIixcImNhcmQtcmVxdWVzdHMtcmVhZFwiLFwiY2FyZC1yZXF1ZXN0cy11cGRhdGVcIixcImNhcmQtcmVxdWVzdHMtZGVsZXRlXCIsXCJjYXJkLWV4cGVuc2VzLWNyZWF0ZVwiLFwiY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXVwZGF0ZVwiLFwiY2FyZC1leHBlbnNlcy1kZWxldGVcIixcInRlYW1zLWNyZWF0ZVwiLFwidGVhbXMtcmVhZFwiLFwidGVhbXMtdXBkYXRlXCIsXCJ0ZWFtcy1kZWxldGVcIixcImNvbmZpZ3VyYXRpb25zLXBvLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tY2UtcmVhZFwiLFwic2V0dGluZy1jYXRlZ29yaXNhdGlvbi1hcC1yZWFkXCIsXCJwYXllZS1jb250YWN0LW5vLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcG8tcmVhZFwiLFwidGVzdC1tb2R1bGUtYTEtZXhwb3J0XCIsXCJ4ZXJvLWFuYWx5c2lzLXJlYWRcIixcImtsb28tc3BlbmQtcmVhZFwiLFwiaXNzdWUtY2FyZC1jcmVhdGVcIixcImFjdGl2YXRlLXBoeXNpY2FsLWNhcmQtdXBkYXRlXCIsXCJhbmFseXRpY3MtZGFzaGJvYXJkLXJlYWRcIixcInNldHRpbmctY2F0ZWdvcmlzYXRpb24tcmVhZFwiLFwidGVzdC1tb2R1bGUtYTEtaW1wb3J0XCIsXCJkYXNoYm9hcmQtaW0tcmVhZFwiLFwiY2hhcmdlYmVlLWN1c3RvbWVyLWNyZWF0ZVwiLFwiY2hhcmdlYmVlLXN1YnNjcmlwdGlvbi1yZWFkXCIsXCJjaGFyZ2ViZWUtY3VzdG9tZXItYmlsbC1yZWFkXCIsXCJjaGFyZ2ViZWUtaW52b2ljZS1yZWFkXCIsXCJjaGFyZ2ViZWUtb3JnYW5pemF0aW9uLXN1YnNjcmlwdGlvbnMtcmVhZFwiLFwiY2hhcmdlYmVlLW9yZ2FuaXphdGlvbi1yZWFkXCIsXCJhcC1pbnZvaWNlLWNyZWF0ZVwiLFwiYXAtaW52b2ljZS1yZWFkXCIsXCJhcC1pbnZvaWNlLXVwZGF0ZVwiLFwic2V0dGluZy1yZWFkXCIsXCJuZXctcGF5ZWUtY29udGFjdC1yZWFkXCIsXCJjb25maWd1cmF0aW9ucy1hdXRvbWF0aWMtZW1haWwtcG8tcmVhZFwiLFwic2NoZWR1bGUtcGF5bWVudC1idXR0b24tcmVhZFwiLFwib3JnYW5pemF0aW9uLWNyZWF0ZVwiLFwib3JnYW5pemF0aW9uLXVwZGF0ZVwiLFwib3JnYW5pemF0aW9uLWRlbGV0ZVwiLFwidGVzdC1tb2R1bGUtYTMtY3JlYXRlXCIsXCJyb2xlcy1yZWFkXCIsXCJyb2xlcy11cGRhdGVcIixcInJvbGVzLWRlbGV0ZVwiLFwidGhyZXNob2xkLXJlYWRcIixcInB1cmNoYXNlLW9yZGVyLWNyZWF0ZVwiLFwicHVyY2hhc2Utb3JkZXItcmVhZFwiLFwicHVyY2hhc2Utb3JkZXItdXBkYXRlXCIsXCJwYXllZS1tYW5hZ2VtZW50LXJlYWQtcmVhZFwiLFwiY2FyZC1leHBlbnNlcy1yZWFkXCIsXCJjYXJkLWV4cGVuc2VzLXVwZGF0ZVwiLFwidGVzdC1tb2R1bGUtYTMtcmVhZFwiLFwicHJvZmlsZS1yZWFkXCIsXCJwcm9maWxlLXVwZGF0ZVwiLFwiaW52b2ljZS1tYXRjaGluZy1wby1yZWFkXCIsXCJpbnZvaWNlLW1hdGNoaW5nLWltLXJlYWRcIl0sXCJyb2xlXCI6e1wiaWRcIjpcIjZiMjY4NGNjLTIyMzEtMTFlZS05ZGVmLTBhMWMyMmFjMmZhNlwiLFwibmFtZVwiOlwiT3JnYW5pc2F0aW9uIEFkbWluXCJ9fSJ9.J7a14_3N-zloY6_WukCX9NgHoOSaV5lf3dWdlKQcqX-721ODgQhILHeS0jEx_o_dKmSbX08m_wVjy86Z-v5tzQ-e5qepbQIv2WoTQEXHAgQooIxnS35w-TyneitW_9sglbTPmCuxmVTFJKfSVnTMS3Io-NKTMvC-2axrW351okf_4mwDijUReAr9TK4hb2O_aYDulCPpz46W_iBIqrS1M0tVwhc26sGi7UmI49S2Sg6kQX_LN5rjstI0MogvfjdSVMDQi2ya5FWbPETEUetdvVx5_Nl0n8i4K44Lw7aJVKT8rG6YlVNz01vSigkOVoVkO6gIgIwF_24QJmuvilOaXpO-lpw9VD1QsnBMP9ud91cDhsYkUM5Zo59GAfWKIxEIv69453MmmKV9y2u_ldaIbubnSXWYww9B-5S9Gh-2HCy8mWTT0cXYFs4UG0oBFTOtslJ5WCMMNmVchER_U0oHap9lTAZvAi2BXC5tc-Nc7XZTg30D5UfAteNI0_YatYGZWYBfLmdFy3f089Fx64Xd7FgyBr0aNayZtbscHFCiLu8vmW50lYclGEMHvwWAwrxDN_-sIw6qK_NUa804eYvu7lwKIretkKWuPHDXVDA1d89gNwKqN1mkabr7bDFN7qHoqGtMkDLaQ5YOVGGu-mQ_j9vnCluV8QlEoVRv_grGjlE"
        pending_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/pending_post_invoices_erp"

        try:
            pending_invoice_response = requests.get(
                pending_url,
                headers={"Authorization": f"Bearer {auth_token}"},
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

