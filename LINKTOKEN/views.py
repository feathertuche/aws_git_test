import json
import os
import traceback
from datetime import datetime, timezone
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from merge.resources.accounting import CategoriesEnum
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client
from .model import ErpLinkToken
from .merge_sync_log_model import MergeSyncLog
import traceback
from rest_framework import status
import uuid
from django.http import JsonResponse, HttpRequest
from threading import Thread
from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from SYNC.models import ERPLogs
from SYNC.queries import get_erplogs_by_link_token_id
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log
from services.merge_service import MergeSyncService
from .helper_function import create_erp_link_token, get_org_entity
from SYNC.models import ERPLogs
from SYNC.queries import get_erplogs_by_link_token_id, get_erplog_link_module_name
from SYNC.helper_function import (
    log_sync_status,
    start_new_sync_process,
    sync_modules_status

)


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
        authorization_header = request.headers.get("Authorization")
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
                api_key = os.environ.get("API_KEY")
                merge_client = create_merge_client(api_key)
                current_time = datetime.now(tz=timezone.utc)
                link_token_response = merge_client.ats.link_token.create(
                    end_user_email_address=end_user_email_address,
                    end_user_organization_name=request.data.get(
                        "end_user_organization_name"
                    ),
                    end_user_origin_id= end_usr_origin_id,
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
                    "bearer": authorization_header,
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
    api_log(msg=f"webhook  begin")
    
    try:
        payload = json.loads(request.body)
        api_log(msg=f"intial sync webhook details {payload}  begin")
        linked_account_data = payload.get("linked_account", {})
        # data = payload.get('data', {})
        # linked_account_data = data.get('linked_account')
   
        account_token = payload.get("data")
        payload_account_tokens = payload.get("linked_account", None)
        if payload_account_tokens is not None:
            end_user_org_id = payload_account_tokens.get('end_user_origin_id')
            if 'sync_status' in account_token:
                api_log(msg=f"sync webhook  begin")
                sync_status_data = account_token.get('sync_status')
                if sync_status_data is not None:
                   
                    linked_account_model_data = payload.get('linked_account', {})
                    model_name = sync_status_data.get('model_name')
                    sync_status_model_data = payload.get('data', {}).get('sync_status', {})
                    link_token_id_model = linked_account_model_data.get('end_user_origin_id')
                    module_name_merge = sync_status_model_data.get('model_name')
                    status = sync_status_data.get('status')
                    merge_status = sync_status_model_data.get('status')
                    sync_type = 'sync'
                    get_label_name = webhook_sync_modul_filter(module_name_merge)
                    response_data = get_erplog_link_module_name(link_token_id_model,get_label_name)
                    api_log(msg=f"<--------response_data object {response_data} start")
                    if response_data.sync_status =='in progress':
                        try:
                            api_log(msg=f"originmergesync log insert object  start")
                            api_log(msg=f"origin idmergesync log insert {link_token_id_model} object  start")
                            api_log(msg=f"mergesync log insert object  start")
                            merge_sync_log, created = MergeSyncLog.objects.get_or_create(
                            link_token_id=link_token_id_model,
                            defaults={
                                    'id': uuid.uuid1(),
                                    'module_name': module_name_merge,
                                    'link_token_id': link_token_id_model,
                                    'end_user_origin_id': link_token_id_model,
                                    'status': merge_status,
                                    'sync_type': sync_type,
                                    'account_type': linked_account_model_data.get('account_type')
                                }
                            )
                            api_log(msg=f"erplinktoken object  start")
                            api_log(msg=f"starttttterplinktoken object  start")
                            modules = []
                            api_log(msg=f"1dictionary start")
                            api_log(msg=f"1dictionary  end******")
                            erp_data = ErpLinkToken.objects.filter(
                                id=link_token_id_model
                            ).first()
                            api_views = {
                                "TrackingCategory": (
                                    MergePostTrackingCategories,
                                    {"link_token_details": erp_data.account_token},
                                ),
                                "CompanyInfo": (
                                    MergeKlooCompanyInsert,
                                    {"link_token_details": erp_data.account_token},
                                ),
                                "Account": (InsertAccountData, {"link_token_details": erp_data.account_token}),
                                "Contact": (
                                    MergePostContacts,
                                    {"link_token_details": erp_data.account_token},
                                ),
                                "TaxRate": (
                                    MergePostTaxRates,
                                    {"link_token_details": erp_data.account_token},
                                ),
                            }
                            
                            api_log(msg=f"****1dictionary {erp_data}  end")
                            api_log(msg=f"dictionary  start")
                            custom_request = HttpRequest()
                            custom_request.method = "POST"
                            custom_request.data = {
                                "erp_link_token_id": erp_data.id,
                            }
                            custom_request.headers = {
                                "Authorization": erp_data.bearer,
                            }
                            
                            api_log(msg=f"thread  start")
                            api_log(msg=f"argggg {custom_request}")
                            api_log(msg=f"argggg2 {erp_data.org_id}")
                            api_log(msg=f"argggg3 {erp_data.id}")
                            api_log(msg=f"argggg4 {erp_data.account_token}")
                            api_log(msg=f"argggg5 {[api_views[module_name_merge]]}")
                            thread = Thread(
                                target=sync_modules_status,
                                args=(
                                    custom_request,
                                    erp_data.org_id,
                                    erp_data.id,
                                    erp_data.account_token,
                                    [api_views[module_name_merge]]
                                
                                ),
                            )
                            
                            thread.start()
                            success_message = "thread started successfully"
                            success_data = {"success": success_message}
                            success_json = json.dumps(success_data)
                            api_log(msg=f"thread  end")
                            return JsonResponse(success_json, status=status.HTTP_200_OK)
                        except Exception as e:
                            print(f"Error occurred while saving MergeSyncLog instance: {e}")
                else:
                    api_log(msg=f"exception on thread")
                    error_message = "exception on thread"
                    error_data = {"error": error_message}
                    error_json = json.dumps(error_data)
                    return JsonResponse(error_json, status=500, safe=False)
                

            else:
                try:
                    
                    ErpLinkToken.objects.filter(
                        end_user_email_address=linked_account_data.get("end_user_email_address")
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
                    
                    modules = [
                            "TAX RATE",
                            "TRACKING CATEGORIES",
                            "COMPANY INFO",
                            "ACCOUNTS",
                            "CONTACTS",
                        ]
                    api_log(msg=f"ERPpppppppinsert sync log table for in progress: {account_token} in progress")
                    erp_link_token_id = account_token.get("end_user_origin_id")
                    api_log(msg=f"attt in progreess sync log table for in progress: {erp_link_token_id} in progress")
                    erp_data = ErpLinkToken.objects.filter(
                                id=erp_link_token_id
                            ).first()
                    
                    for module in modules:
                        api_log(msg=f"insert sync log table for in progress: {module} in progress")
                        log_sync_status(
                            sync_status="in progress",
                            message=f"API {module} executed successfully",
                            label=module,
                            org_id=erp_data.org_id,
                            erp_link_token_id= erp_data.id,
                            account_token= erp_data.account_token,
                        )

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

                    # response_data = {"message": "Webhook received and processed successfully"}
                    
                    # api_log(
                    #     msg=f"FORMATTED DATA to get data account token: {account_token}{linked_account_data} - Status Code: {status.HTTP_200_OK}: {traceback.format_exc()}"
                    # )
                    return JsonResponse(payload, status=status.HTTP_200_OK)

                except ObjectDoesNotExist:
                    # Handle the case where the record does not exist
                    return JsonResponse(
                        {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
                    )
    except Exception as e:
        error_message = f"An error occurred while calling API : {str(e)}"
        api_log(msg=f"exception error  end {error_message}")
        error_message = "Error processing webhook"
        error_data = {"error": error_message}
        error_json = json.dumps(error_data)
        return JsonResponse(error_json, status=500, safe=False)

def webhook_sync_modul_filter(module_name_merge):
    label_name = None
    if module_name_merge == "TaxRate":
        label_name = "TAX RATE"
    if module_name_merge == "TrackingCategory":
        label_name = "TRACKING CATEGORIES"
    if module_name_merge == "CompanyInfo":
        label_name = "COMPANY INFO"
    if module_name_merge == "Account":
        label_name = "ACCOUNTS"
    if module_name_merge == "Contact":
        label_name = "CONTACTS"
    return label_name
