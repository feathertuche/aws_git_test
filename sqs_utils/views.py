import boto3
from django.conf import settings
import json
import threading
import requests

def send_data_to_queue(data_array):
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION
    )
    sqs_client = session.client('sqs')
    queue_name = settings.SQS_QUEUE
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)

    # Send the data array as a JSON string to the queue
    response = sqs_client.send_message(
        MessageBody=json.dumps(data_array)  # Convert data to JSON
    )
    return response


def process_sqs_messages():
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION
    )
    sqs_client = session.client('sqs')
    queue_name = settings.SQS_QUEUE
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)

    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1
        )

        messages = response.get('Messages', [])
        for message in messages:
            data = json.loads(message['Body'])
            print('message rcvd')
            print(data)
            print('message rcvd')
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])


def start_sqs_message_processing():
    thread = threading.Thread(target=process_sqs_messages)
    thread.start()

def send_slack_notification(message):

    webhook_url = "https://hooks.slack.com/services/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"
    payload = {
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")
