import uuid

from django.db import models
from uuid import uuid4

class PassthroughTaxSolution(models.Model):
    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, max_length=255)
    linktoken_id = models.CharField(max_length=255)
    org_id = models.CharField(max_length=255)
    company_id = models.CharField(max_length=255)
    solutionid = models.CharField(max_length=255)
    recordno = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    taxmethod = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    startdate = models.DateField()
    showmultilinetax = models.BooleanField()
    aradvanceoffsetacct = models.CharField(max_length=255, null=True, blank=True)
    aradvanceoffsetaccttitle = models.CharField(max_length=255, null=True, blank=True)
    aradvanceoffsetacctkey = models.CharField(max_length=255, null=True, blank=True)
    glaccountpurchase = models.CharField(max_length=255)
    glaccountpurchasetitle = models.CharField(max_length=255)
    glaccountpurchasekey = models.CharField(max_length=255)
    glaccountsale = models.CharField(max_length=255)
    glaccountsaletitle = models.CharField(max_length=255)
    glaccountsalekey = models.CharField(max_length=255)
    altsetup = models.BooleanField()
    lastupdate = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'passthrough_tax_solutions'
