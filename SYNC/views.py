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

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.org_id = None
        self.entity_id = None
        self.erp_link_token_id = None

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
        post_api_views = [
            MergePostTrackingCategories,
            MergeKlooCompanyInsert,
            InsertAccountData,
            MergePostContacts
        ]

        for index, api_view_class in enumerate(post_api_views, start=1):
            try:
                api_instance = api_view_class()
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
                #self.log_error(error_message=error_message, label=module_name)

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
                #self.log_error(error_message=error_message)
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Fetching queryset and constructing response data
        queryset = self.get_queryset()
        if not queryset:
            return Response("No matching records found.", status=status.HTTP_404_NOT_FOUND)

        response_data = []
        for item in queryset:
            response_data.append({
                "id": item[0],  # Adjust the index for link_token_id
                "account_token": item[1]  # Adjust the index for account_token
            })

        combined_response.append({
            "key": "link_token_data",
            "label": "Link Token Data",
            "data": response_data,
            "Status": status.HTTP_200_OK
        })

        list_response = self.list(request, *args, *kwargs)
        combined_response.append(list_response.data)

        return Response(combined_response, status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.org_id is None or self.entity_id is None:
            return ErpLinkToken.objects.none()
        else:
            filter_token = ErpLinkToken.objects.filter(org_id=self.org_id, entity_id=self.entity_id)
            lnk_token = filter_token.values_list('id', 'account_token')

        return lnk_token

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset:
            return Response(f"Both IDs are the required fields.....")

        response_data = []
        for item in queryset:
            response_data.append({
                "id": item[0],
                "account_token": item[1]
            })
        return Response(response_data)

    # def log_error(self, error_message, account_token, label):
    #     # Log the error to the database
    #     log_entry = ERPLogs(
    #         id=uuid.uuid1(),
    #         org_id=self.org_id,
    #         link_token_id=self.erp_link_token_id,
    #         link_token=account_token,
    #         label=label,
    #         sync_start_time=datetime.now(),
    #         sync_end_time=datetime.now(),
    #         sync_status="Failed",
    #         error_message=error_message
    #     )
    #     log_entry.save()