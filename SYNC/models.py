from django.db import models


class ErpLinkTokenManager(models.Manager):

    def get_erp_logs(self, link_token_id):
        """
        Get link token by link_token_id
        """
        erp_logs = self.filter(link_token_id=link_token_id)
        if not erp_logs.exists():
            return []
        return [
            {
                "sync_status": log.sync_status,
                "label": log.label,
                "org_id": log.org_id,
            }
            for log in erp_logs
        ]


class ERPLogs(models.Model):
    class SyncStatus(models.TextChoices):
        IN_PROGRESS = "in progress", "in progress"
        SUCCESS = "success", "success"
        FAILED = "failed", "failed"

    id = models.UUIDField(primary_key=True, editable=False)
    org_id = models.CharField(max_length=255)
    link_token_id = models.CharField(max_length=36)
    link_token = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    sync_start_time = models.DateTimeField()
    sync_end_time = models.DateTimeField()
    sync_status = models.CharField(
        max_length=15, choices=SyncStatus.choices, default=SyncStatus.IN_PROGRESS
    )
    error_message = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    custom_manager = ErpLinkTokenManager()

    class Meta:
        db_table = "erp_sync_logs"
