import uuid
from datetime import timezone, datetime
from threading import Thread

from django.db import connection
from django.http import HttpRequest

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from INVOICES.views import MergeInvoiceCreate
from LINKTOKEN.merge_sync_log_model import MergeSyncLog
from LINKTOKEN.model import ErpLinkToken
from LINKTOKEN.queries import (
    get_erp_link_token,
    store_daily_or_force_sync_log,
    store_erp_daily_sync_logs,
    daily_or_force_sync_log,
)
from SYNC.helper_function import log_sync_status, sync_modules_status
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log


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


def sage_module_sync(integration_slug):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT module_name 
            FROM erp_modules_setting 
            WHERE integration_name = %s
        """,   [integration_slug]
        )
        module_row = cursor.fetchall()
        module_list = [row[0] for row in module_row]
        return module_list


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

        # add a entry for initial sync
        daily_or_force_sync = store_daily_or_force_sync_log(
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

        api_log(
            msg=f"WEBHOOK: Inserting sync log table for in progress for erp_data {erp_data}"
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

            store_erp_daily_sync_logs(
                {
                    "org_id": erp_data.org_id,
                    "link_token_id": erp_data.id,
                    "daily_or_force_sync_log_id": daily_or_force_sync.id,
                    "link_token": erp_data.account_token,
                    "label": module,
                    "sync_start_time": datetime.now(tz=timezone.utc),
                    "sync_end_time": None,
                    "sync_status": "in_progress",
                    "error_message": None,
                }
            )

        api_log(msg="WEBHOOK: Sync log table inserted successfully")

    except Exception as e:
        # Handle the case where the record does not exist
        api_log(msg=f"WEBHOOK: Exception occurred: in handle_webhook_link_account {e}")


def webhook_sync_modul_filter(module_name_merge):
    label_name = None
    if module_name_merge == "TaxRate":
        label_name = "TAX RATE"
    if module_name_merge == "TrackingCategory":
        label_name = "TRACKING CATEGORIES"
    if module_name_merge == "CompanyInfo":
        label_name = "COMPANY INFO"
    if module_name_merge == "Account":
        label_name = "ACCOUNTS"
    if module_name_merge == "Contact":
        label_name = "CONTACTS"
    if module_name_merge == "Invoice":
        label_name = "INVOICES"
    return label_name


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

            api_log(msg=f"WEBHOOK: response_data object {response_data} start")

            if response_data.status == "in_progress":
                # store the initial sync data
                store_initial_sync(linked_account_data, account_token_data)
            else:
                # store daily sync data
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
    try:
        erp_link_token_id = linked_account_data.get("end_user_origin_id")
        sync_status_data = account_token_data.get("sync_status")
        merge_module_name = sync_status_data.get("model_name")

        api_log(msg=f"WEBHOOK: Merge sync insert {erp_link_token_id} object  start")
        MergeSyncLog.objects.get_or_create(
            link_token_id=erp_link_token_id,
            defaults={
                "id": uuid.uuid1(),
                "module_name": merge_module_name,
                "link_token_id": erp_link_token_id,
                "end_user_origin_id": erp_link_token_id,
                "status": sync_status_data.get("status"),
                "sync_type": "sync",
                "account_type": linked_account_data.get("account_type"),
            },
        )

        erp_data = ErpLinkToken.objects.filter(id=erp_link_token_id).first()
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
        }
        custom_request = HttpRequest()
        custom_request.method = "POST"
        custom_request.data = {
            "erp_link_token_id": erp_data.id,
            "org_id": erp_data.org_id,
        }

        api_log(msg="WEBHOOK: Thread started")
        integration_name = account_token_data["integration_name"]

        sync_module_list = []
        if integration_name == "Sage Intacct" and merge_module_name == "Invoice":
            sync_module_list.append(api_views["Contact"])
            sync_module_list.append(api_views["TrackingCategory"])
        sync_module_list.append(api_views[merge_module_name])
        api_log(msg=f"WEBHOOK:: Total module syncing: {sync_module_list}")
        thread = Thread(
            target=sync_modules_status,
            args=(
                custom_request,
                erp_data.org_id,
                erp_data.id,
                erp_data.account_token,
                sync_module_list,
            ),
        )

        thread.start()
        api_log(msg="WEBHOOK: Thread started successfully")
    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in store_initial_sync {e}")


def store_daily_sync(linked_account_data: dict, account_token_data: dict):
    """
    Function to store the daily sync data
    """
    try:
        erp_link_token_id = linked_account_data.get("end_user_origin_id")
        erp_data = get_erp_link_token(erp_link_token_id)
        merge_module_name = account_token_data.get("sync_status").get("model_name")

        # check if record exists for daily sync
        daily_sync_data = daily_or_force_sync_log(
            {
                "link_token_id": erp_link_token_id,
                "is_initial_sync": False,
                "status": "in_progress",
            }
        )
        if not daily_sync_data:
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

            modules = [
                "TAX RATE",
                "TRACKING CATEGORIES",
                "COMPANY INFO",
                "ACCOUNTS",
                "CONTACTS",
                "INVOICES",
            ]

            for module in modules:
                api_log(
                    msg=f"WEBHOOK: insert sync log table for in progress: {module} in progress"
                )

                store_erp_daily_sync_logs(
                    {
                        "org_id": erp_data.org_id,
                        "link_token_id": erp_data.id,
                        "daily_or_force_sync_log_id": daily_or_force_sync.id,
                        "link_token": erp_data.account_token,
                        "label": module,
                        "sync_start_time": datetime.now(tz=timezone.utc),
                        "sync_end_time": None,
                        "sync_status": "in_progress",
                        "error_message": None,
                    }
                )

        # start thread
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
        }
        custom_request = HttpRequest()
        custom_request.method = "POST"
        custom_request.data = {
            "erp_link_token_id": erp_data.id,
            "org_id": erp_data.org_id,
        }

        api_log(msg="WEBHOOK: Thread started")
        integration_name = account_token_data["integration_name"]

        sync_module_list = []
        if integration_name == "Sage Intacct" and merge_module_name == "Invoice":
            sync_module_list.append(api_views["Contact"])
            sync_module_list.append(api_views["TrackingCategory"])
        sync_module_list.append(api_views[merge_module_name])
        api_log(msg=f"WEBHOOK:: Total module syncing: {sync_module_list}")
        thread = Thread(
            target=sync_modules_status,
            args=(
                custom_request,
                erp_data.org_id,
                erp_data.id,
                erp_data.account_token,
                sync_module_list,
                False,
            ),
        )

        thread.start()
        api_log(msg="WEBHOOK: Thread started successfully")

    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in store_daily_sync {e}")
