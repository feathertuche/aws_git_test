import threading
import uuid
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import APIException

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from SYNC.models import ERPLogs
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log


def sync_modules_status(
    request, link_token_details, org_id, erp_link_token_id, account_token
):
    """
    Syncs the status of the different modules with the ERP system.
    """
    post_api_views = [
        (
            MergePostTrackingCategories,
            {"link_token_details": link_token_details},
        ),
        (
            MergeKlooCompanyInsert,
            {"link_token_details": link_token_details},
        ),
        (InsertAccountData, {"link_token_details": link_token_details}),
        (MergePostContacts, {"link_token_details": link_token_details}),
    ]

    threads = []
    for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
        thread = threading.Thread(
            target=api_call,
            args=(
                request,
                api_view_class,
                kwargs,
                org_id,
                erp_link_token_id,
                account_token,
            ),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    api_log(msg=f"SYNC COMPLETED")


def api_call(request, api_view_class, kwargs, org_id, erp_link_token_id, account_token):
    module_name = api_view_class.__module__
    if module_name.endswith(".views"):
        module_name = module_name[:-6]
    try:
        api_instance = api_view_class(**kwargs)
        response = api_instance.post(request)
        api_log(msg=f"SYNC : model name is: {module_name}, {response.status_code}")
        if response.status_code == status.HTTP_200_OK:
            api_log(msg=f"SYNC : model name is succsssfull")
            log_sync_status(
                sync_status="Success",
                message=f"API {module_name} executed successfully",
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
            label=module_name,
            org_id=org_id,
            erp_link_token_id=erp_link_token_id,
            account_token=account_token,
        )


def log_sync_status(
    sync_status, message, label, org_id, erp_link_token_id, account_token
):
    # Log the error to the database
    log_entry = ERPLogs(
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
    api_log(msg=f"SYNC : STATUS {log_entry}")
    log_entry.save()
