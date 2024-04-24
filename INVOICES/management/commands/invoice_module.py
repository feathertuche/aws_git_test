import uuid
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import connection
from rest_framework import status

from INVOICES.helper_functions import format_merge_invoice_data
from SYNC.models import ERPLogs
from merge_integration.helper_functions import api_log
from services.kloo_service import KlooService
from services.merge_service import MergeInvoiceApiService


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts
    """

    help = "Add Invoice Module for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        print("Adding Invoice Module for all completed linked accounts")
        # get all linked account whose status are complete and Invoice Module is not in master sync
        query = """SELECT
                        erp_link_token.id,
                        erp_link_token.org_id,
                        erp_sync_logs.link_token,
                        erp_link_token.account_token
                    FROM erp_link_token
                    JOIN erp_sync_logs
                    ON erp_link_token.id = erp_sync_logs.link_token_id
                    COLLATE utf8mb4_unicode_ci
                    WHERE erp_link_token.status = 'COMPLETE'
                    AND erp_sync_logs.label = 'TAX RATE'
                    """
        # execute the query and get the linked accounts
        with connection.cursor() as cursor:
            cursor.execute(query)
            linked_accounts = cursor.fetchall()
        if len(linked_accounts) == 0:
            print("No linked accounts found")
            return
        api_log(msg=f"Total Linked Accounts: {len(linked_accounts)}")
        for linked_account in linked_accounts:
            erp_log = None
            try:
                # get the linked account details
                erp_linked_account_id = linked_account[0]
                api_log(msg=f"Linked Account ID: {erp_linked_account_id}")
                # chec if this account have INVOICE in erp_sync_logs
                query = f"""SELECT
                                  id
                              FROM erp_sync_logs
                              WHERE link_token_id = '{erp_linked_account_id}'
                              AND label = 'INVOICES'
                              """
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    invoice_module = cursor.fetchone()
                if invoice_module:
                    api_log(
                        msg=f"INVOICE Module already exists for {erp_linked_account_id}"
                    )
                    continue
                # add INVOICE module to this account
                api_log(msg=f"Adding INVOICE Module to {erp_linked_account_id}")
                # insert the record in erp_sync_logs
                ERPLogs(
                    id=uuid.uuid4(),
                    org_id=linked_account[1],
                    link_token_id=erp_linked_account_id,
                    link_token=linked_account[2],
                    label="INVOICES",
                    sync_start_time=datetime.now(tz=timezone.utc),
                    sync_end_time=datetime.now(tz=timezone.utc),
                    sync_type="sync",
                    sync_status="in progress",
                ).save()
                erp_log = ERPLogs.objects.get(
                    link_token_id=erp_linked_account_id, label="INVOICES"
                )
                api_log(msg=f"INVOICE Module added to {erp_linked_account_id}")
                # fetch the invoices for this account
                account_token = linked_account[3]
                merge_invoice_api_service = MergeInvoiceApiService(account_token)
                invoice_response = merge_invoice_api_service.get_invoices()
                if invoice_response["status"]:
                    api_log(
                        msg=f"INVOICE : Processing {len(invoice_response['data'])} invoices"
                    )
                    if len(invoice_response["data"]) == 0:
                        api_log(
                            msg="No new data found to insert in the kloo Invoice system"
                        )
                        erp_log.sync_status = "no_content"
                        erp_log.error_message = (
                            "No new data found to insert in the kloo Invoice system"
                        )
                        erp_log.sync_end_time = datetime.now(tz=timezone.utc)
                        erp_log.save()
                        continue
                    batch_size = 300
                    # batch_data = []
                    for i in range(0, len(invoice_response["data"]), batch_size):
                        batch_data = invoice_response["data"][i : i + batch_size]
                        # format the data to be posted to kloo
                        # invoices_json = format_merge_invoice_data(
                        #     batch_data, erp_link_token_id, org_id
                        # )
                        # format the data to be posted to kloo
                        invoices_json = format_merge_invoice_data(
                            batch_data, erp_linked_account_id, linked_account[1]
                        )
                        # save the data to the database
                        api_log(msg=f"Invoices batch {i} saving to database")
                        kloo_service = KlooService(
                            auth_token=None,
                            erp_link_token_id=erp_linked_account_id,
                        )
                        invoice_kloo_response = kloo_service.post_invoice_data(
                            invoices_json
                        )
                        api_log(
                            msg=f"Response from kloo for batch {i} is {invoice_kloo_response}"
                        )
                    if invoice_kloo_response["status_code"] == status.HTTP_201_CREATED:
                        api_log(
                            msg="data inserted successfully in the kloo Invoice system"
                        )
                        # update the sync status to success
                        erp_log.sync_status = "success"
                        erp_log.error_message = (
                            "API INVOICES Info completed successfully"
                        )
                        erp_log.sync_end_time = datetime.now(tz=timezone.utc)
                        erp_log.save()
                    else:
                        api_log(msg="Failed to send data to Kloo Contacts API")
                        # update the sync status to failed
                        erp_log.sync_status = "failed"
                        erp_log.error_message = (
                            "Failed to send data to Kloo Contacts API"
                        )
                        erp_log.sync_end_time = datetime.now(tz=timezone.utc)
                        erp_log.save()
            except Exception as e:
                api_log(
                    msg=f"Failed to add INVOICE Module to {linked_account}. Error: {str(e)}"
                )
                erp_log.sync_status = "failed"
                erp_log.error_message = f"Failed to add INVOICE Module. Error: {str(e)}"
                erp_log.sync_end_time = datetime.now(tz=timezone.utc)
                erp_log.save()
                continue
