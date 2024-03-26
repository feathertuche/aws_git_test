from django.apps import AppConfig

from merge_integration.helper_functions import api_log


class InvoicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "INVOICES"

    def ready(self):
        api_log(msg="CRON:INVOICE : Adding Invoice POST cron job")
        from .scheduled_tasks import add_cron_jobs

        add_cron_jobs.start()
