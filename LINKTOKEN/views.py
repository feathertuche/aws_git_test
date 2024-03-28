import json
import os
import uuid

from django.views.decorators.csrf import csrf_exempt
from merge.resources.accounting import CategoriesEnum
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client
from .helper_function import (
    create_erp_link_token,
    get_org_entity,
    get_linktoken,
    handle_webhook_link_account,
    handle_webhook_sync_modules,
)
from .model import ErpLinkToken


class LinkToken(APIView):
    """
    LinkToken API
    """

    def post(self, request):
        org_id = request.data.get("organisation_id")
        end_user_email_address = request.data.get("end_user_email_address")

        if not org_id or not end_user_email_address:
            return Response(
                {"error": "organisation_id and end_user_email_address are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_exist_linktoken = get_linktoken(
            org_id, "INCOMPLETE", end_user_email_address
        )
        is_available = check_exist_linktoken.get("is_available")
        if is_available == 1:
            link_token_data = check_exist_linktoken
            if link_token_data["is_available"]:
                # Update the bearer field with the new token
                link_token_record = ErpLinkToken.objects.get(
                    link_token=link_token_data["link_token"]
                )
                link_token_record.save()
            response = Response(check_exist_linktoken, status=status.HTTP_201_CREATED)
            response.accepted_renderer = JSONRenderer()
            return response
        else:
            try:
                end_usr_origin_id = uuid.uuid1()
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


class WebHook(APIView):
    """
    Webhook api
    """

    @csrf_exempt
    def post(self, request):
        """
        Webhook post method
        """
        api_log(msg="WEBHOOK: Webhook received")
        try:
            payload = json.loads(request.body)
            api_log(msg=f"WEBHOOK: Payload {payload}")
            linked_account_data = payload.get("linked_account", None)
            account_token_data = payload.get("data")
            if linked_account_data is not None:
                if "sync_status" in account_token_data:
                    api_log(
                        msg=f"WEBHOOK: Sync data received for account token {account_token_data.get('account_token')} "
                        f"for module {payload.get('data').get('sync_status').get('model_name')}"
                    )
                    handle_webhook_sync_modules(linked_account_data, account_token_data)
                else:
                    api_log(
                        msg=f"WEBHOOK: Initial data received for account token"
                        f" {account_token_data.get('account_token')}"
                    )
                    handle_webhook_link_account(
                        account_token_data=account_token_data,
                        linked_account_data=linked_account_data,
                    )

        except Exception as e:
            api_log(msg=f"WEBHOOK: Exception occurred: {str(e)}")

        return Response({"status": "WEBHOOK: ended"}, status=status.HTTP_200_OK)
