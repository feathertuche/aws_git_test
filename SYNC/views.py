import uuid
from datetime import datetime
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.exceptions import APIException
from django.core.exceptions import ValidationError
from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from LINKTOKEN.model import ErpLinkToken
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from .models import ERPLogs
from merge_integration.utils import create_merge_client
from merge.core.api_error import ApiError


class DummySerializer(serializers.Serializer):
    pass


def get_erplogs_by_link_token_id(link_token_id):
    data = ERPLogs.objects.filter(link_token_id=link_token_id)
    if not data.exists():
        return []
    return [
        {
            "sync_status": log.sync_status,
            "label": log.label,
            "org_id": log.org_id,
        }
        for log in data
    ]


class ProxySyncAPI(CreateAPIView):
    serializer_class = DummySerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.org_id = None
        self.entity_id = None
        self.erp_link_token_id = None
        self.account_token = None

    def post(self, request, *args, **kwargs):
        org_id = request.data.get("org_id")
        entity_id = request.data.get("entity_id")
        erp_link_token_id = request.data.get("erp_link_token_id")
        self.org_id = org_id
        self.entity_id = entity_id
        self.erp_link_token_id = erp_link_token_id
        combined_response = []
        link_token_details = self.get_queryset()
        if link_token_details is None:
            response_data = {"message": "Sync still pending"}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        self.account_token = link_token_details[0]
        tc_client = create_merge_client(self.account_token)
        try:
            sync_status = tc_client.accounting.sync_status.list()
            # Process sync_status data
        except ApiError as e:
            # Log the error message
            # print(f"API Error: {e}")
            # Return a custom error response
            response_data = {"error": "Seems the connection is lost. Please disconnect and reconnect."}
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        sync_status_result = sync_status.results
        modules = ['TrackingCategory', 'CompanyInfo', 'Account', 'Contact']
        sync_module_status = []
        for module in modules:
            for sync_filter_array in sync_status_result:
                if sync_filter_array.model_name == module:
                    if sync_filter_array.status == 'DONE':
                        sync_module_status.append(sync_filter_array.model_name)

        if set(modules) != set(sync_module_status):
            response_data = {"message": "Sync still pending"}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        else:
            if org_id is None or entity_id is None:
                return Response("Both fields are required to fetch link token..",
                                status=status.HTTP_400_BAD_REQUEST)

            post_api_views = [
                (MergePostTrackingCategories, {'link_token_details': link_token_details}),
                (MergeKlooCompanyInsert, {'link_token_details': link_token_details}),
                (InsertAccountData, {'link_token_details': link_token_details}),
                (MergePostContacts, {'link_token_details': link_token_details})
            ]

            for index, (api_view_class, kwargs) in enumerate(post_api_views, start=1):
                try:
                    api_instance = api_view_class(**kwargs)
                    response = api_instance.post(request)
                    if response.status_code == status.HTTP_200_OK:
                        module_name = api_view_class.__module__
                        if module_name.endswith(".views"):
                            module_name = module_name[:-6]

                        combined_response.append({
                            "key": f"{module_name}",
                            'label': f"{module_name.replace('_', ' ')}",
                            "Status": status.HTTP_200_OK,
                            "successMessage": f"API {module_name} executed successfully"
                        })
                        self.success_log(success_message=f"API {module_name} executed successfully",
                                         label=f"{module_name.replace('_', ' ')}")
                    else:
                        module_name = api_view_class.__module__
                        if module_name.endswith(".views"):
                            module_name = module_name[:-6]
                        error_message = f"API {module_name} failed with status code {response.status_code}"
                        api_exception = APIException(error_message)
                        api_exception.module_name = module_name
                        raise api_exception
                except Exception as e:
                    error_message = f"An error occurred while calling API {index}: {str(e)}"
                    self.log_error(error_message=error_message)
                    return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return the combined response and response_data dictionary
            response_data = get_erplogs_by_link_token_id(erp_link_token_id)
            return Response({'response_data': response_data}, status=status.HTTP_200_OK)

            # except APIException as e:
            #     error_message = str(e)
            #     module_name = getattr(e, "module_name", "")
            #     self.log_error(error_message=error_message, label=module_name)
            #
            #     module_name = api_view_class.__module__
            #     if module_name.endswith(".views"):
            #         module_name = module_name[:-6]
            #
            #     combined_response.append({
            #         'key': f"{module_name}",
            #         'label': f"{module_name.replace('_', ' ')}",
            #         'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
            #         'errorMessage': error_message
            #     })
            #
            # except Exception as e:
            #     error_message = f"An error occurred while calling API {index}: {str(e)}"
            #     self.log_error(error_message=error_message)
            #     return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            #return Response(response_data, status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.org_id is None or self.entity_id is None:
            return ErpLinkToken.objects.none()
        else:
            filter_token = ErpLinkToken.objects.filter(org_id=self.org_id, entity_id=self.entity_id)
            lnk_token = filter_token.values_list('account_token', flat=1)

        return lnk_token

    def log_error(self, error_message, label):
        # Log the error to the database
        log_entry = ERPLogs(
            id=uuid.uuid1(),
            org_id=self.org_id,
            link_token_id=self.erp_link_token_id,
            link_token=self.account_token,
            label=label,
            sync_start_time=datetime.now(),
            sync_end_time=datetime.now(),
            sync_status="Failed",
            error_message=error_message
        )
        log_entry.save()

    def success_log(self, success_message, label):
        log_entry = ERPLogs(
            id=uuid.uuid1(),
            org_id=self.org_id,
            link_token_id=self.erp_link_token_id,
            link_token=self.account_token,
            label=label,
            sync_start_time=datetime.now(),
            sync_end_time=datetime.now(),
            sync_status="Success",
            error_message=success_message
        )
        log_entry.save()
