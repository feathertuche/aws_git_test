import os
import uuid
import urllib.parse
import requests
from merge.core import ApiError
from rest_framework import status
from rest_framework.response import Response
from merge.resources.accounting import (
    AccountsListRequestRemoteFields,
    AccountsListRequestShowEnumOrigins,
    CompanyInfoListRequestExpand,
    ContactsListRequestExpand,
    InvoiceRequest,
    AccountingAttachmentRequest,
    InvoicesListRequestExpand,
)
from INVOICES.exceptions import MergeApiException
from INVOICES.models import InvoiceAttachmentLogs
from merge_integration.helper_functions import api_log
from merge_integration.settings import BASE_URL
from merge_integration.settings import invoices_page_size
from merge_integration.utils import create_merge_client


class MergeService:
    """
    MergeService class
    """

    def __init__(self, account_token: str):
        self.account_token = account_token
        self.merge_client = create_merge_client(account_token)

    def handle_merge_api_error(self, function: str, e: ApiError):
        """
        Handle merge api error
        """
        api_log(msg=f"API MERGE Error in {function} : {str(e)}")
        return {"status": False, "error": str(e)}


class MergeSyncService(MergeService):
    """
    MergeApiService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def sync_status(self):
        """
        Get sync status of all modules [TrackingCategory, CompanyInfo, Account, Contact]
        """
        try:
            sync_status = self.merge_client.accounting.sync_status.list()
            return {"status": True, "data": sync_status}
        except ApiError as e:
            return self.handle_merge_api_error("sync_status", e)

    def force_sync(self):
        """
        Force sync for a module
        """
        try:
            sync_status = (
                self.merge_client.accounting.force_resync.sync_status_resync_create()
            )

            return {"status": True, "data": sync_status}
        except ApiError as e:
            return self.handle_merge_api_error("force_sync", e)


class MergeAccountsService(MergeService):
    """
    MergeAccountsService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def get_accounts(self, modified_date: str = None):
        """
        Get accounts from merge
        """
        try:
            accounts_data = self.merge_client.accounting.accounts.list(
                expand="company",
                remote_fields=AccountsListRequestRemoteFields.CLASSIFICATION,
                show_enum_origins=AccountsListRequestShowEnumOrigins.CLASSIFICATION,
                page_size=100000,
                modified_after=modified_date,
            )

            return {
                "data": accounts_data,
                "status": True,
            }
        except ApiError as e:
            return self.handle_merge_api_error("get_accounts", e)


class MergeCompanyInfoService(MergeService):
    """
    MergeCompanyInfoService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def get_company_info(self, modified_date: str = None):
        """
        Get company info from merge
        """
        try:
            organization_data = self.merge_client.accounting.company_info.list(
                expand=CompanyInfoListRequestExpand.ADDRESSES,
                page_size=100000,
                include_remote_data=True,
                modified_after=modified_date,
            )
            return {"status": True, "data": organization_data}
        except ApiError as e:
            return self.handle_merge_api_error("get_company_info", e)


class MergeTrackingCategoriesService(MergeService):
    """
    MergeTrackingCategoriesService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def get_tracking_categories(self, modified_date: str = None):
        """
        Get tracking categories from merge
        """
        try:
            tracking_categories = self.merge_client.accounting.tracking_categories.list(
                expand="company",
                remote_fields="status",
                show_enum_origins="status",
                page_size=100000,
                modified_after=modified_date,
            )
            return {"status": True, "data": tracking_categories}
        except ApiError as e:
            return self.handle_merge_api_error("get_tracking_categories", e)


