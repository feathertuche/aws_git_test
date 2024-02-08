import uuid
from datetime import datetime

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import APIException
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
# from TAX_RATE.views import MergePostTaxRates
# from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from .model import ERPLogs


class DummySerializer(serializers.Serializer):
    pass


class ProxySyncAPI(CreateAPIView):
    serializer_class = DummySerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

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
        combined_response = {}
        post_api_views = [
            MergePostContacts,
            MergeKlooCompanyInsert
        ]

        for index, api_view_class in enumerate(post_api_views, start=1):
            try:
                api_instance = api_view_class()
                response = api_instance.post(request)

                if response.status_code == status.HTTP_200_OK:
                    combined_response[f"merge_response_{index}"] = response.data

                else:
                    raise APIException(f"API {index} failed with status code {response.status_code}")

            except Exception as e:
                error_message = f"An error occurred while calling API {index}: {str(e)}"
                self.log_error(error_message=error_message)
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(combined_response, status=status.HTTP_200_OK)
