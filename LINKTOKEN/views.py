from merge.resources.accounting import CategoriesEnum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from merge_integration.utils import create_merge_client
import json
import os
import traceback
from .models import ErpLinkToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from merge_integration.helper_functions import api_log

from dotenv import load_dotenv


class LinkToken(APIView):
    def post(self, request):
        try:
            merge_client = create_merge_client()
            link_token_response = merge_client.ats.link_token.create(
                end_user_email_address=request.data.get("end_user_email_address"),
                end_user_organization_name=request.data.get("end_user_organization_name"),
                end_user_origin_id=request.data.get("end_user_origin_id"),
                categories=[CategoriesEnum.ACCOUNTING],
                should_create_magic_link_url=request.data.get("should_create_magic_link_url"),
                link_expiry_mins=30,
            )

            data_to_return = {
                "link_token": link_token_response.link_token,
                "magic_link_url": link_token_response.magic_link_url,
                "integration_name": link_token_response.integration_name,
            }

            response = Response(data_to_return, status=status.HTTP_201_CREATED)
            response.accepted_renderer = JSONRenderer()
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
@csrf_exempt
def webhook_handler(request):
    
    try:
        #data = json.loads(request.body)
        #print("Webhook Data:", data)

        payload = json.loads(request.body)
        # linked_account_data = payload.get('linked_account', {})
        # data = payload.get('data', {})
        # linked_account_data = data.get('linked_account')
        # account_token = data.get('data')

        # link_token_record = ErpLinkToken(
        #     id=linked_account_data.get('id'),
        #     org_id=linked_account_data.get('id'),
        #     entity_id=linked_account_data.get('id'),
        #     link_token=account_token.get('account_token'),
        #     integration_name=linked_account_data.get('integration'),
        #     magic_link_url=linked_account_data.get('webhook_listener_url'),
        #     categories=linked_account_data.get('category'),
        #     platform=linked_account_data.get('account_type'),
        #     end_user_email_address=linked_account_data.get('end_user_email_address'),
        #     end_user_organization_name=linked_account_data.get('end_user_organization_name'),
        #     link_expiry_mins=60,
        #     should_create_magic_link_url=False,
        #     status=linked_account_data.get('status'),
        # )
        # link_token_record.save()

        #response_data = {"message": "Webhook received and processed successfully"}
        return JsonResponse(payload, status=status.HTTP_200_OK)
    except Exception as e:
        error_message = {"Error processing webhook": str(e)}
        api_log(
                msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}")
        return JsonResponse(error_message, status=500)
