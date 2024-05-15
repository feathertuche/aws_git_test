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
            msg="CONTACTS : Added in Kloo Contacts API",
        )

    elif "invoices" in message_body:
        # Send invoices data to Kloo Invoices API
        kloo_service = KlooService(
            auth_token=None,
            erp_link_token_id=None,
        )
        kloo_service.post_invoice_data(message_data)
        api_log(
            msg="INVOICES : Added in Kloo Invoices API",
        )

    elif "tracking_category" in message_body:
        # Send tracking categories data to Kloo Tracking Categories API
        kloo_service = KlooService(
            auth_token=None,
            erp_link_token_id=None,
        )
        kloo_service.post_tracking_categories_data(message_data)
        api_log(
            msg="TRACKING CATEGORIES : Added in Kloo Tracking Categories API",
        )

    else:
        api_log(msg="Invalid message format. Skipping.")


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
                message_data_details = message["Body"]
                message_data_json = json.loads(message_data_details)
                if "erp_contacts" in message_data_json:
                    process_message(message["Body"])
                    sqs.delete_payload_from_s3 = True
                    sqs.delete_message(
                        QueueUrl=settings.queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
                elif "invoices" in message_data_json:
                    process_message(message["Body"])
                    sqs.delete_payload_from_s3 = True
                    sqs.delete_message(
                        QueueUrl=settings.queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
                elif "tracking_category" in message_data_json:
                    process_message(message["Body"])
                    sqs.delete_payload_from_s3 = True
                    sqs.delete_message(
                        QueueUrl=settings.queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
                else:
                    api_log(msg="No new messages found in the queue.")
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)  # Wait for a short period before retrying


def start_polling():
    # Start polling SQS queue in a separate thread
    polling_thread = threading.Thread(target=poll_sqs)
    polling_thread.daemon = True
    polling_thread.start()