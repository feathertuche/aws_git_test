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


def update_invoices_erp_id(id: str, response_id: str):
    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE invoices
            SET erp_id = %s
            WHERE id = %s
            """,
            [response_id, id],
        )
        row = cursor.fetchone()
        return row


def update_line_item_erp_id(invoice_id: str, erp_id: str, line_items):
    """
    helper function to fetch line item remote id based on invoice id
    and insert/update in invoice_line_items table

    """
    with connection.cursor() as cursor:
        cursor.execute(
             """SELECT COUNT(*)
             FROM invoice_line_items
             WHERE invoice_id = %s""",
             [invoice_id],
         )
        row = cursor.fetchone()
        # sys.exit()
        # print("))))))))))))))", row[0])
        if row[0] > 0:
            cursor.execute(
                """UPDATE invoice_line_items
                   SET erp_id = %s
                   WHERE invoice_id = %s
                   """,
                [erp_id, invoice_id],
            )
            print("erp id updated successfully")
        else:
            # for multi_line in line_items:
            line_item_dict = dict(line_items[0])
            tracking_categories = line_item_dict.get('tracking_categories')
            id = uuid.uuid1()
            invoice_id = invoice_id
            item = line_item_dict.get('description')
            unit_price = line_item_dict.get('unit_price')
            quantity = line_item_dict.get('quantity')
            total_amount = line_item_dict.get('total_amount')
            sequence = 1
            erp_id = line_item_dict.get('remote_id')
            erp_remote_data = line_item_dict.get('remote_data')
            erp_account = line_item_dict.get('account')
            erp_tax_rate = line_item_dict.get('integration_params', {}).get('tax_rate_remote_id')
            erp_tracking_categories = ','.join(tracking_categories) if tracking_categories else None
            is_ai_generated = 0

            cursor.execute(
                """INSERT INTO invoice_line_items (id, invoice_id, item, unit_price, quantity, total_amount, sequence,
                    erp_id, erp_remote_data, erp_account, erp_tax_rate, erp_tracking_categories, is_ai_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s)""",
                (id, invoice_id, item, unit_price, quantity, total_amount, sequence,
                    erp_id, erp_remote_data, erp_account, erp_tax_rate, erp_tracking_categories, is_ai_generated)
            )
            print("Inserted successfully")

