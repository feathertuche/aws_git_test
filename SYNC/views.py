from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from COMPANY_INFO.views import MergeKlooCompanyInsert
from TAX_RATE.views import MergePostTaxRates
from TRACKING_CATAGORIES.views import MergePostTrackingCategories


class DummySerializer(serializers.Serializer):
    pass


class ProxySyncAPI(CreateAPIView):
    serializer_class = DummySerializer

    def post(self, request, *args, **kwargs):
        combined_response = {}

        post_api_views = [
            MergePostTrackingCategories,
            MergeKlooCompanyInsert,
            MergePostTaxRates
        ]

        for index, api_view_class in enumerate(post_api_views, start=1):
            try:
                api_instance = api_view_class()
                response = api_instance.post(request)
                if response.status_code == status.HTTP_200_OK:
                    combined_response[f"merge_response_{index}"] = response.data
                else:
                    raise Exception(f"API {index} failed with status code {response.status_code}")
            except Exception as e:
                error_message = f"An error occurred while calling API {index}: {str(e)}"
                return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(combined_response, status=status.HTTP_200_OK)