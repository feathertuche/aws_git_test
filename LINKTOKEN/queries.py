"""
Database queries for LINKTOKEN
"""

import uuid

from django.db import DatabaseError

from LINKTOKEN.model import ErpLinkToken, DailyOrForceSyncLog, ErpDailySyncLogs
from merge_integration.helper_functions import api_log


def get_erp_link_token(erp_link_token_id: str):
    """
    Get link token by org_id and entity_id
    """
    erp_link_token = ErpLinkToken.objects.filter(id=erp_link_token_id).first()
    return erp_link_token


def store_daily_or_force_sync_log(payload_data: dict):
    """
    Store daily or force sync log
    """
    try:
        daily_or_force_sync_log = DailyOrForceSyncLog(
            id=uuid.uuid4(),
            link_token_id=payload_data.get("link_token_id"),
            sync_type=payload_data.get("sync_type"),
            status=payload_data.get("status"),
            sync_date=payload_data.get("sync_date"),
            start_date=payload_data.get("start_date"),
            end_date=payload_data.get("end_date"),
            is_initial_sync=payload_data.get("is_initial_sync"),
        )
        daily_or_force_sync_log.save()
        return daily_or_force_sync_log
    except DatabaseError as e:
        api_log(msg=f"Error storing daily or force sync log: {str(e)}")
        raise e


def store_erp_daily_sync_logs(payload_data: dict):
    """
    Store daily sync logs
    """
    try:
        erp_daily_sync_log = ErpDailySyncLogs(
            id=uuid.uuid4(),
            org_id=payload_data.get("org_id"),
            link_token_id=payload_data.get("link_token_id"),
            daily_or_force_sync_log_id=payload_data.get("daily_or_force_sync_log_id"),
            link_token=payload_data.get("link_token"),
            label=payload_data.get("label"),
            sync_start_time=payload_data.get("sync_start_time"),
            sync_end_time=payload_data.get("sync_end_time"),
            sync_status=payload_data.get("sync_status"),
            error_message=payload_data.get("error_message"),
        )
        erp_daily_sync_log.save()
        return erp_daily_sync_log
    except DatabaseError as e:
        api_log(msg=f"Error storing erp daily sync log: {str(e)}")
        raise e


def daily_or_force_sync_log(filters: dict):
    """
    Get daily or force sync log
    """
    daily_or_force_sync = (
        DailyOrForceSyncLog.objects.filter(**filters).order_by("-sync_date").first()
    )
    return daily_or_force_sync


def erp_daily_sync_logs(filters: dict):
    """
    Get daily sync logs
    """
    erp_daily_sync_log = ErpDailySyncLogs.objects.filter(**filters).first()
    return erp_daily_sync_log


def update_erp_daily_sync_logs(filters: dict, update_payload: dict):
    """
    Update daily sync logs
    """
    try:
        erp_daily_sync_log = ErpDailySyncLogs.objects.filter(**filters).update(
            **update_payload
        )
        return erp_daily_sync_log
    except DatabaseError as e:
        api_log(msg=f"Error updating erp daily sync log: {str(e)}")
        raise e


def update_daily_or_force_sync_log(filters: dict, update_payload: dict):
    """
    Update daily or force sync logs
    """
    try:
        daily_or_force_sync = DailyOrForceSyncLog.objects.filter(**filters).update(
            **update_payload
        )
        return daily_or_force_sync
    except DatabaseError as e:
        api_log(msg=f"Error updating daily or force sync log: {str(e)}")
        raise e
