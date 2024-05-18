"""
Helper functions for the INVOICES app
"""

import uuid

from merge.resources.accounting import InvoiceLineItemRequest

from INVOICES.queries import get_currency_id
from merge_integration.helper_functions import api_log


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


def filter_invoice_payloads(invoice_valid_payload):
    """
    prepare invoice payload based on integration name
    """
    integration_name = invoice_valid_payload.get("integration_name")
    model_data = invoice_valid_payload.get("model")

    if integration_name == "Sage Intacct":
        return create_sage_invoice_payload(model_data)
    elif integration_name == "Xero":
        return create_xero_invoice_payload(model_data)
    else:
        raise Exception("Integration doesn't exists for invoice filter")


def filter_attachment_payloads(attachment_valid_payload, invoice_created):
    """
    prepare invoice payload based on integration name
    """
    integration_name = attachment_valid_payload.get("integration_name")
    model_data = attachment_valid_payload.get("model")

    if integration_name == "Sage Intacct":
        return create_sage_attachment_payload(
            model_data, invoice_created.model.remote_id
        )

    elif integration_name == "Xero":
        return create_xero_attachment_payload(model_data, invoice_created.model.id)

    else:
        raise Exception("Integration doesn't exists for Attachment filter")


def create_sage_invoice_payload(invoice_validated_payload):
    """
    Sage invoice payload
    """
    api_log(msg="Creating sage invoice payload")

    model_data = invoice_validated_payload

    # prepare line items data
    line_items_data = []
    for line_item_payload in model_data.get("line_items", []):
        line_item_data = {
            "unit_price": line_item_payload.get("unit_price"),
            "currency": line_item_payload.get("currency"),
            "exchange_rate": model_data.get("exchange_rate"),
            "description": line_item_payload.get("item"),
            "quantity": line_item_payload.get("quantity"),
            "total_amount": line_item_payload.get("total_amount"),
            "tracking_categories": model_data.get("tracking_categories"),
            "account": line_item_payload.get("account"),
            "sequence": line_item_payload.get("sequence"),
        }
        line_items_data.append(line_item_data)

    # sort line items by sequence
    line_items_data = sorted(line_items_data, key=lambda x: x["sequence"])

    # prepare invoice data
    invoice_data = {
        "id": model_data.get("kloo_invoice_id"),
        "type": model_data.get("type"),
        "due_date": model_data.get("due_date"),
        "issue_date": model_data.get("issue_date"),
        "contact": model_data.get("contact"),
        "number": model_data.get("number"),
        "memo": model_data.get("memo"),
        "company": model_data.get("company"),
        "currency": model_data.get("currency"),
        "tracking_categories": model_data.get("tracking_categories"),
        "sub_total": model_data.get("sub_total"),
        "total_tax_amount": model_data.get("total_tax_amount"),
        "total_amount": model_data.get("total_amount"),
        "line_items": [
            InvoiceLineItemRequest(**line_item) for line_item in line_items_data
        ],
    }

    return invoice_data


def create_xero_invoice_payload(invoice_validated_payload):
    """
    xero invoice payload
    """

    model_data = invoice_validated_payload
    # prepare line items data
    line_items_data = []
    for line_item_payload in model_data.get("line_items", []):
        line_item_data = {
            "unit_price": line_item_payload.get("unit_price"),
            "currency": line_item_payload.get("currency"),
            "exchange_rate": model_data.get("exchange_rate"),
            "description": line_item_payload.get("item"),
            "quantity": line_item_payload.get("quantity"),
            "created_at": line_item_payload.get("created_at"),
            "tracking_categories": model_data.get("tracking_categories"),
            "integration_params": {
                "tax_rate_remote_id": line_item_payload.get("tax_rate_remote_id")
            },
            "account": line_item_payload.get("account"),
            "remote_data": line_item_payload.get("remote_data"),
            "sequence": line_item_payload.get("sequence"),
        }
        line_items_data.append(line_item_data)

    # sort line items by sequence
    line_items_data = sorted(line_items_data, key=lambda x: x["sequence"])

    # prepare invoice data
    invoice_data = {
        "id": model_data.get("kloo_invoice_id"),
        "type": model_data.get("type"),
        "due_date": model_data.get("due_date"),
        "issue_date": model_data.get("issue_date"),
        "contact": model_data.get("contact"),
        "number": model_data.get("number"),
        "memo": model_data.get("memo"),
        "status": model_data.get("status"),
        "company": model_data.get("company"),
        "currency": model_data.get("currency"),
        "tracking_categories": model_data.get("tracking_categories"),
        "sub_total": model_data.get("sub_total"),
        "total_tax_amount": model_data.get("total_tax_amount"),
        "total_amount": model_data.get("total_amount"),
        "integration_params": {
            "tax_application_type": model_data.get("tax_application_type")
        },
        "line_items": [
            InvoiceLineItemRequest(**line_item) for line_item in line_items_data
        ],
    }
    api_log(msg=f"this is a invoice data: {invoice_data}")

    return invoice_data


def create_sage_attachment_payload(attachment_validated_payload, remote_id):
    """
    create sage attachment
    """
    attachment_data = attachment_validated_payload.get("attachment")
    attachment_payload = {
        "id": attachment_validated_payload.get("kloo_invoice_id"),
        "file_name": attachment_data.get("file_name"),
        "file_url": attachment_data.get("file_url"),
        "integration_params": {
            "folder_name": "Invoices",
            "supdocid": remote_id,
        },
    }

    return attachment_payload


def create_xero_attachment_payload(attachment_validated_payload, invoice_id):
    """
    create xero attachment
    """
    attachment_data = attachment_validated_payload.get("attachment")

    attachment_payload = {
        "id": attachment_validated_payload.get("kloo_invoice_id"),
        "file_name": attachment_data.get("file_name"),
        "file_url": attachment_data.get("file_url"),
        "integration_params": {
            "transaction_id": invoice_id,
            "transaction_name": attachment_data.get("transaction_name"),
        },
    }

    return attachment_payload


