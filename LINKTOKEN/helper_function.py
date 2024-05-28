"""
This module contains the helper functions for the sync process.
"""

import time
import uuid
from datetime import timezone, datetime, timedelta
from threading import Thread

from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from INVOICES.views import MergeInvoiceCreate
from ITEMS.views import MergeItemCreate
from LINKTOKEN.merge_sync_log_model import MergeSyncLog
from LINKTOKEN.model import ErpLinkToken, ErpDailySyncLogs
from LINKTOKEN.queries import (
    get_erp_link_token,
    store_daily_or_force_sync_log,
    store_erp_daily_sync_logs,
    daily_or_force_sync_log,
    sage_module_sync,
)
from LINKTOKEN.utils import webhook_sync_modul_filter
from SYNC.helper_function import (
    log_sync_status,
    start_sync_process,
    start_sync_process_sage,
)
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log
from sqs_utils.sqs_manager import send_slack_notification


def validate_webhook(payload):
    """
    Function to validate the webhook
    """
    api_log(msg="WEBHOOK: Webhook validated successfully")

    linked_account_data = payload.get("linked_account", None)
    account_token_data = payload.get("data")
    end_user_origin_id = linked_account_data.get("end_user_origin_id")

    erp_link_token_exists = get_erp_link_token(erp_link_token_id=end_user_origin_id)
    if erp_link_token_exists is None:
        api_log(
            msg=f"WEBHOOK: Erp link token does not exist for {end_user_origin_id}"
            f" in this environment"
        )
        return {
            "status": False,
            "message": "WEBHOOK: Erp link token does not exist",
        }

    event = payload.get("hook").get("event")
    if account_token_data.get(
        "integration_name"
    ) == "Sage Intacct" and "synced" in event.split("."):
        if account_token_data.get("sync_status").get("model_name") != "Account":
            return {
                "status": False,
                "message": "WEBHOOK: Webhook event not found",
            }
        daily_or_force_sync = daily_or_force_sync_log(
            {
                "link_token_id": end_user_origin_id,
                "is_initial_sync": True,
                "status": "success",
            }
        )

        if not daily_or_force_sync:
            api_log(
                msg=f"WEBHOOK: No initial sync record found for {end_user_origin_id}"
            )
            return {
                "status": False,
                "message": "WEBHOOK: No initial sync record found",
            }

        api_log(msg="WEBHOOK: No proper event for sage intacct")
        return {
            "status": True,
            "message": "WEBHOOK: Sage Intacct event found",
        }

    return {
        "status": True,
        "message": "WEBHOOK: Webhook validated successfully",
    }


