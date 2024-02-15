import uuid
from datetime import datetime
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.exceptions import APIException
from COMPANY_INFO.views import MergeKlooCompanyInsert
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from .models import ERPLogs


class DummySerializer(serializers.Serializer):
    pass


class ProxySyncAPI(CreateAPIView):
    serializer_class = DummySerializer

    def log_error(self, error_message):
        # Log the error to the database
        log_entry = ERPLogs(
            id=uuid.uuid1(),
            org_id='f246345g55',
            link_token_id='c5ocb9c',
            link_token='v435454g45g4gb544',
            label='errorrrr',
            sync_start_time=datetime.now(),
            sync_end_time=datetime.now(),
            sync_status="Failed",
            error_message=error_message
        )
        log_entry.save()

    def post(self, request, *args, **kwargs):
        combined_response = []
        post_api_views = [
            MergePostTrackingCategories,
            MergeKlooCompanyInsert
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
                        "Status": status.HTTP_200_OK,
                        "successMessage": f"API {{module_name} executed successfully"
                    })
    
                else:
                    error_message = f"API {module_name} failed with status code {response.status_code}"
                    raise APIException(error_message)
    
            except APIException as e:
                error_message = str(e)
                self.log_error(error_message=error_message)
    
                module_name = api_view_class.__module__
                if module_name.endswith(".views"):
                    module_name = module_name[:-6]
    
                combined_response.append({
                    'key': f"{module_name}",
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'errorMessage': error_message
                })
    
            except Exception as e:
                error_message = f"An error occurred while calling API {index}: {str(e)}"
                self.log_error(error_message=error_message)
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(combined_response, status=status.HTTP_200_OK)
