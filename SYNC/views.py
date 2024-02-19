import uuid
from datetime import datetime
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.exceptions import APIException

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from LINKTOKEN.model import ErpLinkToken
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from .models import ERPLogs


class DummySerializer(serializers.Serializer):
    pass


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

        if org_id is None or entity_id is None:
            return Response("Both fields are required to fetch link token..", status=status.HTTP_400_BAD_REQUEST)

        self.org_id = org_id
        self.entity_id = entity_id
        self.erp_link_token_id = erp_link_token_id

        combined_response = []
        link_token_details = self.get_queryset()
        self.account_token = link_token_details[0]

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
                    self.success_log(success_message=f"API {module_name} executed successfully", label=f"{module_name.replace('_', ' ')}")
    
                else:
                    module_name = api_view_class.__module__
                    if module_name.endswith(".views"):
                        module_name = module_name[:-6]
                    error_message = f"API {module_name} failed with status code {response.status_code}"
                    api_exception = APIException(error_message)
                    api_exception.module_name = module_name
                    raise api_exception

            except APIException as e:
                error_message = str(e)
                module_name = getattr(e, "module_name", "")
                self.log_error(error_message=error_message, label=module_name)

                module_name = api_view_class.__module__
                if module_name.endswith(".views"):
                    module_name = module_name[:-6]

                combined_response.append({
                    'key': f"{module_name}",
                    'label': f"{module_name.replace('_', ' ')}",
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'errorMessage': error_message
                })
    
            except Exception as e:
                error_message = f"An error occurred while calling API {index}: {str(e)}"
                self.log_error(error_message=error_message)
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(combined_response, status=status.HTTP_200_OK)

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