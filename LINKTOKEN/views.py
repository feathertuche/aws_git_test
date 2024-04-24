import json
import os
import uuid
from threading import Lock

from django.views.decorators.csrf import csrf_exempt
from merge.core import ApiError
from merge.resources.accounting import CategoriesEnum
from rest_framework import status
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
from .queries import get_erp_link_token

# Define a global lock
webhook_lock = Lock()

class LinkToken(APIView):
    """
    LinkToken API
    """

    def post(self, request):
        api_log(msg=f"LINKTOKEN: LinkToken API called with data {request.data}")
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
            api_log(msg="LINKTOKEN: Link token already exists")
            link_token_data = check_exist_linktoken
            if link_token_data["is_available"]:
                # Update the bearer field with the new token
                link_token_record = ErpLinkToken.objects.get(
                    link_token=link_token_data["link_token"]
                )
                link_token_record.save()
            return Response(check_exist_linktoken, status=status.HTTP_201_CREATED)
        else:
            api_log(msg="LINKTOKEN: Creating new link token")
            try:
                end_usr_origin_id = uuid.uuid1()
                api_key = os.environ.get("API_KEY")
                api_log(msg=f"LINKTOKEN: API key {api_key}")
                merge_client = create_merge_client(api_key)
                api_log(msg=f"LINKTOKEN: Merge client created {merge_client}")

                try:
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
                    api_log(msg=f"LINKTOKEN: Link token response {link_token_response}")
                except ApiError as e:
                    api_log(msg=f"LINKTOKEN: Exception occurred: {e}")

                data_to_return = {
                    "link_token": link_token_response.link_token,
                    "magic_link_url": link_token_response.magic_link_url,
                    "integration_name": link_token_response.integration_name,
                }

                api_log(msg=f"LINKTOKEN: Link token created with data {data_to_return}")

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

                api_log(msg=f"LINKTOKEN: Creating ERP link token with data {data}")

                create_erp_link_token(data)

                api_log(msg="LINKTOKEN: ERP link token created successfully")
                return Response(data_to_return, status=status.HTTP_201_CREATED)
            except Exception as e:
                api_log(msg=f"LINKTOKEN: Exception occurred: {str(e)}")
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
            with webhook_lock:
                payload = json.loads(request.body)
                api_log(msg=f"WEBHOOK: Payload {payload}")
                linked_account_data = payload.get("linked_account", None)
                account_token_data = payload.get("data")
                end_user_origin_id = linked_account_data.get("end_user_origin_id")
                # check if the linked account exists , since webhook hits all env
                erp_link_token_exists = get_erp_link_token(
                    erp_link_token_id=end_user_origin_id
                )
                if erp_link_token_exists is None:
                    api_log(
                        msg=f"WEBHOOK: Erp link token does not exist for {end_user_origin_id}"
                        f" in this environment"
                    )
                    return Response(
                        {"status": "WEBHOOK: Erp link token does not exist"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # check type of webhook it is
                event = payload.get("hook").get("event")
                if "synced" in event.split("."):
                    api_log(
                        msg=f"WEBHOOK: Sync data received for End User id {end_user_origin_id} "
                        f"for module {payload.get('data').get('sync_status').get('model_name')}"
                    )
                    handle_webhook_sync_modules(linked_account_data, account_token_data)
                elif "linked" in event.split("."):
                    api_log(
                        msg=f"WEBHOOK: Initial data received for End User id"
                        f" {end_user_origin_id}"
                    )
                    handle_webhook_link_account(
                        account_token_data=account_token_data,
                        linked_account_data=linked_account_data,
                    )
                else:
                    api_log(msg="WEBHOOK: No proper event found")
                    return Response(
                        {"status": "No proper event found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            return Response({"status": "WEBHOOK: ended"}, status=status.HTTP_200_OK)
        except Exception as e:
            api_log(msg=f"WEBHOOK: Exception occurred: {str(e)}")
