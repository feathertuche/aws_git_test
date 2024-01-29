from merge.resources.accounting import CategoriesEnum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from merge_integration.utils import create_merge_client
import sys


class LinkToken(APIView):
    def post(self, request):
        try:
            merge_client = create_merge_client()
            link_token_response = merge_client.ats.link_token.create(
                end_user_email_address=request.data.get("end_user_email_address"),
                end_user_organization_name=request.data.get("end_user_organization_name"),
                end_user_origin_id=request.data.get("end_user_origin_id"),
                categories=[CategoriesEnum.ATS],
                should_create_magic_link_url=request.data.get("should_create_magic_link_url"),
                link_expiry_mins=30,
            )
            return Response(link_token_response, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @csrf_exempt
    def webhook_handler(self, request):
        """
        Handles incoming webhook requests.

        Args:
            self: The LinkToken instance.
            request: The incoming HTTP request.

        Returns:
            HttpResponse: The HTTP response.
        """
        print("webhook-data-start")
        print(data = json.loads(request.body))
        print("webhook-data-end")
        if request.method == 'POST':
            try:
                # Assuming the data sent by the webhook is in JSON format
                data = json.loads(request.body)

                # Print or log the received data
                print("Webhook Data:", data)

                # Your logic to process the data and generate a response
                # For example, you might want to store the data in the database or perform some other action

                # Return a response
                return HttpResponse("Webhook received successfully", status=200)
            except Exception as e:
                print("Error processing webhook data:", str(e))
                return HttpResponse("Error processing webhook data", status=500)
        else:
            return HttpResponse("Unsupported method", status=405)   
