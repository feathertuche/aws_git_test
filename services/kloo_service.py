"""
Kloo Service class to connect with kloo API
"""

import json

import requests

from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_LOCAL_URL


class KlooException(Exception):
    """
    KlooException class
    """

    pass


class KlooService:
    """
    KlooService class
    """

    def __init__(self, auth_token: str = None, erp_link_token_id: str = None):
        self.auth_token = auth_token
        self.erp_link_token_id = str(erp_link_token_id)
        self.KLOO_URL = GETKLOO_LOCAL_URL
        self.headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {self.auth_token}",
        }

    def handle_kloo_api_error(
        self, function: str, exception: KlooException | Exception
    ):
        """
        Handle kloo api error
        """
        api_log(msg=f"API KLOO Error in {function} : {str(exception)}")
        return {"status": False, "error": str(exception), "status_code": 500}

    def post_contacts_data(self, contacts_formatted_payload: dict):
        """
        Post contacts data to kloo API
        """
        try:
            api_log(
                msg=f"Posting Contacts data to Kloo: {json.dumps(contacts_formatted_payload)}"
            )

            contact_url = f"{self.KLOO_URL}/ap/erp-integration/insert-erp-contacts"
            contact_response_data = requests.post(
                contact_url,
                json=contacts_formatted_payload,
                headers=self.headers,
            )

            if contact_response_data.status_code != 201:
                raise KlooException(
                    f"Error in posting contacts data: {contact_response_data.json()}"
                )
            # success_message = f"success message: posting contacts data to laravel: {contact_response_data.json()}"
            # send_slack_notification(success_message)
            return {
                "status": True,
                "data": contact_response_data.json(),
                "status_code": contact_response_data.status_code,
            }

        except (KlooException, Exception) as e:
            # error_message = (f"Error in posting contacts data: {contact_response_data.json() : {e}}")
            # send_slack_notification(error_message)
            return self.handle_kloo_api_error("post_contacts_data", e)

    def post_tracking_categories_data(
        self, tracking_categories_formatted_payload: dict
    ):
        """
        Post tracking categories data to kloo API
        """
        try:
            api_log(
                msg=f"Posting Tracking Categories data to Kloo: {json.dumps(tracking_categories_formatted_payload)}"
            )

            tc_url = f"{self.KLOO_URL}/organizations/erp-tracking-categories"
            tc_response_data = requests.post(
                tc_url,
                json=tracking_categories_formatted_payload,
                headers=self.headers,
            )

            if tc_response_data.status_code != 201:
                raise KlooException(
                    f"Error in posting tracking categories data: {tc_response_data.json()}"
                )

            return {
                "status": True,
                "data": tc_response_data.json(),
                "status_code": tc_response_data.status_code,
            }

        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_tracking_categories_data", e)

    def post_invoice_data(self, invoice_formatted_payload: dict):
        """
        Post invoice data to kloo API
        """
        try:
            api_log(
                msg=f"Posting invoice data to Kloo: {json.dumps(invoice_formatted_payload)}"
            )

            invoice_url = f"{self.KLOO_URL}/ap/erp-integration/insert-erp-invoices"
            invoice_response_data = requests.post(
                invoice_url, json=invoice_formatted_payload, headers=self.headers
            )

            if invoice_response_data.status_code != 201:
                api_log(
                    msg=f"Error in posting invoice data: {invoice_response_data.json()}"
                )
                raise KlooException

            return {
                "status": True,
                "data": invoice_response_data.json(),
                "status_code": invoice_response_data.status_code,
            }

        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_invoice_data", e)

    def sync_complete_mail(self, sync_complete_payload: dict):
        """
        Post sync complete mail to kloo API
        """
        try:
            api_log(msg=f"MAIL: Sync Complete Payload: {sync_complete_payload}")
            daily_sync_id = sync_complete_payload["daily_sync_id"]

            sync_url = f"{self.KLOO_URL}/ap/erp-integration/erp-sync-email"
            sync_response_data = requests.get(sync_url, params={"id": daily_sync_id})

            if sync_response_data.status_code != 200:
                raise KlooException(
                    f"Error in posting sync complete mail: {sync_response_data.json()}"
                )

            return {
                "status": True,
                "data": sync_response_data.json(),
                "status_code": sync_response_data.status_code,
            }

        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_sync_complete_mail", e)
