"""
DB queries for INVOICES
"""
import uuid

import MySQLdb
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


def update_invoices_erp_id(uuid_id: str, response_id: str):
    """
    helper function update erp_id on Invoices table ID field.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE invoices
            SET erp_id = %s
            WHERE id = %s
            """,
            [response_id, uuid_id],
        )
        row = cursor.fetchone()
        return row


def insert_line_item_erp_id(invoice_id: str, line_items):
    """
    helper function to fetch line item remote id based on invoice id
    and update in invoice_line_items table

    """
    api_log(msg=f"line items from query py file : {line_items}")
    api_log(msg=f"updated of the line items started for invoice id : {invoice_id}")
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
                    api_log(msg=f"existing rows length: {len(rows)}")
                    api_log(msg=f"DB rows data: {rows}")
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

    except MySQLdb.Error as db_error:
        api_log(msg=f"EXCEPTION : Database error occurred: {db_error}")
    except Exception as e:
        api_log(msg=f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}")
