"""
Third part apis services
"""

import uuid

from merge.resources.accounting import InvoiceRequest, AccountingAttachmentRequest

from INVOICES.exceptions import MergeApiException
from INVOICES.models import InvoiceAttachmentLogs
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class MergeInvoiceApiService:
    """
    MergeApiService class
    """

    def __init__(self, account_token: str):
        self.merge_client = create_merge_client(account_token)

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
