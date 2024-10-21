
from django.apps import AppConfig
from .signals import start_sqs_polling

class MergeIntegrationConfig(AppConfig):
    name = 'merge_integration'

    def ready(self):
        print("-app-2333333333333----1starttttttProcessing message:----------")
        start_sqs_polling()
        pass  # No need to import here