class MergeContactsService(MergeService):
    """
    MergeContactsService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def get_contacts(self, modified_date: str = None):
        """
        Get contacts from merge
        """
        try:
            contact_data = self.merge_client.accounting.contacts.list(
                expand=ContactsListRequestExpand.ADDRESSES,
                remote_fields="status",
                show_enum_origins="status",
                page_size=100000,
                modified_after=modified_date,
            )
            return {"status": True, "data": contact_data}
        except ApiError as e:
            return self.handle_merge_api_error("get_contacts", e)


class MergeInvoiceApiService(MergeService):
    """
    MergeApiService class
    """

    def __init__(self, account_token: str):
        super().__init__(account_token)

    def get_invoices(self, modified_after: str = None, batch_size: int = 100):
        """
        get_invoices method
        """
        try:
            invoice_data = self.merge_client.accounting.invoices.list(
                expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                page_size=invoices_page_size,
                include_remote_data=True,
                modified_after=modified_after,
            )

            all_company_info = []
            while True:
                api_log(msg=f"Adding {len(invoice_data.results)} Company Info to the list.")

                all_company_info.extend(invoice_data.results)

                if invoice_data.next is None:
                    break
                invoice_data = self.merge_client.accounting.invoices.list(
                    expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                    page_size=invoices_page_size,
                    include_remote_data=True,
                    modified_after=modified_after,
                    cursor=invoice_data.next,
                )

                api_log(
                    msg=f"Data coming for Company MERGE API is : {invoice_data}"
                )
                api_log(
                    msg=f"COMPANY INFO GET:: The length of the next page account data is : {len(invoice_data.results)}"
                )
                api_log(
                    msg=f"Length of all COMPANY INFO: {len(invoice_data.results)}"
                )

            api_log(
                msg=f"COMPANY INFO GET:: The length of all company info data is : {len(all_company_info)}"
            )
            return {
                "data": all_company_info,
                "status": True,
            }

        except ApiError as e:
            return self.handle_merge_api_error("get_invoices", e)

    def create_invoice(self, invoice_data: dict):
        """
        create_invoice method
        """
        try:
            response = self.merge_client.accounting.invoices.create(
                model=InvoiceRequest(**invoice_data)
            )
            if len(response.errors) > 0:
                api_log(msg="MERGE : Error creating invoice")
                raise MergeApiException(response.errors)

            api_log(msg=f"MERGE : Invoice created successfully: {response}")

            self.create_or_update_log(
                {
                    "id": uuid.uuid4(),
                    "invoice_id": invoice_data.get("id"),
                    "type": "invoice",
                    "status": "success",
                    "message": "Invoice created successfully",
                }
            )

            return response

        except Exception as e:
            self.create_or_update_log(
                {
                    "id": uuid.uuid4(),
                    "invoice_id": invoice_data.get("id"),
                    "type": "invoice",
                    "status": "failed",
                    "message": str(e),
                }
            )
            api_log(msg=f"MERGE EXCEPTION: Error creating invoice: {str(e)}")
            raise e

    def update_invoice(self, invoice_id: str, invoice_data: dict):
        api_key = os.getenv("API_KEY")
        api_log(msg=f"[API KEY FOR INVOICE PATCH] : {api_key}")
        api_log(msg=f"[ACCOUNT TOKEN FOR INVOICE PATCH] : {self.account_token}")
        api_log(msg=f"[PAYLOAD FOR INVOICE PATCH] :{invoice_data}")
        print(" ")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-Account-Token": self.account_token,
                "Accept": "application/json"
            }
            api_log(msg=f"[BEARER TOKEN BLOC merge service file] : {headers}")
            invoice_update_url = f"https://api-eu.merge.dev/api/accounting/v1/invoices/{invoice_id}"
            api_log(msg=f"[URL response] : {invoice_update_url}")

            invoice_update_request = requests.patch(invoice_update_url, json=invoice_data, headers=headers)
            api_log(msg=f"[INVOICE REQUESTS.PATCH RESPONSE] : {invoice_update_request}")

            if invoice_update_request.status_code == status.HTTP_200_OK:
                api_log("Invoice updated successfully......")
                api_log(msg=f"[MERGE INVOICE UPDATE BLOC] :: Invoice ID {invoice_id} was successfully updated in Xero "
                            f"with status code: {status.HTTP_200_OK}")
                return Response(
                    {"message": f"[INVOICE UPDATE BLOC] :: Invoice ID {invoice_id} was successfully updated in Xero "
                                f"with status code: {status.HTTP_200_OK}"}
                )

            elif invoice_update_request.status_code == status.HTTP_404_NOT_FOUND:
                error_msg = f"[MERGE SERVICE PY INVOICE UPDATE BLOC] :: Invoice ID {invoice_id} is Incorrect and the " \
                            f"status code is : {status.HTTP_404_NOT_FOUND}"
                api_log(msg=error_msg)
                raise MergeApiException(error_msg)

            else:
                error_msg = f"[MERGE INVOICE UPDATE BLOC] :: Invoice ID {invoice_id} failed to update in Xero with " \
                            f"status code: {invoice_update_request.status_code} "
                api_log(msg=error_msg)
                raise MergeApiException(error_msg)

        except Exception as e:
            print("This is a exception bloc in merge_service py file ::", e)
            # self.create_or_update_log(
            #     {
            #         "id": uuid.uuid4(),
            #         "invoice_id": invoice_data.get("id"),
            #         "type": "invoice",
            #         "status": "failed",
            #         "message": str(e),
            #     }
            # )
            api_log(msg=f"MERGE EXCEPTION: Error updating invoice: {str(e)}")
            raise e

    def create_attachment(self, attachment_data: dict):
        """
        create_attachment method
        """
        try:
            response = self.merge_client.accounting.attachments.create(
                model=AccountingAttachmentRequest(**attachment_data)
            )
            if len(response.errors) > 0:

                api_log(msg="MERGE : Error creating attachment")
                raise MergeApiException(response.errors)

            self.create_or_update_log(
                {
                    "id": uuid.uuid4(),
                    "invoice_id": attachment_data.get("id"),
                    "type": "attachment",
                    "status": "success",
                    "message": "Attachment created successfully",
                }
            )

            api_log(msg=f"MERGE : Attachment created successfully: {response}")
            return response

        except Exception as e:
            self.create_or_update_log(
                {
                    "id": uuid.uuid4(),
                    "invoice_id": attachment_data.get("id"),
                    "type": "attachment",
                    "status": "failed",
                    "message": str(e),
                }
            )
            api_log(msg=f"MERGE EXCEPTION: Error creating attachment: {str(e)}")
            raise e

    @classmethod
    def create_or_update_log(cls, log_data: dict):
        """
        create_log method
        """
        try:
            # check if log already exists
            log = InvoiceAttachmentLogs.objects.filter(
                invoice_id=log_data.get("invoice_id"), type=log_data.get("type")
            ).first()

            if log:
                log.status = log_data.get("status")
                log.message = log_data.get("message")
                log.save()
                api_log(msg=f"INVOICE LOG : Log updated successfully: {log}")
                return log

            create_object = InvoiceAttachmentLogs(**log_data)
            log_created = create_object.save()
            api_log(msg=f"INVOICE LOG : Log created successfully: {log_created}")

            return log_created
        except Exception as e:
            api_log(msg=f"INVOICE LOG EXCEPTION: Error creating log: {str(e)}")
            raise e
