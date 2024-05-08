"""
DB queries for INVOICES
"""
import uuid
from rest_framework.response import Response
from rest_framework import status
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


def insert_line_item_erp_id(invoice_id: str, line_items):
    """
    helper function to fetch line item remote id based on invoice id
    and insert/update in invoice_line_items table

    """
    api_log(msg=f"line items from query py file : {line_items}")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT *
                 FROM invoice_line_items
                 WHERE invoice_id = %s
                 ORDER BY sequence desc""",
                [invoice_id],
            )
            rows = cursor.fetchall()
            new_items = []
            for line in line_items:
                new_items.append(dict(line))
            api_log(msg=f" query line item list :{new_items}")
            db_row = len(rows)
            api_log(msg=f" query line item list :{db_row}")

            if db_row > 0:
                for index in range(db_row):
                    row = rows[index]
                    loop_line_items = new_items[index]
                    api_log(msg=f"DB rows details: {len(rows)}")
                    api_log(msg=f"DB rows details: {rows}")
                    api_log(msg=f"List of line item JSON : {loop_line_items}")

                    tracking_categories = loop_line_items.get('tracking_categories')
                    list_row = list(row)
                    api_log(msg=f" uuid id : {list_row[0]}")
                    list_row[2] = loop_line_items.get('item')
                    list_row[3] = loop_line_items.get('unit_price')
                    list_row[4] = loop_line_items.get('quantity')
                    list_row[5] = loop_line_items.get('total_amount')
                    list_row[10] = loop_line_items.get('remote_id')
                    list_row[19] = loop_line_items.get('remote_data')
                    list_row[20] = loop_line_items.get('account')
                    list_row[21] = loop_line_items.get('integration_params', {}).get('tax_rate_remote_id')
                    list_row[22] = ','.join(tracking_categories) if tracking_categories else None
                    update_query = """
                                UPDATE invoice_line_items
                                SET item = %s, unit_price = %s, quantity = %s,
                                    total_amount = %s, sequence = %s, erp_id = %s,
                                    erp_remote_data = %s, erp_account = %s, erp_tax_rate = %s,
                                    erp_tracking_categories = %s
                                WHERE invoice_id = %s AND id = %s
                            """
                    api_log(msg="summit")
                    update_args = (
                        list_row[2], list_row[3], list_row[4], list_row[5], 1,
                        list_row[10], list_row[19], list_row[20], list_row[21],
                        list_row[22], invoice_id, list_row[0]
                    )
                    # Convert None values to NULL
                    update_args = tuple(arg if arg is not None else None for arg in update_args)
                    cursor.execute(update_query, update_args)
                    api_log(msg=f"Updated line item with erp_id: {list_row[10]}")
                    api_log(msg="updated successfully")

    except Exception as e:
        error_message = f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}"
        return Response(
            {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_erp_ids(invoice_id: str, erp_payload):
    """
    Fetch erp_id values from the invoice_lite_items table
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """select id 
            FROM invoices
            WHERE erp_id = %s
            """,
            [invoice_id],
        )
        row1 = cursor.fetchone()

        api_log(msg=f"This is the list of ID(s) from Invoices table: {row1[0]}")
        cursor.execute(
            """SELECT erp_id
                FROM invoice_line_items
                WHERE invoice_id = %s and erp_id is null and delete_at is null
            """,
            [row1[0]],
        )
        rows = cursor.fetchall()

        erp_ids = [row[0] for row in rows]
        api_log(msg=f"[ERP ID from invoice_line_items TABLE] : {erp_ids}")
        for new_line_items in erp_payload:
            api_log(msg=f"[ERP ID from LINE ITEM's PAYLOAD] : {new_line_items['id']}")
            if new_line_items["id"] not in erp_ids:
                tracking_categories = new_line_items.get('tracking_categories')
                id = uuid.uuid1()
                invoice_id = row1
                item = new_line_items.get('description')
                unit_price = new_line_items.get('unit_price')
                quantity = new_line_items.get('quantity')
                total_amount = new_line_items.get('total_amount')
                sequence = 1
                erp_id = new_line_items.get('remote_id')
                erp_remote_data = new_line_items.get('remote_data')
                erp_account = new_line_items.get('account')
                erp_tax_rate = new_line_items.get('integration_params', {}).get('tax_rate_remote_id')
                erp_tracking_categories = ','.join(tracking_categories) if tracking_categories else None
                is_ai_generated = 0
                print(new_line_items.get('description'))
                cursor.execute(
                    """INSERT INTO invoice_line_items (id, invoice_id, item, unit_price, quantity, total_amount, sequence,
                        erp_id, erp_remote_data, erp_account, erp_tax_rate, erp_tracking_categories, is_ai_generated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s)""",
                    (id, invoice_id, item, unit_price, quantity, total_amount, sequence,
                     erp_id, erp_remote_data, erp_account, erp_tax_rate, erp_tracking_categories, is_ai_generated)
                )
                print("Inserted successfully")
            else:
                # If the erp_id already exists in invoice_line_items, perform an UPDATE
                tracking_categories = new_line_items.get('tracking_categories')
                item = new_line_items.get('description')
                unit_price = new_line_items.get('unit_price')
                quantity = new_line_items.get('quantity')
                total_amount = new_line_items.get('total_amount')
                erp_remote_data = new_line_items.get('remote_data')
                erp_account = new_line_items.get('account')
                erp_tax_rate = new_line_items.get('integration_params', {}).get('tax_rate_remote_id')
                erp_tracking_categories = ','.join(tracking_categories) if tracking_categories else None

                cursor.execute(
                    """UPDATE invoice_line_items 
                       SET item = %s, unit_price = %s, quantity = %s, total_amount = %s,
                           erp_remote_data = %s, erp_account = %s, erp_tax_rate = %s,
                           erp_tracking_categories = %s
                       WHERE erp_id = %s""",
                    (item, unit_price, quantity, total_amount, erp_remote_data,
                     erp_account, erp_tax_rate, erp_tracking_categories, erp_id)
                )
                api_log(msg=f"Updated line item with erp_id: {erp_id}")
                print("updated successfully")
