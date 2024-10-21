"""
DB queries for Tax Rates
"""
import json
import uuid
from datetime import datetime
from MySQLdb import IntegrityError
from django.db import DatabaseError, connection
from django.utils import timezone
from SYNC.models import ERPLogs
from merge_integration.helper_functions import api_log


def Insert_Sage_Tax_Rates(tax_rate_payload: dict):
    """
    Insert Sage Tax rates into erp_tax_rates table.
    tax_rate_payload: its a payload
    """

    current_time = datetime.now()

    # Check if RECORDNO already exists in the table
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM erp_tax_rate
            WHERE RECORDNO = %s AND erp_link_token_id = %s
            """,
            (tax_rate_payload["RECORDNO"], tax_rate_payload["erp_link_token_id"])
        )
        if cursor.fetchall():
            # skip insertion if RECORDNO already exists.
            api_log(
                msg=f"Tax rate with RECORDNO {tax_rate_payload['RECORDNO']} already exists, skipping insertion.")
            return

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT IGNORE INTO erp_tax_rate (
                    id,
                    organization_id,
                    erp_link_token_id,
                    erp_id,
                    description,
                    total_tax_rate,
                    effective_tax_rate,
                    company,
                    erp_field_mappings,
                    erp_modified_at,
                    erp_created_at,
                    erp_remote_data,
                    deleted_at,
                    created_at,
                    updated_at,
                    glaccount,
                    erp_identifier,
                    RECORDNO,
                    detail_id,
                    tax_solution_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid1()),
                    tax_rate_payload["organization_id"],
                    tax_rate_payload["erp_link_token_id"],
                    None,
                    tax_rate_payload["DESCRIPTION"],
                    None,
                    None,
                    None,
                    json.dumps({}),
                    current_time,
                    current_time,
                    json.dumps(tax_rate_payload) if tax_rate_payload else None,
                    None,  # Placeholder for deleted_at
                    current_time,
                    current_time,
                    tax_rate_payload["GLACCOUNT"],
                    "PASSTHROUGH",
                    tax_rate_payload["RECORDNO"],
                    tax_rate_payload["DETAILID"],
                    tax_rate_payload["TAXSOLUTIONID"]
                )
            )
            connection.commit()
            api_log(msg="Tax rate data inserted successfully!")
    except DatabaseError as e:
        # Handle database errors, e.g., connection issues, syntax errors, etc.
        api_log(msg=f"Database error: {e}")
    except IntegrityError as e:
        # Handle integrity errors, e.g., duplicate key, invalid data, etc.
        api_log(msg=f"Integrity error: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        api_log(msg=f"Unexpected error: {e}")


def save_tax_rate(org_id: str, erp_link_token: str):
    """
    Hlper query to save the Sage tax rate as in-progress in ERPlogs table
    """
    try:
        existing_sage_tax_rate_log = ERPLogs.objects.filter(org_id=org_id, link_token_id=erp_link_token, label="SAGE TAX RATE").first()
        api_log(msg=f"existing data for sage tax rates from erp_sync_logs table:: {existing_sage_tax_rate_log}")
        if not existing_sage_tax_rate_log:
            api_log(msg=f"There is no sage tax rates for erp link token ID:: {erp_link_token}")
            # If no such record exists, create a new one
            tax_rate_save = ERPLogs(
                id=uuid.uuid4(),
                org_id=org_id,
                link_token_id=erp_link_token,
                link_token=erp_link_token,
                label="SAGE TAX RATE",
                sync_start_time=timezone.now(),
                sync_end_time=timezone.now(),
                sync_type="sync",
                sync_status="in progress",
            ).save()

            api_log(msg=f"saved tax rate status details to erp_sync_logs table ::{tax_rate_save}")
        api_log(msg=f"inserted tax rates module to erp sync log table for erp link token ID:: {erp_link_token}")

    except Exception as e:
        api_log(msg=f"Error saving ERPLogs: Sage TAX RATES:{str(e)}")
