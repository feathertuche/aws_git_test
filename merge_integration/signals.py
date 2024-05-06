from django.dispatch import receiver
from django.db.models.signals import post_migrate
from .tasks import start_polling

@receiver(post_migrate)
def start_sqs_polling():
    print("-signal-2333333333333----1starttttttProcessing message:----------")
    start_polling()
