"""
DB queries for INVOICES
"""

import uuid

import MySQLdb
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


def update_erp_id_in_line_items(invoice_id: str, line_items):
    """
    helper function to fetch line item remote id based on invoice id
    and update in invoice_line_items table

    """
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

            api_log(msg=f" existing rows data from invoice_line_items :{rows}")
            new_items = []
            for line in line_items:
                new_items.append(dict(line))
            db_row = len(rows)

            if db_row > 0:
                for index in range(db_row):
                    row = rows[index]
                    loop_line_items = new_items[index]

                    api_log(msg=f"DB rows data: {row}")

                    loop_line_items.get("tracking_categories")
                    list_row = list(row)
                    api_log(msg=f" uuid id : {list_row}")
                    list_row[10] = loop_line_items.get("id")
                    list_row[11] = loop_line_items.get("remote_id")
                    api_log(
                        msg=f" list row from payload : {loop_line_items.get('remote_id')}"
                    )
                    update_query = """
                              UPDATE invoice_line_items
                              SET erp_id = %s,
                              remote_id = %s
                              WHERE invoice_id = %s AND id = %s
                            """
                    update_args = (list_row[10], list_row[11], invoice_id, list_row[0])
                    # Convert None values to NULL
                    update_args = tuple(
                        arg if arg is not None else None for arg in update_args
                    )
                    cursor.execute(update_query, update_args)
                    api_log(msg=f"Updated line item with erp_id: {list_row[10]}")

    except MySQLdb.Error as db_error:
        api_log(msg=f"EXCEPTION : Database error occurred: {db_error}")
    except Exception as e:
        api_log(
            msg=f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}"
        )


def patch_update_line_items(invoice_id: str, line_items):
    """
    helper function to fetch line item remote id based on invoice id
    and update in invoice_line_items table

    """
    api_log(msg=f"line items from query py file : {line_items}")
    api_log(msg=f"updated of the line items started for invoice id : {invoice_id}")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id
                 FROM invoices
                 WHERE erp_id = %s""",
                [invoice_id],
            )
            rows = cursor.fetchall()
            api_log(msg=f" ID field of invoices table :{rows[0][0]}")

            cursor.execute(
                """SELECT *
                 FROM invoice_line_items
                 WHERE invoice_id = %s
                 ORDER BY sequence desc""",
                [rows[0][0]],
            )
            invoice_id_row = cursor.fetchall()
            api_log(
                msg=f" invoice ID field of invoice_line_items table :{invoice_id_row}"
            )
            new_items = []
            for line in line_items:
                new_items.append(line)
            api_log(msg=f"payload data: {new_items}")
            api_log(msg=f"payload data type: {type(new_items)}")
            db_row = len(invoice_id_row)

            if db_row > 0:
                for index in range(db_row):
                    row_tuple = invoice_id_row[index]
                    loop_line_items = new_items[index]
                    api_log(msg=f"loop_line_items {loop_line_items}")
                    # loop_line_items_dict = dict(loop_line_items)
                    # api_log(msg=f"loop_line_items dict :{loop_line_items_dict}")
                    # api_log(msg=f"existing rows length: {len(rows)}")
                    api_log(msg=f"DB rows data: {row_tuple}")
                    api_log(msg=f"List of line item JSON : {loop_line_items}")

                    row = list(row_tuple)
                    row[0] = uuid.uuid1()
                    row[1] = rows[0][0]
                    api_log(msg=f"{invoice_id}")
                    row[2] = loop_line_items.get("description")
                    # api_log(msg=f"{item}")
                    row[3] = loop_line_items.get("unit_price")
                    # api_log(msg=f"{unit_price}")
                    row[4] = loop_line_items.get("quantity")
                    # api_log(msg=f"{quantity}")
                    row[5] = loop_line_items.get("total_amount")
                    # api_log(msg=f"{total_amount}")
                    row[6] = loop_line_items.get("sequence")
                    # api_log(msg=f"{sequence}")
                    row[7] = loop_line_items.get("created_at")
                    # api_log(msg=f"{created_at}")
                    row[8] = loop_line_items.get("updated_at")
                    # api_log(msg=f"{updated_at}")
                    row[9] = loop_line_items.get("deleted_at")
                    # api_log(msg=f"{deleted_at}")
                    row[10] = loop_line_items.get("id")
                    # api_log(msg=f"{erp_id}")
                    row[11] = loop_line_items.get("remote_id")
                    # api_log(msg=f"{remote_id}")
                    row[18] = loop_line_items.get("erp_modified_at")
                    # api_log(msg=f"{erp_modified_at}")
                    row[19] = loop_line_items.get("erp_created_at")
                    # api_log(msg=f"{erp_created_at}")
                    row[20] = loop_line_items.get("erp_remote_data")
                    # api_log(msg=f"{erp_remote_data}")
                    row[21] = loop_line_items.get("erp_account")
                    # api_log(msg=f"{row[21]}")

                    update_query = """UPDATE invoice_line_items SET invoice_id = %s, item = %s, unit_price = %s,
                    quantity = %s, total_amount = %s, sequence = %s, created_at = %s, updated_at = %s, deleted_at = %s,
                    erp_id = %s, remote_id = %s, erp_modified_at = %s, erp_created_at = %s, erp_remote_data = %s,
                    erp_account = %s
                              WHERE invoice_id = %s AND id = %s
                            """
                    update_args = (
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9],
                        row[10],
                        row[11],
                        row[18],
                        row[19],
                        row[20],
                        row[21],
                        row[1],
                        row[0],
                    )
                    # Convert None values to NULL
                    update_args = tuple(
                        arg if arg is not None else None for arg in update_args
                    )
                    cursor.execute(update_query, update_args)
                    api_log(msg="updated successfully")

    except MySQLdb.Error as db_error:
        api_log(msg=f"EXCEPTION : Database error occurred: {db_error}")
    except Exception as e:
        api_log(
            msg=f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}"
        )
