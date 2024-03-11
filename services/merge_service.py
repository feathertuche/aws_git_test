from merge.core import ApiError

from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client


class MergeSyncService:
    """
    MergeApiService class
    """

    def __init__(self, account_token: str):
        self.merge_client = create_merge_client(account_token)

    def sync_status(self):
        """
        Get sync status of all modules [TrackingCategory, CompanyInfo, Account, Contact]
        """
        try:
            sync_status = self.merge_client.accounting.sync_status.list()
            return {"status": True, "data": sync_status}
        except ApiError as e:
            api_log(msg=f"SYNC STATUS :API MERGE Error {e}")
            return {"status": False, "error": "Sync Status api failed"}
