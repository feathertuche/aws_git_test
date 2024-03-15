import json
import os
import traceback
import uuid
from datetime import datetime, timezone
from threading import Thread

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from merge.resources.accounting import CategoriesEnum
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from SYNC.helper_function import start_sync_process
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client
from .helper_function import create_erp_link_token, get_org_entity
from .model import ErpLinkToken


class LinkToken(APIView):
    def get_linktoken(self, org_id, status, end_user_email_address):
        filter_token = ErpLinkToken.objects.filter(
            org_id=org_id, status=status, end_user_email_address=end_user_email_address
        )

        if not filter_token:
            return {"is_available": 0}

        first_token = filter_token.first()
        timestamp = first_token.created_at.replace(tzinfo=timezone.utc)
        current_time = datetime.now(tz=timezone.utc)
        time_difference = current_time - timestamp
        difference_in_minutes = time_difference.total_seconds() / 60
        if first_token and difference_in_minutes < first_token.link_expiry_mins:
            data = {
                "link_token": first_token.link_token,
                "magic_link_url": first_token.magic_link_url,
                "integration_name": first_token.integration_name,
                # "time_difference": difference_in_minutes,
                # "current_time": current_time,
                "timestamp": timestamp,
                "is_available": 1,
            }
            return data
        else:
            return {"is_available": 0}

    def post(self, request):
        org_id = request.data.get("organisation_id")
        end_user_email_address = request.data.get("end_user_email_address")

        if not org_id or not end_user_email_address:
            return Response(
                {"error": "organisation_id and end_user_email_address are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_exist_linktoken = self.get_linktoken(
            org_id, "INCOMPLETE", end_user_email_address
        )
        is_available = check_exist_linktoken.get("is_available")
        if is_available == 1:
            response = Response(check_exist_linktoken, status=status.HTTP_201_CREATED)
            response.accepted_renderer = JSONRenderer()
            return response
        else:
            try:
                end_usr_origin_id = uuid.uuid1()
                # new_insert = post_data(request)
                api_key = os.environ.get("API_KEY")
                merge_client = create_merge_client(api_key)
                link_token_response = merge_client.ats.link_token.create(
                    end_user_email_address=end_user_email_address,
                    end_user_organization_name=request.data.get(
                        "end_user_organization_name"
                    ),
                    end_user_origin_id=end_usr_origin_id,
                    categories=[CategoriesEnum.ACCOUNTING],
                    should_create_magic_link_url=request.data.get(
                        "should_create_magic_link_url"
                    ),
                    link_expiry_mins=30,
                    integration=request.data.get("integration"),
                )

                data_to_return = {
                    "link_token": link_token_response.link_token,
                    "magic_link_url": link_token_response.magic_link_url,
                    "integration_name": link_token_response.integration_name,
                }
                data = {
                    "id": end_usr_origin_id,
                    "categories": request.data.get("categories"),
                    "entity_id": get_org_entity(request.data.get("organisation_id"))[0],
                    "integration_name": request.data.get("integration"),
                    "link_expiry_mins": request.data.get("link_expiry_mins"),
                    "org_id": request.data.get("organisation_id"),
                    "should_create_magic_link_url": request.data.get(
                        "should_create_magic_link_url"
                    ),
                    "link_token": link_token_response.link_token,
                    "end_user_organization_name": request.data.get(
                        "end_user_organization_name"
                    ),
                    "end_user_email_address": request.data.get(
                        "end_user_email_address"
                    ),
                    "magic_link_url": link_token_response.magic_link_url,
                    "status": "INCOMPLETE",
                }

                create_erp_link_token(data)
                response = Response(data_to_return, status=status.HTTP_201_CREATED)
                response.accepted_renderer = JSONRenderer()
                return response
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


@csrf_exempt
def webhook_handler(request):
    try:
        # data = json.loads(request.body)
        # print("Webhook Data:", data)

        payload = json.loads(request.body)
        linked_account_data = payload.get("linked_account", {})
        # data = payload.get('data', {})
        # linked_account_data = data.get('linked_account')
        account_token = payload.get("data")

        try:
            ErpLinkToken.objects.filter(
                id=linked_account_data.get("end_user_origin_id")
            ).update(
                integration_name=linked_account_data.get("integration"),
                magic_link_url=linked_account_data.get("webhook_listener_url"),
                categories=linked_account_data.get("category"),
                platform=linked_account_data.get("account_type"),
                account_token=account_token.get("account_token"),
                end_user_email_address=linked_account_data.get(
                    "end_user_email_address"
                ),
                end_user_organization_name=linked_account_data.get(
                    "end_user_organization_name"
                ),
                link_expiry_mins=60,
                should_create_magic_link_url=False,
                status=linked_account_data.get("status"),
            )
            api_log(
                msg=f"FORMATTED DATA to get data account token: {account_token}{linked_account_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
            )

            erp_data = ErpLinkToken.objects.filter(
                id=linked_account_data.get("end_user_origin_id")
            ).first()

            thread = Thread(
                target=start_sync_process,
                args=(
                    request,
                    erp_data.id,
                    erp_data.org_id,
                    erp_data.account_token,
                ),
            )

            thread.start()

            return JsonResponse(payload, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            # Handle the case where the record does not exist
            return JsonResponse(
                {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        error_message = {"Error processing webhook": str(e)}
        api_log(
            msg=f"Error retrieving organizations details: {str(e)} - Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}: {traceback.format_exc()}"
        )
        return JsonResponse(error_message, status=500)
