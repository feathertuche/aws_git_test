from django.db import models


class MergeSyncLog(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=255)
    link_token_id = models.CharField(max_length=255)
    end_user_origin_id = models.CharField(max_length=255)
    module_name = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    sync_type = models.CharField(max_length=10)
    account_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = "merge_sync_log"
