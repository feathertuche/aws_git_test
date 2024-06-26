from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from merge_integration.helper_functions import api_log
from services.merge_service import MergeItemsApiService


# Create your views here.
class MergeItemCreate(APIView):
    """
    API to create invoices in the kloo Invoices system.
    """

    def __init__(self, link_token_details=None, last_modified_at=None):
        super().__init__()
        self.link_token_details = link_token_details
        self.last_modified_at = last_modified_at

    def post(self, request):
        """
        Handles POST requests to insert data to the kloo Invoices system.

        Returns:
            Response indicating success or failure of data insertion.
        """

        erp_link_token_id = request.data.get("erp_link_token_id")
        org_id = request.data.get("org_id")

        merge_items_api_service = MergeItemsApiService(
            self.link_token_details, org_id, erp_link_token_id
        )
        items_response = merge_items_api_service.get_items(self.last_modified_at)

        try:
            if items_response["status"]:
                api_log(msg=f"ITEMS : Processing {len(items_response['data'])} Items")

                if len(items_response["data"]) == 0:
                    return Response(
                        {
                            "message": "No new data found to insert in the kloo Items system"
                        },
                        status=status.HTTP_204_NO_CONTENT,
                    )

                api_log(msg="Data inserted successfully in the kloo Items system")
                return Response({"message": "API Invoice Info completed successfully"})

            api_log(msg="Failed to send data to Kloo Items API")
            return Response(
                {"error": "Failed to send data to Kloo Items API"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            error_message = f"Failed to send data to Kloo Items API. Error: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
