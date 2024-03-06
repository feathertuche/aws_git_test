from merge.core.api_error import ApiError
from rest_framework import status, serializers
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from merge_integration.utils import create_merge_client
from .helper_function import sync_modules_status
from .models import ERPLogs


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
        self.org_id = request.data.get("org_id")
        self.entity_id = request.data.get("entity_id")
        self.erp_link_token_id = request.data.get("erp_link_token_id")

        # check if org and entity id are present
        if self.org_id is None or self.entity_id is None:
            return Response(
                "Both fields are required to fetch link token..",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if link token id is present
        link_token_details = self.get_queryset()
        if link_token_details is None:
            response_data = {"message": "Sync still pending", "retry": 1}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        api_log(msg=f"SYNC :link token details{link_token_details}")

        # check the status of the modules in merge
        self.account_token = link_token_details[0]
        tc_client = create_merge_client(self.account_token)
        try:
            sync_status = tc_client.accounting.sync_status.list()
        except ApiError as e:
            api_log(msg=f"SYNC :API MERGE Error {e}")
            response_data = {
                "error": "Seems the connection is lost. Please disconnect and reconnect.",
                "retry": 0,
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # check if all modules are done syncing
        sync_status_result = sync_status.results
        modules = ["TrackingCategory", "CompanyInfo", "Account", "Contact"]
        sync_module_status = []
        for module in modules:
            for sync_filter_array in sync_status_result:
                if sync_filter_array.model_name == module:
                    if sync_filter_array.status == "DONE":
                        sync_module_status.append(sync_filter_array.model_name)

        # match the modules and sync_module_status
        if set(modules) != set(sync_module_status):
            response_data = {"message": "Sync still pending", "retry": 1}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)

        # check if the logs are present in the database
        response_data = get_erplogs_by_link_token_id(self.erp_link_token_id)
        api_log(msg=f"SYNC :ERP Log Data {response_data}")

        # if logs are present, return the logs
        if response_data:
            return Response(
                {"response_data": response_data, "retry": 0},
                status=status.HTTP_200_OK,
            )

        sync_modules_status(
            request,
            link_token_details,
            self.org_id,
            self.erp_link_token_id,
            self.account_token,
        )

        # Return the combined response and response_data dictionary
        response_data = get_erplogs_by_link_token_id(self.erp_link_token_id)
        return Response(
            {"response_data": response_data, "retry": 0},
            status=status.HTTP_200_OK,
        )

    def get_queryset(self):
        if self.org_id is None or self.entity_id is None:
            return ErpLinkToken.objects.none()
        else:
            filter_token = ErpLinkToken.objects.filter(
                org_id=self.org_id, entity_id=self.entity_id
            )
            lnk_token = filter_token.values_list("account_token", flat=1)

        return lnk_token
