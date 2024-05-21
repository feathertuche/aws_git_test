"""
DB queries for INVOICES
"""

import uuid

from django.db import DatabaseError, connection

from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log


def get_erp_link_tokens(filters: dict = None):
    """
    Get the erp_link_token details from the database
    """
    try:
        erp_link_tokens = ErpLinkToken.objects.filter(**filters)
        return erp_link_tokens
    except DatabaseError as e:
        api_log(msg=f"Error retrieving erp_link_token details: {str(e)}")
        raise e


def get_currency_id(currency_code: str):
    """
    Get the currency_id from the currency_code
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT id
                FROM currencies
                WHERE currency = %s
                """,
            [currency_code],
        )
        row = cursor.fetchone()
        return row


def update_invoices_erp_id(invoice_table_id: str, erp_invoice_id: str, remote_id: str):
    """
    helper function update erp_id on Invoices table ID field.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE invoices
            SET erp_id = %s, remote_id = %s
            WHERE id = %s
            """,
            [erp_invoice_id, remote_id, invoice_table_id],
        )
        row = cursor.fetchone()
        return row


def get_existing_invoice_line_items(invoice_id: uuid.UUID):
    """
    Get the line items from the invoice_line_items table
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT *
                FROM invoice_line_items
                WHERE invoice_id = %s AND erp_id IS NOT NULL
                ORDER BY sequence desc""",
            [invoice_id],
        )
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows


def get_new_invoice_line_items(invoice_id: uuid.UUID):
    """
    Get the line items from the invoice_line_items table
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT *
                FROM invoice_line_items
                WHERE invoice_id = %s AND erp_id IS NULL
                ORDER BY sequence desc""",
            [invoice_id],
        )
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows


def update_line_item(line_item_id: uuid.UUID, update_data: dict):
    """
    Update the erp_id and remote_id in the invoice_line_items table
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE invoice_line_items
                    SET
                        erp_id = %s,
                        remote_id = %s,
                        erp_purchase_price = %s,
                        erp_purchase_account = %s,
                        erp_company = %s,
                        erp_field_mappings = %s,
                        erp_modified_at = %s,
                        erp_created_at = %s,
                        erp_remote_data = %s
                    WHERE id = %s
                """,
                [
                    update_data.get("id"),
                    update_data.get("remote_id"),
                    update_data.get("unit_price"),
                    update_data.get("account"),
                    update_data.get("company"),
                    update_data.get("field_mappings"),
                    update_data.get("modified_at"),
                    update_data.get("created_at"),
                    update_data.get("remote_data"),
                    line_item_id,
                ],
            )
            row = cursor.fetchone()
            return row
    except DatabaseError as e:
        api_log(msg=f"Error updating line item query: {str(e)}")
        raise e
