from merge.resources.accounting import CategoriesEnum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from merge_integration.utils import create_merge_client
import sys


class LinkToken(APIView):
    def post(self, request):
        try:
            merge_client = create_merge_client()
            link_token_response = merge_client.ats.link_token.create(
                end_user_email_address=request.data.get("end_user_email_address"),
                end_user_organization_name=request.data.get("end_user_organization_name"),
                end_user_origin_id=request.data.get("end_user_origin_id"),
                categories=[CategoriesEnum.ATS],
                should_create_magic_link_url=request.data.get("should_create_magic_link_url"),
                link_expiry_mins=30,
            )
            return Response(link_token_response, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
