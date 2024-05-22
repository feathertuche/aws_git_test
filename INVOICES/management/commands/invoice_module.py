import uuid
from datetime import datetime, timezone

import requests
from django.core.management.base import BaseCommand
from merge.resources.accounting import (
    InvoicesListRequestExpand,
)
from rest_framework import status

from INVOICES.queries import get_currency_id
from merge_integration.helper_functions import api_log
from merge_integration.settings import GETKLOO_BASE_URL
from merge_integration.utils import create_merge_client


class Command(BaseCommand):
    """
    Search and add matching suppliers from the list to Kloo Contacts

    1. Add user account token
    2. Add erp link token id
    3. Add organization id
    4. Add auth token from the env where you want to send the data ( since we cant use intranet api from outside)


    * First add the list of suppliers names in the variable suppliers_name_list
    * Then fetch the contacts data from the merge api , you must do it in batch of 100 records
    * First get 100 records search for matching suppliers , if any match found store that supplier merge id variable contact_ids
    * Then fetch the next 100 records and do the same until all the records are fetched
    * Then send the contact_ids to Merge retrieve api to get the contact data
    * Then format the data in the required format and send it to the Kloo Contacts API

    """

    help = "Add Matching suppliers from list to Kloo Contacts"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.KLOO_URL = None

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")

        account_token = ""
        erp_link_token_id = ""
        org_id = ""
        auth_token = ""

        try:
            invoice_client = create_merge_client(account_token)

            modified_after = "2024-04-30 10:38:41+00:00"

            # convert the date to iso format
            modified_after = datetime.strptime(
                modified_after, "%Y-%m-%d %H:%M:%S%z"
            ).astimezone(timezone.utc)

            invoices_records = []

            invoice_data = invoice_client.accounting.invoices.list(
                expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                page_size=100,
                include_remote_data=True,
                modified_after=modified_after,
            )

            total_invoices = 0

            while True:
                api_log(msg=f"Adding {len(invoice_data.results)} invoices to the list.")

                total_invoices += len(invoice_data.results)

                invoices_records.extend(invoice_data.results)

                if invoice_data.next is None:
                    break

                invoice_data = invoice_client.accounting.invoices.list(
                    expand=InvoicesListRequestExpand.ACCOUNTING_PERIOD,
                    page_size=100,
                    include_remote_data=True,
                    cursor=invoice_data.next,
                    modified_after=modified_after,
                )

            api_log(msg=f"Total Invoices: {len(invoices_records)} and {total_invoices}")

            formatted_data = format_merge_invoice_data(
                invoices_records, erp_link_token_id, org_id
            )

            formatted_data["erp_link_token_id"] = erp_link_token_id
            formatted_data["org_id"] = org_id

            invoice_url = f"{GETKLOO_BASE_URL}/ap/erp-integration/insert-erp-invoices"
            api_log(msg=f"Url: {invoice_url}")

            invoice_response_data = requests.post(
                invoice_url,
                json=formatted_data,
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            if invoice_response_data.status_code == status.HTTP_201_CREATED:
                api_log(msg="data inserted successfully in the kloo Contacts system")
            else:
                api_log(
                    msg=f"Failed to send data to Kloo Contacts API with status code {invoice_response_data.status_code}"
                )
        except Exception as e:
            api_log(msg=f"Error in fetching contacts data : {e}")
            return


def format_merge_invoice_data(invoice_response, erp_link_token_id, org_id):
    """
    Format the merge invoice data
    """
    try:
        invoices_json = []
        for invoice in invoice_response:
            invoices_data = {
                "id": str(uuid.uuid4()),
                "erp_id": invoice.id,
                "organization_id": org_id,
                "erp_link_token_id": str(erp_link_token_id),
                "contact": invoice.contact,
                "number": invoice.number,
                "issue_date": (
                    invoice.issue_date.isoformat() if invoice.issue_date else None
                ),
                "due_date": (
                    invoice.due_date.isoformat() if invoice.due_date else None
                ),
                "paid_on_date": (
                    invoice.paid_on_date.isoformat() if invoice.paid_on_date else None
                ),
                "memo": invoice.memo,
                "company": invoice.company,
                "currency": (
                    get_currency_id(invoice.currency)[0] if invoice.currency else None
                ),
                "exchange_rate": invoice.exchange_rate,
                "total_discount": invoice.total_discount,
                "sub_total": invoice.sub_total,
                "erp_status": invoice.status,
                "total_tax_amount": invoice.total_tax_amount,
                "total_amount": invoice.total_amount,
                "balance": invoice.balance,
                "tracking_categories": (
                    [category for category in invoice.tracking_categories]
                    if invoice.tracking_categories is not None
                    else None
                ),
                "payments": (
                    [payment for payment in invoice.payments]
                    if invoice.payments is not None
                    else None
                ),
                "applied_payments": (
                    [applied_payment for applied_payment in invoice.applied_payments]
                    if invoice.applied_payments is not None
                    else None
                ),
                "line_items": (
                    [format_line_item(line_item) for line_item in invoice.line_items]
                    if invoice.line_items is not None
                    else None
                ),
                "accounting_period": invoice.accounting_period,
                "purchase_orders": (
                    [purchase_order for purchase_order in invoice.purchase_orders]
                    if invoice.purchase_orders is not None
                    else None
                ),
                "erp_created_at": (
                    invoice.created_at.isoformat() if invoice.created_at else None
                ),
                "erp_modified_at": (
                    invoice.modified_at.isoformat() if invoice.modified_at else None
                ),
                "erp_field_mappings": invoice.field_mappings,
                "erp_remote_data": (
                    [
                        invoice_remote_data.data
                        for invoice_remote_data in invoice.remote_data
                    ]
                    if invoice.remote_data is not None
                    else None
                ),
            }
            invoices_json.append(invoices_data)

        return {"invoices": invoices_json}
    except Exception as e:
        api_log(msg=f"Error formatting merge invoice data: {e}")


def format_line_item(line_item):
    """
    Format the line items data
    """
    return {
        "id": line_item.id,
        "remote_id": line_item.remote_id,
        "created_at": (
            line_item.created_at.isoformat() if line_item.created_at else None
        ),
        "modified_at": (
            line_item.modified_at.isoformat() if line_item.modified_at else None
        ),
        "description": line_item.description,
        "unit_price": line_item.unit_price,
        "quantity": line_item.quantity,
        "total_amount": line_item.total_amount,
        "currency": line_item.currency,
        "exchange_rate": line_item.exchange_rate,
        "item": line_item.item,
        "account": line_item.account,
        "tracking_category": line_item.tracking_category,
        "tracking_categories": line_item.tracking_categories,
        "company": line_item.company,
        "remote_was_deleted": line_item.remote_was_deleted,
        "field_mappings": line_item.field_mappings,
    }
