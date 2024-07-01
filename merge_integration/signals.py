from django.db.models.signals import post_migrate
from django.dispatch import receiver


from .helper_functions import api_log
from .tasks import start_polling


@receiver(post_migrate)
def start_sqs_polling():
    """
    Start SQS polling
    """
    api_log(msg="Starting SQS polling")
    start_polling()
