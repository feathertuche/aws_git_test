from django.db import models


class ErpLinkTokenManager(models.Manager):
    pass

class ErpLinkToken(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
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

    objects = ErpLinkTokenManager()
    class Meta:
        db_table = 'erp_link_token'  # Set the actual table name here
