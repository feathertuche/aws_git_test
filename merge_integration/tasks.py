import threading
import time
import boto3
from merge_integration import settings
import json
from merge_integration.settings import GETKLOO_LOCAL_URL, contacts_page_size
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from merge_integration.helper_functions import api_log


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

    if 'erp_contacts' in message_body:
        erp_contacts = message_data["erp_contacts"]
        contact_url = (
            f"{GETKLOO_LOCAL_URL}/ap/erp-integration/insert-erp-contacts"
        )
        print("ERP Contacts-------------------------------:")
        contact_response_data = requests.post(
            contact_url,
            json=message_data,
            # stream=True,
        )

        if contact_response_data.status_code == status.HTTP_201_CREATED:
            api_log(
                msg="data inserted successfully in the kloo Contacts system"
            )
            return Response(
                {"message": "API Contact Info completed successfully"}
            )

        else:
            return Response(
                {"error": "Failed to send data to Kloo Contacts API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        for contact in erp_contacts:
            print(json.dumps(contact, indent=2))
    else:
        print("empty message. Skipping.")


def poll_sqs():
    # Initialize SQS client
    sqs = boto3.client('sqs', region_name=settings.AWS_DEFAULT_REGION,
                       aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    print("polling start message:")

    while True:
        try:
            # Poll SQS queue for messages (with long polling)
            response = sqs.receive_message(
                QueueUrl=settings.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20  # Long polling wait time (max 20 seconds)
            )

            # Process received messages
            messages = response.get('Messages', [])
            for message in messages:
                process_message(message['Body'])
                sqs.delete_message(
                    QueueUrl=settings.queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)  # Wait for a short period before retrying


def start_polling():
    # Start polling SQS queue in a separate thread
    polling_thread = threading.Thread(target=poll_sqs)
    polling_thread.daemon = True
    polling_thread.start()
