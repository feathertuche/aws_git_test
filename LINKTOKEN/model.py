from django.db import models


class ErpLinkTokenManager(models.Manager):
    def get_link_token(self, org_id, entity_id):
        """
        Get link token by org_id and entity_id
        """
        filter_token = self.filter(org_id=org_id, entity_id=entity_id)
        if filter_token.exists():
            return filter_token.values_list("account_token", flat=True).first()

        return None


class ErpLinkToken(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=255)
    org_id = models.CharField(max_length=255)
    entity_id = models.CharField(max_length=255)
    link_token = models.CharField(max_length=255)
    account_token = models.CharField(max_length=255)
    integration_name = models.CharField(max_length=255)
    magic_link_url = models.CharField(max_length=255)
    categories = models.JSONField()
    platform = models.CharField(max_length=255)
    end_user_email_address = models.EmailField()
    end_user_organization_name = models.CharField(max_length=255)
    link_expiry_mins = models.IntegerField()
    should_create_magic_link_url = models.BooleanField()
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    custom_manager = ErpLinkTokenManager()

    class Meta:
        db_table = "erp_link_token"  # Set the actual table name here


class DailyOrForceSyncLog(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    link_token_id = models.CharField(max_length=36)
    sync_date = models.DateTimeField(null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    STATUS_CHOICES = (
        ("in_progress", "In Progress"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="in_progress"
    )
    SYNC_TYPE_CHOICES = (
        ("daily_sync", "Daily Sync"),
        ("force_resync", "Force Resync"),
    )
    sync_type = models.CharField(
        max_length=12, choices=SYNC_TYPE_CHOICES, default="daily sync"
    )
    is_initial_sync = models.BooleanField(default=False)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = "daily_or_force_sync_log"


class ErpDailySyncLogs(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    org_id = models.CharField(max_length=36)
    link_token_id = models.CharField(max_length=36)
    daily_or_force_sync_log_id = models.CharField(max_length=36)
    link_token = models.CharField(max_length=36)
    label = models.CharField(max_length=255)
    sync_start_time = models.DateTimeField(auto_now_add=True)
    sync_end_time = models.DateTimeField(null=True)
    SYNC_STATUS_CHOICES = (
        ("in_progress", "In Progress"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    sync_status = models.CharField(max_length=10, choices=SYNC_STATUS_CHOICES)
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    objects = models.Manager()

    class Meta:
        db_table = "erp_daily_sync_logs"
