from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from ACCOUNTS.views import InsertAccountData
from COMPANY_INFO.views import MergeKlooCompanyInsert
from CONTACTS.views import MergePostContacts
from LINKTOKEN.model import ErpLinkToken
from TRACKING_CATEGORIES.views import MergePostTrackingCategories
from merge_integration.helper_functions import api_log
from services.merge_service import MergeSyncService
from .helper_function import sync_modules_status
from .models import ERPLogs
from .queries import get_link_token, get_erplogs_by_link_token_id
from .serializers import ProxyReSyncSerializer


class ProxySyncAPI(CreateAPIView):
    def post(self, request, *args, **kwargs):
        # validate the request using serializer
        serializer = ProxyReSyncSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # check if link token id is present
        link_token_details = get_link_token(
            serializer.validated_data["org_id"], serializer.validated_data["entity_id"]
        )
        if link_token_details is None:
            response_data = {"message": "Sync still pending", "retry": 1}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        api_log(msg=f"SYNC :link token details{link_token_details}")

        # check the status of the modules in merge
        account_token = link_token_details

        merge_client = MergeSyncService(account_token)
        sync_status_response = merge_client.sync_status()
        if not sync_status_response["status"]:
            response_data = {
                "error": "Seems the connection is lost. Please disconnect and reconnect.",
                "retry": 0,
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # check if all modules are done syncing
        sync_status_result = sync_status_response["data"].results
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
        response_data = get_erplogs_by_link_token_id(
            serializer.validated_data["erp_link_token_id"]
        )
        api_log(msg=f"SYNC :ERP Log Data {response_data}")
        api_views = {
            "TRACKING CATEGORIES": (
                MergePostTrackingCategories,
                {"link_token_details": link_token_details},
            ),
            "COMPANY INFO": (
                MergeKlooCompanyInsert,
                {"link_token_details": link_token_details},
            ),
            "ACCOUNTS": (InsertAccountData, {"link_token_details": link_token_details}),
            "CONTACTS": (
                MergePostContacts,
                {"link_token_details": link_token_details},
            ),
        }

        # if logs are present check if any module is failed
        post_api_views = []
        if response_data:
            for log in response_data:
                if log["sync_status"] == "failed":
                    post_api_views.append(api_views[log["label"]])

            # if all modules are successfull return the response
            if not post_api_views:
                return Response(
                    {"response_data": response_data, "retry": 0},
                    status=status.HTTP_200_OK,
                )

        # if logs are not present then add all the modules to the post_api_views
        if not post_api_views:
            post_api_views = list(api_views.values())

        api_log(msg=f"SYNC :post_api_views {post_api_views}")

        sync_modules_status(
            request,
            link_token_details,
            serializer.validated_data["org_id"],
            serializer.validated_data["erp_link_token_id"],
            account_token,
            post_api_views,
        )

        # Return the combined response and response_data dictionary
        response_data = get_erplogs_by_link_token_id(
            serializer.validated_data["erp_link_token_id"]
        )
        return Response(
            {"response_data": response_data, "retry": 0},
            status=status.HTTP_200_OK,
        )


class ProxyReSyncAPI(CreateAPIView):
    """
    API to resync the data for the given link token
    """

    def post(self, request, *args, **kwargs):
        """
        API to resync the data for the given link token
        """

        # validate the request using serializer
        serializer = ProxyReSyncSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get link token
        link_token_id = ErpLinkToken.custom_manager.get_link_token(
            serializer.validated_data["org_id"], serializer.validated_data["entity_id"]
        )
        if link_token_id is None:
            return Response(
                "Link token not found",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check the ERP logs table for the given link token
        erp_logs = ERPLogs.custom_manager.get_erp_logs(
            serializer.validated_data["erp_link_token_id"]
        )
        if not erp_logs:
            return Response(
                "Sync still pending",
                status=status.HTTP_202_ACCEPTED,
            )
