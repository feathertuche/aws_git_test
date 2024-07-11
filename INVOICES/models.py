from django.db import models


class TypeEnum(models.TextChoices):
    invoice = "invoice"
    attachment = "attachment"


class StatusEnum(models.TextChoices):
    success = "success"
    failed = "failed"


class InvoiceAttachmentLogs(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    invoice_id = models.UUIDField()
    attachment_id = models.UUIDField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TypeEnum.choices)
    status = models.CharField(max_length=20, choices=StatusEnum.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    problem_type = models.CharField(max_length=55)

    class Meta:
        db_table = "invoice_attachment_logs"
