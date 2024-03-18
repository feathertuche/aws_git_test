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
    bearer = models.TextField()
    
    objects = models.Manager()
    custom_manager = ErpLinkTokenManager()

    class Meta:
        db_table = "erp_link_token"  # Set the actual table name here
