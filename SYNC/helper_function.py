import time
import uuid
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.exceptions import APIException

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from INVOICES.views import MergeInvoiceCreate
from LINKTOKEN.queries import (
    daily_or_force_sync_log,
    update_erp_daily_sync_logs,
    erp_daily_sync_logs,
    update_daily_or_force_sync_log,
)
from SYNC.models import ERPLogs
from SYNC.queries import get_erplogs_by_link_token_id
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log
from services.merge_service import MergeSyncService


def start_failed_sync_process(request, erp_link_token_id, org_id, account_token):
    """
    Starts the sync process.
    """

    api_log(
        msg=f"SYNC helper1 : Starting the sync process account_token {account_token}"
    )

    try:
        api_log(msg="SYNC : Checking the status of the modules")
        # sleep for 30 seconds

        merge_client = MergeSyncService(account_token)
        sync_status_response = merge_client.sync_status()

        if not sync_status_response["status"]:
            api_log(msg="SYNC : Sync Status is not available")
            return

        # Check if all modules are done syncing
        sync_status_result = sync_status_response["data"].results
        api_log(msg=f"SYNC HELPER 2: This is sync status result: {sync_status_result}")
        modules = [
            "TrackingCategory",
            "CompanyInfo",
            "Account",
            "Contact",
            "TaxRate",
            "Invoice",
        ]
        sync_module_status = []
        api_log(msg=f"SYNC HELPER 2: These are the modules: {modules}")
        for module in modules:
            for sync_filter_array in sync_status_result:
                if sync_filter_array.model_name == module:
                    api_log(
                        msg=f"SYNC :sync_filter_array {sync_filter_array.model_name} and {sync_filter_array.status}"
                    )
                    if sync_filter_array.status == "DONE":
                        sync_module_status.append(sync_filter_array.model_name)

                    if sync_filter_array.status in ["FAILED", "PARTIALLY_SYNCED"]:
                        api_log(
                            msg=f"SYNC :Syncing module {module} is failed from merge"
                        )

        api_log(msg=f"SYNC :Current Sync Modules {sync_module_status}")

        # check if the logs are present in the database
        response_data = get_erplogs_by_link_token_id(erp_link_token_id)
        api_log(msg=f"SYNC :ERP Log Data {response_data}")
        api_views = {
            "TRACKING CATEGORIES": (
                MergePostTrackingCategories,
                {"link_token_details": account_token},
            ),
            "COMPANY INFO": (
                MergeKlooCompanyInsert,
                {"link_token_details": account_token},
            ),
            "ACCOUNTS": (InsertAccountData, {"link_token_details": account_token}),
            "CONTACTS": (
                MergePostContacts,
                {"link_token_details": account_token},
            ),
            "TAX RATE": (
                MergePostTaxRates,
                {"link_token_details": account_token},
            ),
            "INVOICES": (
                MergeInvoiceCreate,
                {"link_token_details": account_token},
            ),
        }

        link_token_details = api_views["ACCOUNTS"][1]["link_token_details"]
        api_log(
            msg=f"SYNC HELPER4: LINK OTKN DETAILS OF ACCOUNTS: {link_token_details}"
        )
        # if logs are present check if any module is failed
        post_api_views = []
        if response_data:
            for log in response_data:
                if log["sync_status"] in ["failed", "in progress"]:
                    post_api_views.append(api_views[log["label"]])

            # if all modules are successfully return the response
            if not post_api_views:
                api_log(msg="SYNC : All modules are already successfully synced")
                return

        # if logs are not present then add all the modules to the post_api_views
        if not post_api_views:
            api_log(msg="SYNC : Logs are not present syncing all modules")
            post_api_views = list(api_views.values())

        api_log(msg=f"SYNC :post_api_views {post_api_views}")
        sync_modules_status(
            request,
            org_id,
            erp_link_token_id,
            account_token,
            post_api_views,
        )

        # Return the combined response and response_data dictionary
        api_log(
            msg=f"SYNC : All modules are successful AND following sync module status: {sync_modules_status}"
        )
    except Exception:
        api_log(msg="SYNC : Exception for model")
        return


def sync_modules_status(
    request,
    org_id,
    erp_link_token_id,
    account_token,
    post_api_views,
    initial_sync=True,
):
    """
    Syncs the status of the different modules with the ERP system.
    """

    time.sleep(15)
    for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
        try:
            api_call(
                request,
                api_view_class,
                kwargs,
                org_id,
                erp_link_token_id,
                account_token,
                initial_sync,
            )
        except Exception:
            api_log(msg=f"SYNC : Exception for model {api_view_class}")
            return

    api_log(msg="SYNC COMPLETED")


