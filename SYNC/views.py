from threading import Thread

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from .helper_function import start_sync_process
from .models import ERPLogs
from .queries import get_link_token
from .serializers import ProxyReSyncSerializer


class ProxySyncAPI(CreateAPIView):
    def post(self, request, *args, **kwargs):
        # validate the request using serializer
        serializer = ProxyReSyncSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # check if link token id is present
        link_token_details = get_link_token(
            serializer.validated_data["erp_link_token_id"]
        )
        if link_token_details is None:
            response_data = {"message": "Sync still pending", "retry": 1}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        api_log(msg=f"SYNC :link token details{link_token_details}")

        # check the status of the modules in merge
        account_token = link_token_details

        thread = Thread(
            target=start_sync_process,
            args=(
                request,
                serializer.validated_data["erp_link_token_id"],
                serializer.validated_data["org_id"],
                account_token,
            ),
        )

        thread.start()

        return Response(
            {"message": "Sync Process Started Successfully"},
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
