from django.apps import AppConfig


class InvoicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "INVOICES"

    def ready(self):
        from .scheduled_tasks import add_cron_jobs

        add_cron_jobs.start()
