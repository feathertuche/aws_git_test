from django.db import models


class ErpLinkTokenManager(models.Manager):
    pass


class ERPLogs(models.Model):
    class SyncStatus(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'
        PENDING = 'pending', 'Pending'

    id = models.UUIDField(primary_key=True, editable=False)
    org_id = models.CharField(max_length=255)
    link_token_id = models.CharField(max_length=36)
    link_token = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    sync_start_time = models.DateTimeField()
    sync_end_time = models.DateTimeField()
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.PENDING)
    error_message = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(auto_now=True)

    objects = ErpLinkTokenManager()

    class Meta:
        db_table = 'erp_sync_logs'