import json
import threading
import time

import boto3

from merge_integration import settings
from merge_integration.helper_functions import api_log
from services.kloo_service import KlooService


def process_message(message):
    # Simulate message processing
    message_body = message
    try:
        message_data = json.loads(message_body)
    except json.JSONDecodeError:
        print("Invalid JSON format. Skipping message.")
        return

    if not message:
        print("Received an empty message. Skipping.")
        return

    if "erp_contacts" in message_body:
        # Send contacts data to Kloo Contacts API
        kloo_service = KlooService(
            auth_token=None,
            erp_link_token_id=None,
        )
        kloo_service.post_contacts_data(message_data)
        api_log(
            msg="CONTACTS : Response from Kloo Contacts API",
        )

    elif "invoices" in message_body:
        # Send invoices data to Kloo Invoices API
        kloo_service = KlooService(
            auth_token=None,
            erp_link_token_id=None,
        )
        kloo_service.post_invoice_data(message_data)
        api_log(
            msg="INVOICES : Response from Kloo Invoices API",
        )

    else:
        print("empty message. Skipping.")


def poll_sqs():
    # Initialize SQS client
    sqs = boto3.client(
        "sqs",
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    print("polling start message:")

    while True:
        try:
            # Poll SQS queue for messages (with long polling)
            response = sqs.receive_message(
                QueueUrl=settings.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # Long polling wait time (max 20 seconds)
            )

            # Process received messages
            messages = response.get("Messages", [])
            for message in messages:
                process_message(message["Body"])
                message_data_details = message["Body"]
                message_data_json = json.loads(message_data_details)
                if "erp_contacts" in message_data_json:
                    sqs.delete_message(
                        QueueUrl=settings.queue_url, ReceiptHandle=message["ReceiptHandle"]
                    )
                elif "invoices" in message_data_json:
                    sqs.delete_message(
                        QueueUrl=settings.queue_url, ReceiptHandle=message["ReceiptHandle"]
                    )
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)  # Wait for a short period before retrying


def start_polling():
    # Start polling SQS queue in a separate thread
    polling_thread = threading.Thread(target=poll_sqs)
    polling_thread.daemon = True
    polling_thread.start()
