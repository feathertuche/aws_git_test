import logging
import socket
import time
import json

from merge_integration.helper_functions import request_log

request_logger = logging.getLogger(__name__)

class RequestLogMiddleware:
    """Request Logging Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_start_time = time.time()
        response = self.get_response(request)
        request_end_time = time.time()
        response_start_time = time.time()
        response_time = response_start_time - request_start_time
        upstream_time = response_start_time - request_end_time

        log_data = [
            request.META["REMOTE_ADDR"],
            request.method,
            request.get_full_path(),
            response.status_code,
            f"{response_time:.6f}",
            f"{upstream_time:.6f}",
        ]

        request_log(msg=log_data)

        return response