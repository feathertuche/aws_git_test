import time
import uuid
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import APIException

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
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

    api_log(msg=f"SYNC : Starting the sync process account_token {account_token}")

    try:
        while True:
            api_log(msg="SYNC : Checking the status of the modules")
            # sleep for 30 seconds
            api_log(msg="SYNC : Sleeping for 60 seconds")
            time.sleep(60)
            api_log(msg="SYNC : Waking up")

            merge_client = MergeSyncService(account_token)
            sync_status_response = merge_client.sync_status()

            if not sync_status_response["status"]:
                api_log(msg="SYNC : Sync Status is not available")
                break

            # Check if all modules are done syncing
            sync_status_result = sync_status_response["data"].results
            modules = [
                "TrackingCategory",
                "CompanyInfo",
                "Account",
                "Contact",
                "TaxRate",
            ]
            sync_module_status = []
            api_log(msg=f"SYNC :sync_module_status {sync_module_status}")
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
                            sync_module_status.append(sync_filter_array.model_name)

            api_log(msg=f"SYNC :Current Sync Modules {sync_module_status}")

            # Check if all modules are synced
            if set(modules) == set(sync_module_status):
                api_log(
                    msg="SYNC : All modules are synced, starting the fetching process"
                )
                break

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
        }

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
        api_log(msg="SYNC : All modules are successfull")
    except Exception:
        api_log(msg="SYNC : Exception for model")
        return


def start_new_sync_process(request, erp_link_token_id, org_id, account_token):
    """
    Starts the sync process.
    """

    api_log(msg=f"SYNC : Starting the sync process account_token {account_token}")

    try:
        modules = [
            "TrackingCategory",
            "CompanyInfo",
            "Account",
            "Contact",
            "TaxRate",
        ]

        api_views = {
            "TrackingCategory": (
                MergePostTrackingCategories,
                {"link_token_details": account_token},
            ),
            "CompanyInfo": (
                MergeKlooCompanyInsert,
                {"link_token_details": account_token},
            ),
            "Account": (InsertAccountData, {"link_token_details": account_token}),
            "Contact": (
                MergePostContacts,
                {"link_token_details": account_token},
            ),
            "TaxRate": (
                MergePostTaxRates,
                {"link_token_details": account_token},
            ),
        }

        modules_copy = modules.copy()

        while True:
            api_log(msg="SYNC : Checking the status of the modules")
            # sleep for 30 seconds
            api_log(msg="SYNC : Sleeping for 60 seconds")
            time.sleep(60)
            api_log(msg="SYNC : Waking up")

            get_erplogs_by_link_token_id(erp_link_token_id)

            merge_client = MergeSyncService(account_token)
            sync_status_response = merge_client.sync_status()

            if not sync_status_response["status"]:
                api_log(msg="SYNC : Sync Status is not available")
                break

            # Check if all modules are done syncing
            sync_status_result = sync_status_response["data"].results
            for module in modules_copy:
                for sync_filter_array in sync_status_result:
                    if sync_filter_array.model_name == module:
                        if sync_filter_array.status == "DONE":
                            api_log(
                                msg=f"SYNC :Syncing module {module} is done, removing from the list"
                            )
                            sync_modules_status(
                                request,
                                org_id,
                                erp_link_token_id,
                                account_token,
                                [api_views[module]],
                            )
                            modules.remove(module)

                        if sync_filter_array.status in ["FAILED", "PARTIALLY_SYNCED"]:
                            api_log(
                                msg=f"SYNC :Syncing module {module} is failed from merge, "
                                f"removing from the list"
                            )
                            log_sync_status(
                                sync_status="Failed",
                                message=f"API {module} failed from merge side",
                                label=module,
                                org_id=org_id,
                                erp_link_token_id=erp_link_token_id,
                                account_token=account_token,
                            )
                            modules.remove(module)

                # assign the latest modules to module copy
                modules_copy = modules.copy()

            # if all modules are synced then break the loop
            if not modules:
                api_log(
                    msg="SYNC : All modules are synced, starting the fetching process"
                )
                break

        # Return the combined response and response_data dictionary
        api_log(msg="SYNC : All modules are successfull")
    except Exception:
        api_log(msg="SYNC : Exception for model")
        return


def sync_modules_status(
    request,
    org_id,
    erp_link_token_id,
    account_token,
    post_api_views,
):
    """
    Syncs the status of the different modules with the ERP system.
    """

    for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
        try:
            api_call(
                request,
                api_view_class,
                kwargs,
                org_id,
                erp_link_token_id,
                account_token,
            )
        except Exception:
            api_log(msg=f"SYNC : Exception for model {api_view_class}")
            return

    api_log(msg="SYNC COMPLETED")


def api_call(request, api_view_class, kwargs, org_id, erp_link_token_id, account_token):
    module_name = api_view_class.__module__
    if module_name.endswith(".views"):
        module_name = module_name[:-6]

    api_log(msg=f"SYNC : model name is: {module_name} has started")
    try:
        api_instance = api_view_class(**kwargs)
        response = api_instance.post(request)
        api_log(msg=f"SYNC : model name is: {module_name}, {response}")
        if response.status_code == status.HTTP_200_OK:
            api_log(msg="SYNC : model name is succsssfull")
            log_sync_status(
                sync_status="Success",
                message=f"API {module_name} completed successfully",
                label=f"{module_name.replace('_', ' ')}",
                org_id=org_id,
                erp_link_token_id=erp_link_token_id,
                account_token=account_token,
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
        log_sync_status(
            sync_status="Failed",
            message=error_message,
            label=f"{module_name.replace('_', ' ')}",
            org_id=org_id,
            erp_link_token_id=erp_link_token_id,
            account_token=account_token,
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
        log_entry.sync_end_time = datetime.now()
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
        sync_start_time=datetime.now(),
        sync_end_time=datetime.now(),
        sync_status=sync_status,
        error_message=message,
    )
    log_entry_create.save()
    api_log(msg=f"SYNC : STATUS {log_entry}")
    return