def get_org_entity(organization_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT
        soe.id
        FROM organization_configurations soc1
        JOIN organization_entity_details soe ON soe.organization_configurations_id = soc1.id
        WHERE 1 = 1
        AND soc1.organization_id = %s
        AND soc1.config_key_name = 'org_entities'
        AND soe.deleted_at IS NULL
        ORDER BY CASE WHEN soe.status = 'default' THEN 0 ELSE 1 END, soe.id ASC""",
            [organization_id],
        )
        row = cursor.fetchone()
        return row


def create_erp_link_token(request):
    link_token_record = ErpLinkToken(**request)

    link_token_record.save()
    return link_token_record


def get_linktoken(org_id, status, end_user_email_address):
    filter_token = ErpLinkToken.objects.filter(
        org_id=org_id, status=status, end_user_email_address=end_user_email_address
    )

    if not filter_token:
        return {"is_available": 0}

    first_token = filter_token.first()
    timestamp = first_token.created_at.replace(tzinfo=timezone.utc)
    current_time = datetime.now(tz=timezone.utc)
    time_difference = current_time - timestamp
    difference_in_minutes = time_difference.total_seconds() / 60
    if first_token and difference_in_minutes < first_token.link_expiry_mins:
        data = {
            "link_token": first_token.link_token,
            "magic_link_url": first_token.magic_link_url,
            "integration_name": first_token.integration_name,
            "timestamp": timestamp,
            "is_available": 1,
        }
        return data
    else:
        return {"is_available": 0}


def handle_webhook_link_account(linked_account_data: dict, account_token_data: dict):
    """
    Function to handle the webhook data for the linked account
    """
    try:
        ErpLinkToken.objects.filter(
            id=linked_account_data.get("end_user_origin_id")
        ).update(
            integration_name=linked_account_data.get("integration"),
            magic_link_url=linked_account_data.get("webhook_listener_url"),
            categories=linked_account_data.get("category"),
            platform=linked_account_data.get("account_type"),
            account_token=account_token_data.get("account_token"),
            end_user_email_address=linked_account_data.get("end_user_email_address"),
            end_user_organization_name=linked_account_data.get(
                "end_user_organization_name"
            ),
            link_expiry_mins=60,
            should_create_magic_link_url=False,
            status=linked_account_data.get("status"),
        )

        integration_slug = linked_account_data.get("integration_slug")
        modules = sage_module_sync(integration_slug)

        erp_link_token_id = linked_account_data.get("end_user_origin_id")
        erp_data = get_erp_link_token(erp_link_token_id)

        # add entry for initial sync
        store_daily_or_force_sync_log(
            {
                "link_token_id": erp_link_token_id,
                "sync_type": "daily_sync",
                "status": "in_progress",
                "sync_date": datetime.now(tz=timezone.utc),
                "start_date": datetime.now(tz=timezone.utc),
                "end_date": None,
                "is_initial_sync": True,
            }
        )

        for module in modules:
            api_log(
                msg=f"WEBHOOK: insert sync log table for in progress: {module} in progress"
            )
            log_sync_status(
                sync_status="in progress",
                message=f"API {module} executed successfully",
                label=module,
                org_id=erp_data.org_id,
                erp_link_token_id=erp_data.id,
                account_token=erp_data.account_token,
            )

        # start pooling for sage intacct integration
        # since sync status webhook are not reliable
        if linked_account_data.get("integration") == "Sage Intacct":
            account_token_data = {
                "sync_status": {
                    "last_sync_finished": datetime.now(tz=timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "last_sync_start": datetime.now(tz=timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "model_name": "Account",
                },
            }

            handle_webhook_sync_modules(linked_account_data, account_token_data)

        api_log(msg="WEBHOOK: Sync log table inserted successfully")

    except Exception as e:
        # Handle the case where the record does not exist
        api_log(msg=f"WEBHOOK: Exception occurred: in handle_webhook_link_accounts {e}")


def handle_webhook_sync_modules(linked_account_data: dict, account_token_data: dict):
    """
    Function to handle the webhook data for the sync modules
    """
    try:
        sync_status_data = account_token_data.get("sync_status")
        if sync_status_data is not None:
            response_data = daily_or_force_sync_log(
                {
                    "link_token_id": linked_account_data.get("end_user_origin_id"),
                    "is_initial_sync": True,
                }
            )

            api_log(
                msg=f"WEBHOOK: Initial Sync Object {response_data.id} is in status {response_data.status}"
            )

            if response_data.status == "in_progress":
                # store the initial sync data
                msg = f"WEBHOOK: Start initial sync {account_token_data.get('account_token')}"
                send_slack_notification(msg)
                store_initial_sync(linked_account_data, account_token_data)
            else:
                # store daily sync data
                msg = f"daily sync started: {account_token_data.get('account_token')}"
                send_slack_notification(msg)
                store_daily_sync(linked_account_data, account_token_data)

        else:
            api_log(
                msg=f"WEBHOOK: No Sync data received for account token {account_token_data.get('account_token')}"
            )

    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in handle_webhook_sync_modules {e}")


def store_initial_sync(linked_account_data: dict, account_token_data: dict):
    """
    Function to store the initial sync data
    """

    api_log(
        msg=f"WEBHOOK: Start initial sync {linked_account_data.get('end_user_origin_id')}"
    )
    initial_sync = f"WEBHOOK: Start initial sync {linked_account_data.get('end_user_origin_id')}"
    send_slack_notification(initial_sync)

    try:
        erp_link_token_id = linked_account_data.get("end_user_origin_id")
        sync_status_data = account_token_data.get("sync_status")
        merge_module_name = sync_status_data.get("model_name")
        integration_name = linked_account_data.get("integration")

        modules = []
        if integration_name == "Sage Intacct" and merge_module_name == "Account":
            modules.append("Contact")
            modules.append("TrackingCategory")
            modules.append("Invoice")
            modules.append("CompanyInfo")
            modules.append("Item")

        modules.append(merge_module_name)

        api_log(msg=f"WEBHOOK: Merge sync insert {erp_link_token_id} object  start")

        for module in modules:
            MergeSyncLog.objects.get_or_create(
                link_token_id=erp_link_token_id,
                defaults={
                    "id": uuid.uuid1(),
                    "module_name": module,
                    "link_token_id": erp_link_token_id,
                    "end_user_origin_id": erp_link_token_id,
                    "status": sync_status_data.get("status"),
                    "sync_type": "sync",
                    "account_type": linked_account_data.get("account_type"),
                },
            )

        erp_data = ErpLinkToken.objects.filter(id=erp_link_token_id).first()

        # check if record exists for daily sync
        daily_or_force_sync = daily_or_force_sync_log(
            {
                "link_token_id": erp_link_token_id,
                "is_initial_sync": True,
                "status": "in_progress",
            }
        )
        api_log(
            msg=f"WEBHOOK: Inserting sync log table for in progress for erp_data {erp_data}"
        )

        insert_sync = f"WEBHOOK: Inserting sync log table for in progress for erp_data {erp_data}"
        send_slack_notification(insert_sync)
        for module in modules:
            api_log(
                msg=f"WEBHOOK: insert sync log table for in progress: {module} in progress"
            )
            module_name = webhook_sync_modul_filter(module)

            # add one second to the sync end time to avoid duplicate records
            sync_end_time = (
                datetime.strptime(
                    account_token_data.get("sync_status").get("last_sync_finished"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                + timedelta(seconds=1)
            ).astimezone(timezone.utc)
            store_erp_daily_sync_logs(
                {
                    "org_id": erp_data.org_id,
                    "link_token_id": erp_data.id,
                    "daily_or_force_sync_log_id": daily_or_force_sync.id,
                    "link_token": erp_data.account_token,
                    "label": module_name,
                    "sync_start_time": account_token_data.get("sync_status").get(
                        "last_sync_start"
                    ),
                    "sync_end_time": sync_end_time,
                    "sync_status": "in_progress",
                    "error_message": None,
                }
            )

        api_views = {
            "TrackingCategory": (
                MergePostTrackingCategories,
                {"link_token_details": erp_data.account_token},
            ),
            "CompanyInfo": (
                MergeKlooCompanyInsert,
                {"link_token_details": erp_data.account_token},
            ),
            "Account": (
                InsertAccountData,
                {"link_token_details": erp_data.account_token},
            ),
            "Contact": (
                MergePostContacts,
                {"link_token_details": erp_data.account_token},
            ),
            "Invoice": (
                MergeInvoiceCreate,
                {"link_token_details": erp_data.account_token},
            ),
            "TaxRate": (
                MergePostTaxRates,
                {"link_token_details": erp_data.account_token},
            ),
            "Item": (
                MergeItemCreate,
                {"link_token_details": erp_data.account_token},
            ),
        }
        custom_request = HttpRequest()
        custom_request.method = "POST"
        custom_request.data = {
            "erp_link_token_id": erp_data.id,
            "org_id": erp_data.org_id,
        }

        api_log(msg="WEBHOOK: Thread started")
        integration_name_msg = f"Integration Name: {integration_name}"
        send_slack_notification(integration_name_msg)
        api_log(msg=f"WEBHOOK:: Total module syncing: {modules}")
        total_module_sync = f"WEBHOOK:: Total module syncing: {modules}"
        send_slack_notification(total_module_sync)
        if integration_name == "Sage Intacct":
            for module in modules:
                thread = Thread(
                    target=start_sync_process_sage,
                    args=(
                        custom_request,
                        erp_data.org_id,
                        erp_data.id,
                        daily_or_force_sync.id,
                        erp_data.account_token,
                        [module],
                        api_views,
                    ),
                )

                thread.start()

        if integration_name == "Xero":
            thread = Thread(
                target=start_sync_process,
                args=(
                    custom_request,
                    erp_data.org_id,
                    erp_data.id,
                    erp_data.account_token,
                    modules,
                    api_views,
                ),
            )

            thread.start()
        api_log(msg="WEBHOOK: Thread started successfully")
        thread_sync = "WEBHOOK: Thread started successfully"
        send_slack_notification(thread_sync)
    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in store_initial_sync {e}")
        thread_error_sync = f"WEBHOOK: Exception occurred: in store_initial_sync {e}"
        send_slack_notification(thread_error_sync)


def store_daily_sync(linked_account_data: dict, account_token_data: dict):
    """
    Function to store the daily sync data
    """
    api_log(
        msg=f"WEBHOOK: Start Daily sync {linked_account_data.get('end_user_origin_id')}"
    )


    try:
        erp_link_token_id = linked_account_data.get("end_user_origin_id")
        erp_data = get_erp_link_token(erp_link_token_id)
        merge_module_name = account_token_data.get("sync_status").get("model_name")
        integration_name = linked_account_data.get("integration")

        # check if cache has the key for webhook sync
        if cache.get(f"webhook_sync_{erp_link_token_id}"):
            api_log(msg="WEBHOOK: Webhook sync already in progress")
            time.sleep(5)

        cache.set(f"webhook_sync_{erp_link_token_id}", True)

        # check if record exists for daily sync
        daily_or_force_sync = daily_or_force_sync_log(
            {
                "link_token_id": erp_link_token_id,
                "is_initial_sync": False,
                "status": "in_progress",
            }
        )
        if not daily_or_force_sync:
            # create a new entry for daily or force sync log
            daily_or_force_sync = store_daily_or_force_sync_log(
                {
                    "link_token_id": erp_link_token_id,
                    "sync_type": "daily_sync",
                    "status": "in_progress",
                    "sync_date": datetime.now(tz=timezone.utc),
                    "start_date": datetime.now(tz=timezone.utc),
                    "end_date": None,
                    "is_initial_sync": False,
                }
            )

        # delete the cache key
        cache.delete(f"webhook_sync_{erp_link_token_id}")

        modules = []
        if integration_name == "Sage Intacct" and merge_module_name == "Account":
            modules.append("Contact")
            modules.append("TrackingCategory")
            modules.append("Invoice")
            modules.append("CompanyInfo")
            modules.append("Item")

        modules.append(merge_module_name)

        last_modified_dates = {}
        for module in modules:
            module_name = webhook_sync_modul_filter(module)
            api_log(
                msg=f"WEBHOOK: insert sync log table for in progress: {module_name} in progress"
            )

            # add one second to the sync end time to avoid duplicate records
            sync_end_time = (
                datetime.strptime(
                    account_token_data.get("sync_status").get("last_sync_finished"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                + timedelta(seconds=1)
            ).astimezone(timezone.utc)

            store_erp_daily_sync_logs(
                {
                    "org_id": erp_data.org_id,
                    "link_token_id": erp_data.id,
                    "daily_or_force_sync_log_id": daily_or_force_sync.id,
                    "link_token": erp_data.account_token,
                    "label": module_name,
                    "sync_start_time": account_token_data.get("sync_status").get(
                        "last_sync_start"
                    ),
                    "sync_end_time": sync_end_time,
                    "sync_status": "in_progress",
                    "error_message": None,
                }
            )

            # now get all the modules with daily sync id
            # query to check if status is no content or success
            erp_sync_logs = ErpDailySyncLogs.objects.filter(
                link_token_id=erp_link_token_id,
                label=module_name,
                sync_status__in=["no_content", "success"],
            ).order_by("-sync_start_time")

            api_log(
                msg=f"WEBHOOK: Inserting sync log table for in progress for erp_data {erp_data}"
            )

            if erp_sync_logs.exists():
                erp_sync_log = erp_sync_logs.first()
                last_modified_dates[erp_sync_log.label] = (
                    erp_sync_log.sync_end_time.astimezone(timezone.utc)
                )
            else:
                last_modified_dates[module_name] = None
            api_log(
                msg=f"WEBHOOK: Last modified date for {module_name} "
                f"is {last_modified_dates[module_name]}"
            )

        # start thread
        api_views = {
            "TrackingCategory": (
                MergePostTrackingCategories,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("TrackingCategory")
                    ),
                },
            ),
            "CompanyInfo": (
                MergeKlooCompanyInsert,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("CompanyInfo")
                    ),
                },
            ),
            "Account": (
                InsertAccountData,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("Account")
                    ),
                },
            ),
            "Contact": (
                MergePostContacts,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("Contact")
                    ),
                },
            ),
            "Invoice": (
                MergeInvoiceCreate,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("Invoice")
                    ),
                },
            ),
            "TaxRate": (
                MergePostTaxRates,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("TaxRate")
                    ),
                },
            ),
            "Item": (
                MergeItemCreate,
                {
                    "link_token_details": erp_data.account_token,
                    "last_modified_at": last_modified_dates.get(
                        webhook_sync_modul_filter("item")
                    ),
                },
            ),
        }
        custom_request = HttpRequest()
        custom_request.method = "POST"
        custom_request.data = {
            "erp_link_token_id": erp_data.id,
            "org_id": erp_data.org_id,
        }

        api_log(msg="WEBHOOK: Thread started")
        webhook_msg = f"WEBHOOK:: Total module syncing: {modules}"
        send_slack_notification(webhook_msg)
        api_log(msg=f"WEBHOOK:: Total module syncing: {modules}")
        if integration_name == "Sage Intacct":
            for module in modules:
                thread = Thread(
                    target=start_sync_process_sage,
                    args=(
                        custom_request,
                        erp_data.org_id,
                        erp_data.id,
                        daily_or_force_sync.id,
                        erp_data.account_token,
                        [module],
                        api_views,
                        False,
                    ),
                )

                thread.start()

        if integration_name == "Xero":
            thread = Thread(
                target=start_sync_process,
                args=(
                    custom_request,
                    erp_data.org_id,
                    erp_data.id,
                    erp_data.account_token,
                    modules,
                    api_views,
                    False,
                ),
            )

            thread.start()

        api_log(msg="WEBHOOK: Thread started successfully")
        webhook_msg_complete = f"WEBHOOK: Thread started successfully"
        send_slack_notification(webhook_msg_complete)
    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in store_daily_sync {e}")
        webhook_error_msg = f"WEBHOOK: Exception occurred: in store_daily_sync {e}"
        send_slack_notification(webhook_error_msg)
