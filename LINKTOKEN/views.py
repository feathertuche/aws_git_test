from merge.resources.accounting import CategoriesEnum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from merge_integration.utils import create_merge_client
import json
from .models import ErpLinkToken

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
def webhook_handler(request):
    
    try:
        #data = json.loads(request.body)
        #print("Webhook Data:", data)

        payload = json.loads(request.body)
        linked_account_data = payload.get('linked_account', {})
        data = payload.get('data', {})
        linked_account_data = data.get('linked_account')
        account_token = data.get('data')

        link_token_record = ErpLinkToken(
            id=linked_account_data.get('id'),
            org_id=linked_account_data.get('id'),
            entity_id=linked_account_data.get('id'),
            link_token=account_token.get('account_token'),
            integration_name=linked_account_data.get('integration'),
            magic_link_url=linked_account_data.get('webhook_listener_url'),
            categories=linked_account_data.get('category'),
            platform=linked_account_data.get('account_type'),
            end_user_email_address=linked_account_data.get('end_user_email_address'),
            end_user_organization_name=linked_account_data.get('end_user_organization_name'),
            link_expiry_mins=60,
            should_create_magic_link_url=False,
            status=linked_account_data.get('status'),
        )
        link_token_record.save()

        # Your webhook handling logic here

        # Assuming your logic was successful, respond with data
        response_data = {"message": "Webhook received and processed successfully"}
        return JsonResponse(response_data, status=200)
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", str(e))
        # If JSON decoding fails, respond with an error using HttpResponse
        return HttpResponse("Invalid JSON data", status=400, content_type='text/plain')
    except Exception as e:
        print("Webhook Handling Error:", str(e))
        # If there's an error in your webhook handling logic, respond with an error using HttpResponse
        return HttpResponse("Error processing webhook", status=500, content_type='text/plain')