# =========================================================================================#
# PATCH PAYLOAD#
# =========================================================================================#


def patch_sage_invoice_payload(patch_payload):
    """
    Sage invoice payload
    """
    api_log(msg="Creating sage invoice payload")

    payload_data = patch_payload

    line_items = []
    for line_item_data in payload_data["model"]["line_items"]:
        line_item = {
            "id": line_item_data.get("id"),
            "remote_id": line_item_data.get("remote_id"),
            "unit_price": float(
                line_item_data.get("unit_price")
                if line_item_data.get("unit_price") is not None
                else 0
            ),
            "currency": line_item_data.get("currency"),
            "exchange_rate": line_item_data.get("exchange_rate"),
            "description": line_item_data.get("item"),
            "quantity": float(
                line_item_data.get("quantity")
                if line_item_data.get("quantity") is not None
                else 0
            ),
            "total_amount": float(
                line_item_data.get("total_amount")
                if line_item_data.get("total_amount") is not None
                else 0
            ),
            "created_at": line_item_data.get("created_at"),
            "tracking_categories": line_item_data.get("tracking_categories"),
            "account": line_item_data.get("account"),
        }
        line_items.append(line_item)

    payload = {
        "model": {
            "id": payload_data.get("kloo_invoice_id"),
            "type": payload_data["model"].get("type"),
            "due_date": payload_data["model"].get("due_date"),
            "issue_date": payload_data["model"].get("issue_date"),
            "contact": payload_data["model"].get("contact"),
            "number": payload_data["model"].get("number"),
            "memo": payload_data["model"].get("memo"),
            "status": payload_data["model"].get("status"),
            "company": payload_data["model"].get("company"),
            "currency": payload_data["model"].get("currency"),
            "tracking_categories": payload_data["model"].get("tracking_categories"),
            "sub_total": float(
                payload_data["model"].get("sub_total")
                if payload_data["model"].get("sub_total") is not None
                else 0
            ),
            "total_tax_amount": float(
                payload_data["model"].get("total_tax_amount")
                if payload_data["model"].get("total_tax_amount") is not None
                else 0
            ),
            "total_amount": float(
                payload_data["model"].get("total_amount")
                if payload_data["model"].get("total_amount") is not None
                else 0
            ),
            "line_items": line_items,
        },
        "warnings": [],
        "errors": [],
    }

    return payload


def patch_xero_invoice_payload(patch_payload):
    """
    Xero invoice payload
    """
    api_log(msg=f"payload in invoice helper function: {patch_payload}")

    api_log(msg="Creating Xero invoice payload")
    api_log(msg="45")
    payload_data = patch_payload
    api_log(msg="46")
    line_items = []
    for line_item_data in payload_data["model"]["line_items"]:
        api_log(msg="47")
        api_log(msg=f"line_item_data: {line_item_data}")
        line_item = {
            "id": line_item_data.get("erp_id"),
            "remote_id": line_item_data.get("remote_id"),
            "unit_price": float(
                line_item_data.get("unit_price")
                if line_item_data.get("unit_price") is not None
                else 0
            ),
            "currency": line_item_data.get("currency"),
            "exchange_rate": line_item_data.get("exchange_rate"),
            "description": line_item_data.get("item"),
            "quantity": float(
                line_item_data.get("quantity")
                if line_item_data.get("quantity") is not None
                else 0
            ),
            "created_at": line_item_data.get("created_at"),
            # "tracking_categories": line_item_data.get("tracking_categories"),
            # "integration_params": {
            #     "tax_rate_remote_id": line_item_data.get("tax_rate_remote_id")
            # },
            "account": line_item_data.get("account"),
            "remote_data": line_item_data.get("remote_data"),
        }
        line_items.append(line_item)

    payload = {
        "model": {
            "id": payload_data["model"].get("erp_id"),  # erp_id of invoice table
            "invoice_id": payload_data["model"].get(
                "kloo_invoice_id"
            ),  # id field of invoice table
            "type": payload_data["model"].get("type"),
            "due_date": payload_data["model"].get("due_date"),
            "issue_date": payload_data["model"].get("issue_date"),
            "contact": payload_data["model"].get("contact"),
            "number": payload_data["model"].get("number"),
            "memo": payload_data["model"].get("memo"),
            "status": payload_data["model"].get("status"),
            "company": payload_data["model"].get("company"),
            "currency": payload_data["model"].get("currency"),
            "tracking_categories": payload_data["model"].get("tracking_categories"),
            "sub_total": float(
                payload_data["model"].get("sub_total")
                if payload_data["model"].get("sub_total") is not None
                else 0
            ),
            "total_tax_amount": float(
                payload_data["model"].get("total_tax_amount")
                if payload_data["model"].get("total_tax_amount") is not None
                else 0
            ),
            "total_amount": float(
                payload_data["model"].get("total_amount")
                if payload_data["model"].get("total_amount") is not None
                else 0
            ),
            "line_items": line_items,
        },
        "warnings": [],
        "errors": [],
    }

    return payload


def invoice_patch_payload(request_data):
    """
    prepare invoice payload based on integration name
    """
    api_log(msg=f"request payload : {request_data}")

    integration_name = request_data.get("integration_name")
    # model_data = request_data.get("model")

    api_log(msg=f"model data : {request_data}")

    if integration_name == "Sage Intacct":
        return patch_sage_invoice_payload(request_data)

    elif integration_name == "Xero":
        return patch_xero_invoice_payload(request_data)

    else:
        raise Exception("Integration doesn't exists for invoice filter")
