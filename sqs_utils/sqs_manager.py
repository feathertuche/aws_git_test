import json
import boto3
import requests
from django.conf import settings
from sqs_extended_client import (
    SQSExtendedClientSession,
)
from merge_integration.helper_functions import api_log
from merge_integration.settings import SQS_BUCKET


def send_data_to_queue(data_array):
    """
    Send data to the SQS queue
    """
    api_log(msg=f"SQS working with session {SQSExtendedClientSession}")

    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )
    sqs_client = session.client("sqs")
    sqs_client.large_payload_support = SQS_BUCKET
    sqs_client.use_legacy_attribute = False
    queue_name = settings.SQS_QUEUE
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)

    # Send the data array as a JSON string to the queue
    response = sqs_client.send_message(
        QueueUrl=queue_url["QueueUrl"],
        MessageBody=json.dumps(data_array),  # Convert data to JSON
    )

    api_log(msg=f"Data sent to SQS: {response}")

    return response


def send_slack_notification(message):
    webhook_url = settings.SLACK_WEBHOOK_URL
    payload = {"text": message}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")
