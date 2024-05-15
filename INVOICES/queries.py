"""
DB queries for INVOICES
"""
import json
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

            api_log(msg=f" existing rows data from invoice_line_items :{rows}")
            new_items = []
            for line in line_items:
                new_items.append(dict(line))
            api_log(msg=f" query line item list :{new_items}")
            db_row = len(rows)
            api_log(msg=f" query count :{db_row}")

            if db_row > 0:
                for index in range(db_row):
                    row = rows[index]
                    loop_line_items = new_items[index]
                    api_log(msg=f"existing rows length: {len(rows)}")
                    api_log(msg=f"DB rows data: {rows}")
                    api_log(msg=f"List of line item JSON : {loop_line_items}")

                    loop_line_items.get("tracking_categories")
                    list_row = list(row)
                    api_log(msg=f" uuid id : {list_row}")
                    list_row[10] = loop_line_items.get("id")
                    list_row[11] = loop_line_items.get("remote_id")
                    api_log(msg=f" list_row[10] : {list_row[10]}")
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
                    api_log(msg="updated successfully")

    except MySQLdb.Error as db_error:
        api_log(msg=f"EXCEPTION : Database error occurred: {db_error}")
    except Exception as e:
        api_log(
            msg=f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}"
        )


def update_line_items(invoice_erp_id: str, line_items_payload: list):
    api_log(msg=f"invoice_erp_id: {invoice_erp_id}")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id
                 FROM invoices
                 WHERE erp_id = %s""",
                [invoice_erp_id],
            )
            rows = cursor.fetchall()
            invoice_id = rows[0][0]
            api_log(msg=f"ID field of invoices table: {rows[0][0]}")

            cursor.execute(
                """SELECT erp_id
                 FROM invoice_line_items
                 WHERE invoice_id = %s""",
                [invoice_id],
            )
            api_log(msg="12")
            get_erp_id_from_db = cursor.fetchall()
            invoice_id = rows[0][0]
            api_log(msg="13")
            api_log(msg=f"uuid field of invoice_line_items table: {get_erp_id_from_db}")
            api_log(msg="14")

            # convert erp_ids tuple from DB to a list
            erp_id_list = [
                element for tuple_ in get_erp_id_from_db for element in tuple_
            ]
            api_log(msg=f"erp id list from invoice_line_item table : {erp_id_list}")

            # fetching list of remote_id's from line items payload
            remote_id_payload_list = []
            for line_item_dict in line_items_payload:
                api_log(msg=f"remote ids dictionary : {line_item_dict}")
                remote_id_payload_list.append(line_item_dict["id"])
            api_log(msg=f"remote id's list from payload : {remote_id_payload_list}")

            # Bloc to compare the erp_id field from db and id field of payload from line_items
            api_log(msg=f"merge payload: {line_items_payload}")
            for item_data in line_items_payload:
                api_log(msg=f"item_data : {item_data}")
                if item_data["id"] in erp_id_list:
                    api_log(msg="Executing the UPDATE bloc as the ERP iD already exist")
                    item = item_data["description"]
                    unit_price = (item_data["unit_price"],)
                    quantity = (item_data["quantity"],)
                    erp_id = item_data["id"]
                    update_query = """
                        UPDATE invoice_line_items
                        SET
                            item = %s,
                            unit_price = %s,
                            quantity = %s
                        WHERE
                            invoice_id = %s AND erp_id = %s
                    """

                    # Assuming list_row[10] corresponds to tracking_categories
                    update_args = (
                        # description,
                        item,
                        unit_price,
                        quantity,
                        invoice_id,
                        erp_id,
                    )

                    update_args = tuple(
                        arg if arg is not None else None for arg in update_args
                    )
                    cursor.execute(update_query, update_args)
                    api_log(msg="updated successfully")

                else:
                    api_log(msg="Executing the Insert bloc as the ERP ID doesn't exist")
                    all_tracking_categories = item_data.get("tracking_categories")
                    invoice_id = rows[0][0]
                    item = item_data.get("description")
                    unit_price = item_data.get("unit_price")
                    quantity = item_data.get("quantity")
                    total_amount = item_data.get("total_amount")
                    erp_id = item_data.get("id")
                    erp_remote_data = item_data.get("remote_data")
                    erp_account = item_data.get("account")
                    erp_tracking_categories = (
                        json.dumps(all_tracking_categories) if all_tracking_categories else None
                    )

                    # insert the data
                    insert_query = """INSERT INTO invoice_line_items (id, invoice_id, item, unit_price, quantity,
                    total_amount, erp_id, erp_remote_data, erp_account, erp_tracking_categories) VALUES (%s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s) """

                    id = uuid.uuid1()
                    insert_args = (
                        id,
                        invoice_id,
                        item,
                        unit_price,
                        quantity,
                        total_amount,
                        erp_id,
                        erp_remote_data,
                        erp_account,
                        erp_tracking_categories,
                    )
                    cursor.execute(insert_query, insert_args)

    except MySQLdb.Error as db_error:
        api_log(msg=f"EXCEPTION : Database error occurred: {db_error}")
    except Exception as e:
        api_log(
            msg=f"EXCEPTION : Failed to send data to invoice_line_items table: {str(e)}"
        )
