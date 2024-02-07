from datetime import datetime

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import APIException
from COMPANY_INFO.views import MergeKlooCompanyInsert
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATAGORIES.views import MergePostTrackingCategories
import requests
from .model import ERPLogs


class DummySerializer(serializers.Serializer):
    pass


class ProxySyncAPI(CreateAPIView):
    serializer_class = DummySerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        combined_response = {}
        erp_failure_logs = []

        post_api_views = [
            MergePostTrackingCategories,
            MergeKlooCompanyInsert,
            MergePostTaxRates
        ]

        for index, api_view_class in enumerate(post_api_views, start=1):
            try:
                api_instance = api_view_class()
                response = api_instance.post(request)
                response.raise_for_status()
                combined_response[f"merge_response_{index}"] = response.data
            except APIException as a:
                error_message = f"An error occurred while calling API {index}: {str(a)}"
                erp_failure_logs.append({
                    'sync_start_time': datetime.now(),
                    'sync_end_time': datetime.now(),
                    'sync_status': response.status_code if hasattr(response,
                                                                   'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'error_message': error_message
                })
        ERPLogs.objects.bulk_create([ERPLogs(**log) for log in erp_failure_logs])

        if erp_failure_logs:
            return Response(
                {
                    'error': 'One or more API calls failed. Check erp_logs for details.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        else:
            return Response(combined_response, status=status.HTTP_200_OK)
