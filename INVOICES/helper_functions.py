"""
Helper functions for the INVOICES app
"""

import uuid

from INVOICES.queries import get_currency_id


def format_merge_invoice_data(invoice_response, erp_link_token_id, org_id):
    """
    Format the merge invoice data
    """
    invoices_json = []
    for invoice in invoice_response["data"]:
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
            "due_date": (invoice.due_date.isoformat() if invoice.due_date else None),
            "paid_on_date": (
                invoice.paid_on_date.isoformat() if invoice.paid_on_date else None
            ),
            "memo": invoice.memo,
            "company": invoice.company,
            "currency": get_currency_id(invoice.currency)[0],
            "exchange_rate": invoice.exchange_rate,
            "total_discount": invoice.total_discount,
            "sub_total": invoice.sub_total,
            "erp_status": invoice.status,
            "total_tax_amount": invoice.total_tax_amount,
            "total_amount": invoice.total_amount,
            "balance": invoice.balance,
            "tracking_categories": [
                category for category in invoice.tracking_categories
            ],
            "payments": [payment for payment in invoice.payments],
            "applied_payments": [
                applied_payment for applied_payment in invoice.applied_payments
            ],
            "line_items": [
                format_line_item(line_item) for line_item in invoice.line_items
            ],
            "accounting_period": invoice.accounting_period,
            "purchase_orders": [
                purchase_order for purchase_order in invoice.purchase_orders
            ],
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

    return invoices_json


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
