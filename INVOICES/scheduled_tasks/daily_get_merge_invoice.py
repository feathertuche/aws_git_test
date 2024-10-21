"""
Cron job to get invoices from the merge and post them to kloo
"""

from INVOICES.helper_functions import format_merge_invoice_data
from INVOICES.queries import get_erp_link_tokens
from INVOICES.serializers import ErpInvoiceSerializer
from merge_integration.helper_functions import api_log
from services.kloo_service import KlooService
from services.merge_service import MergeInvoiceApiService


def main():
    # Get all invoices from merge
    try:
        # merge invoice api service

        # get all completed link tokens
        link_tokens = get_erp_link_tokens({"status": "COMPLETE"})

        for link_token in link_tokens:
            api_log(
                msg=f"CRON-INVOICE : Processing link_token: {link_token.account_token}"
            )

            # Get the invoices from merge
            merge_invoice_api_service = MergeInvoiceApiService(link_token.account_token)
            invoice_response = merge_invoice_api_service.get_invoices()

            if not invoice_response["status"]:
                api_log(msg="CRON-INVOICE : No invoices found in merge")
                continue

            if len(invoice_response["data"].results) == 0:
                api_log(msg="CRON-INVOICE : No invoices found in merge")
                continue

            api_log(
                msg=f"CRON-INVOICE : Processing {len(invoice_response['data'].results)} invoices"
            )

            # format the data to be posted to kloo
            invoices_json = format_merge_invoice_data(
                invoice_response, link_token.id, link_token.org_id
            )

            # validate the data using serializer
            serialized_invoices = ErpInvoiceSerializer(data=invoices_json, many=True)

            if not serialized_invoices.is_valid():
                api_log(
                    msg=f"CRON-INVOICE : Validation Error in Invoice POST cron job: {serialized_invoices.errors}"
                )
                continue

            # save the data to the database
            api_log(msg="CRON-INVOICE : Invoices saving to database")

            kloo_service = KlooService(
                auth_token=None,
                erp_link_token_id=link_token.id,
            )
            kloo_service.post_invoice_data(invoices_json)

            api_log(msg="CRON-INVOICE : Invoices posted to Kloo")

    except Exception as e:
        api_log(msg=f"CRON-INVOICE : Exception in Invoice POST cron job: {str(e)}")
        return {"status": False, "error": str(e)}
