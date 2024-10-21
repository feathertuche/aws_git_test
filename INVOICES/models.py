from django.db import models


class TypeEnum(models.TextChoices):
    invoice = "invoice"
    attachment = "attachment"


class StatusEnum(models.TextChoices):
    success = "success"
    failed = "failed"


class InvoiceStatusEnum(models.TextChoices):
    paid = "paid"
    approved = "approved"
    rejected = "rejected"
    scheduled = "scheduled"
    submitted = "submitted"
    cancelled = "cancelled"
    failed = "failed"
    in_review = "in_review"
    hold = "hold"
    DRAFT = "DRAFT"


class InvoiceAttachmentLogs(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, max_length=36)
    invoice_id = models.CharField(max_length=36)
    attachment_id = models.UUIDField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TypeEnum.choices)
    status = models.CharField(max_length=20, choices=StatusEnum.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    invoice_status = models.CharField(max_length=20, choices=InvoiceStatusEnum.choices)
    problem_type = models.CharField(max_length=55)

    class Meta:
        db_table = "invoice_attachment_logs"


class CronRetry(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    kloo_invoice_id = models.CharField(max_length=50)
    cron_execution_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "erp_pending_invoices_retry"

    def __str__(self):
        return f"{self.kloo_invoice_id}"
