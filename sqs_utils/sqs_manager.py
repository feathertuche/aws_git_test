import json
import threading

import boto3
from django.conf import settings

from merge_integration.helper_functions import api_log


def send_data_to_queue(data_array):
    """
    Send data to the SQS queue
    """
    api_log(msg=f"SQS payload length: {len(data_array)}")

    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )
    sqs_client = session.client("sqs")
    sqs_client.large_payload_support = "dev-bulk-data-import"
    sqs_client.use_legacy_attribute = False
    queue_name = settings.SQS_QUEUE
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)

    # Send the data array as a JSON string to the queue
    response = sqs_client.send_message(
        QueueUrl=queue_url["QueueUrl"],
        MessageBody=json.dumps(data_array),  # Convert data to JSON
    )
    return response


def process_sqs_messages():
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )
    sqs_client = session.client("sqs")
    queue_name = settings.SQS_QUEUE
    response = sqs_client.get_queue_url(QueueName=queue_name)
    queue_url = response["QueueUrl"]  # Extract QueueUrl from response

    while True:
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)

        messages = response.get("Messages", [])
        for message in messages:
            data = json.loads(message["Body"])
            print("message received")
            print(data)
            print("message received")
            sqs_client.delete_message(
                QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
            )


def start_sqs_message_processing():
    thread = threading.Thread(target=process_sqs_messages)
    thread.start()
