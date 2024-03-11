import uuid
from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import APIException

from SYNC.models import ERPLogs
from merge_integration.helper_functions import api_log


def sync_modules_status(
    request,
    link_token_details,
    org_id,
    erp_link_token_id,
    account_token,
    post_api_views,
):
    """
    Syncs the status of the different modules with the ERP system.
    """

    for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
        api_call(
            request,
            api_view_class,
            kwargs,
            org_id,
            erp_link_token_id,
            account_token,
        )

    # threads = []
    # for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
    #     thread = threading.Thread(
    #         target=api_call,
    #         args=(
    #             request,
    #             api_view_class,
    #             kwargs,
    #             org_id,
    #             erp_link_token_id,
    #             account_token,
    #         ),
    #     )
    #     threads.append(thread)
    #     thread.start()
    #
    # for thread in threads:
    #     thread.join()

    api_log(msg=f"SYNC COMPLETED")


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