def api_call(
    request,
    api_view_class,
    kwargs,
    org_id,
    erp_link_token_id,
    account_token,
    initial_sync,
):
    module_name = api_view_class.__module__
    if module_name.endswith(".views"):
        module_name = module_name[:-6]

    model_name = module_name.replace("_", " ")

    api_log(msg=f"SYNC : model name is: {module_name} has started")
    try:
        api_instance = api_view_class(**kwargs)
        response = api_instance.post(request)
        api_log(msg=f"SYNC : model name is: {module_name}, {response}")
        if response.status_code == status.HTTP_200_OK:
            api_log(msg="SYNC : model name is succsssfull")

            if initial_sync:
                log_sync_status(
                    sync_status="Success",
                    message=f"API {module_name} completed successfully",
                    label=f"{model_name}",
                    org_id=org_id,
                    erp_link_token_id=erp_link_token_id,
                    account_token=account_token,
                )

            update_logs_for_daily_sync(
                erp_link_token_id, "success", f"{model_name}", None
            )
        else:
            api_log(msg=f"SYNC : model name {module_name} is failure")
            error_message = (
                f"API {module_name} failed with status code {response.status_code}"
            )
            api_exception = APIException(error_message)
            raise api_exception
    except Exception as e:
        api_log(msg=f"SYNC : Exception for model {module_name}")
        error_message = f"An error occurred while calling API : {str(e)}"
        if initial_sync:
            log_sync_status(
                sync_status="Failed",
                message=error_message,
                label=f"{model_name}",
                org_id=org_id,
                erp_link_token_id=erp_link_token_id,
                account_token=account_token,
            )
        update_logs_for_daily_sync(
            erp_link_token_id, "failed", f"{model_name}", error_message
        )


def log_sync_status(
    sync_status, message, label, org_id, erp_link_token_id, account_token
):
    api_log(
        msg=f"SYNC : STATUS {sync_status} {message} {label} {org_id} {erp_link_token_id} {account_token}"
    )
    # check if sync status is present , then update the status
    log_entry = ERPLogs.objects.filter(
        link_token_id=erp_link_token_id, label=label, org_id=org_id
    ).first()

    if log_entry:
        log_entry.sync_status = sync_status
        log_entry.sync_end_time = datetime.now(tz=timezone.utc)
        log_entry.error_message = message
        log_entry.save()
        api_log(msg=f"SYNC : STATUS UPDATED {log_entry}")
        return
    # Log the error to the database
    log_entry_create = ERPLogs(
        id=uuid.uuid1(),
        org_id=org_id,
        link_token_id=erp_link_token_id,
        link_token=account_token,
        label=label,
        sync_start_time=datetime.now(tz=timezone.utc),
        sync_end_time=datetime.now(tz=timezone.utc),
        sync_status=sync_status,
        error_message=message,
    )
    log_entry_create.save()
    api_log(msg=f"SYNC : STATUS {log_entry}")


def update_logs_for_daily_sync(
    erp_link_token_id: str, status: str, model: str, error_message: str = None
):
    try:
        api_log(msg="SYNC : Update logs for daily Sync")

        # get the latest log record from daily or force sync log
        daily_sync_log = daily_or_force_sync_log(
            {
                "link_token_id": erp_link_token_id,
                "status": "in_progress",
                "end_date": None,
            }
        )

        if not daily_sync_log:
            api_log(
                msg=f"SYNC : Daily or force sync log not found for link token {erp_link_token_id}"
            )
            return

        api_log(msg=f"SYNC : Daily or force sync log found {daily_sync_log.id}")

        # now update the erp daily sync logs model
        update_erp_daily_sync_logs(
            {
                "link_token_id": daily_sync_log.link_token_id,
                "daily_or_force_sync_log_id": daily_sync_log.id,
                "label": model,
            },
            {
                "sync_status": status,
                "label": model,
                "sync_end_time": datetime.now(tz=timezone.utc),
                "error_message": error_message,
            },
        )

        api_log(msg=f"SYNC : Updated erp daily sync logs for {model}")

        # now check if all modules are completed ( success or failed )
        daily_sync_logs = erp_daily_sync_logs(
            {
                "link_token_id": daily_sync_log.link_token_id,
                "daily_or_force_sync_log_id": daily_sync_log.id,
                "sync_status": "in_progress",
            }
        )

        api_log(msg=f"SYNC : Daily sync logs {daily_sync_logs}")

        if not daily_sync_logs:
            api_log(
                msg=f"SYNC : All modules are completed for link token {erp_link_token_id}"
            )
            # update the daily or force sync log
            update_daily_or_force_sync_log(
                {
                    "id": daily_sync_log.id,
                },
                {"status": "success", "end_date": datetime.now(tz=timezone.utc)},
            )

        api_log(msg=f"SYNC : Updated daily or force sync log for {erp_link_token_id}")

    except Exception as e:
        api_log(msg=f"WEBHOOK: Exception occurred: in update_logs_for_daily_sync {e}")
        return
