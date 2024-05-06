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

    def handle_kloo_api_error(
        self, function: str, exception: KlooException | Exception
    ):
        """
        Handle kloo api error
        """
        api_log(msg=f"API KLOO Error in {function} : {str(exception)}")
        return {"status": False, "error": str(exception), "status_code": 500}

    def post_account_data(self, account_payload: dict):
        """
        Post account data to kloo API
        """
        try:
            field_list = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {},
                }
            ]

            accounts_list = []
            for account in account_payload:
                account_dict = {
                    "id": account.id,
                    "remote_id": account.remote_id,
                    "name": account.name,
                    "description": account.description,
                    "classification": account.classification,
                    "type": account.type,
                    "status": account.status,
                    "current_balance": account.current_balance,
                    "currency": account.currency,
                    "account_number": account.account_number,
                    "parent_account": account.parent_account,
                    "company": account.company,
                    "remote_was_deleted": account.remote_was_deleted,
                    "created_at": account.created_at.isoformat() + "Z",
                    "modified_at": account.modified_at.isoformat() + "Z",
                    "field_mappings": field_list,
                    "remote_data": account.remote_data,
                }
                accounts_list.append(account_dict)
            accounts_formatted_data = {"accounts": accounts_list}

            post_account_payload = accounts_formatted_data
            post_account_payload["erp_link_token_id"] = self.erp_link_token_id
            account_url = f"{self.KLOO_URL}/organizations/insert-erp-accounts"
            account_response_data = requests.post(
                account_url,
                json=post_account_payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )

            if account_response_data.status_code != 201:
                raise KlooException(
                    f"Error in posting account data: {account_response_data.json()}"
                )

            return {
                "status": True,
                "data": account_response_data.json(),
                "status_code": account_response_data.status_code,
            }
        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_account_data", e)

    def post_contacts_data(self, contacts_formatted_payload: dict):
        """
        Post contacts data to kloo API
        """
        try:
            contact_url = f"{self.KLOO_URL}/ap/erp-integration/insert-erp-contacts"
            contact_response_data = requests.post(
                contact_url,
                json=contacts_formatted_payload,
                # headers={"Authorization": f"Bearer {self.auth_token}"},
            )

            if contact_response_data.status_code != 201:
                raise KlooException(
                    f"Error in posting contacts data: {contact_response_data.json()}"
                )

            return {
                "status": True,
                "data": contact_response_data.json(),
                "status_code": contact_response_data.status_code,
            }

        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_contacts_data", e)

    def post_company_info_data(self, company_info_payload: dict):
        """
        Post company info data to kloo API
        """
        try:
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
                    "created_at": addr.created_at.isoformat() + "Z",
                    "modified_at": addr.modified_at.isoformat() + "Z",
                }
                for addr in company_info_payload.results[0].addresses
            ]

            formatted_data = []
            for organization in company_info_payload:
                formatted_entry = {
                    "id": organization.id,
                    "remote_id": organization.remote_id,
                    "name": organization.name,
                    "legal_name": organization.legal_name,
                    "tax_number": organization.tax_number,
                    "fiscal_year_end_month": organization.fiscal_year_end_month,
                    "fiscal_year_end_day": organization.fiscal_year_end_day,
                    "currency": organization.currency,
                    "remote_created_at": organization.remote_created_at.isoformat()
                    + "Z",
                    "urls": organization.urls,
                    "addresses": formatted_addresses,
                    "phone_numbers": [
                        {
                            "number": phone.number,
                            "type": phone.type,
                            "created_at": organization.created_at.isoformat() + "Z",
                            "modified_at": organization.modified_at.isoformat() + "Z",
                        }
                        for phone in organization.phone_numbers
                    ],
                    "remote_was_deleted": organization.remote_was_deleted,
                    "created_at": organization.created_at.isoformat() + "Z",
                    "modified_at": organization.modified_at.isoformat() + "Z",
                    "field_mappings": organization.field_mappings,
                    "remote_data": organization.remote_data,
                }
                formatted_data.append(formatted_entry)

            kloo_format_json = {"companies": formatted_data}

            merge_payload = kloo_format_json
            merge_payload["erp_link_token_id"] = self.erp_link_token_id
            kloo_url = f"{self.KLOO_URL}/organizations/insert-erp-companies"
            kloo_data_insert = requests.post(
                kloo_url,
                json=merge_payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )

            if kloo_data_insert.status_code != 201:
                raise KlooException(
                    f"Error in posting company info data: {kloo_data_insert.json()}"
                )

            return {
                "status": True,
                "data": kloo_data_insert.json(),
                "status_code": kloo_data_insert.status_code,
            }

        except (KlooException, Exception) as e:
            return self.handle_kloo_api_error("post_company_info_data", e)

    def post_tracking_categories_data(self, tracking_categories_payload: dict):
        """
        Post tracking categories data to kloo API
        """
        try:
            field_mappings = [
                {
                    "organization_defined_targets": {},
                    "linked_account_defined_targets": {},
                }
            ]

            formatted_data = []
            for category in tracking_categories_payload:
                formatted_entry = {
                    "id": category.id,
                    "name": category.name,
                    "status": category.status,
                    "category_type": category.category_type,
                    "parent_category": category.parent_category,
                    "company": category.company,
                    "remote_was_deleted": category.remote_was_deleted,
                    "remote_id": category.remote_id,
                    "created_at": category.created_at.isoformat() + "Z",
                    "updated_at": category.modified_at.isoformat() + "Z",
                    "field_mappings": field_mappings,
                    "remote_data": category.remote_data,
                }
                formatted_data.append(formatted_entry)

            kloo_format_json = {"tracking_category": formatted_data}

            tc_payload = kloo_format_json

            tc_payload["erp_link_token_id"] = self.erp_link_token_id

            tc_url = f"{self.KLOO_URL}/organizations/erp-tracking-categories"
            tc_response_data = requests.post(
                tc_url,
                json=tc_payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
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

    def post_invoice_data(self, invoice_payload: list):
        """
        Post invoice data to kloo API
        """
        try:
            kloo_format_json = {"invoices": invoice_payload}

            api_log(
                msg=f"Total Invoices posting to kloo: {len(kloo_format_json['invoices'])} "
            )

            post_invoice_payload = kloo_format_json
            post_invoice_payload["erp_link_token_id"] = str(self.erp_link_token_id)

            api_log(
                msg=f"Posting invoice data to Kloo: {json.dumps(post_invoice_payload)}"
            )

            invoice_url = f"{self.KLOO_URL}/ap/erp-integration/insert-erp-invoices"
            invoice_response_data = requests.post(
                invoice_url,
                json=post_invoice_payload,
                stream=True,
                # headers={"Authorization": f"Bearer {self.auth_token}"},
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
