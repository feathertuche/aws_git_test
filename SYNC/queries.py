from LINKTOKEN.model import ErpLinkToken
from SYNC.models import ERPLogs


def get_link_token(erp_link_token_id):
    """
    Get link token by org_id and entity_id
    """
    filter_token = ErpLinkToken.objects.filter(id=erp_link_token_id)
    if filter_token.exists():
        return filter_token.values_list("account_token", flat=True).first()

    return None


def get_erplogs_by_link_token_id(link_token_id):
    """
    Get ERP logs by link token id
    """
    data = ERPLogs.objects.filter(link_token_id=link_token_id)
    if not data.exists():
        return []
    return [
        {
            "sync_status": log.sync_status,
            "label": log.label,
            "org_id": log.org_id,
        }
        for log in data
    ]


def get_erplog_link_module_name(link_token_id, label):
    """
    Get ERP logs by link token id
    """
    data = ERPLogs.objects.filter(link_token_id=link_token_id, label=label).first()
    return data
