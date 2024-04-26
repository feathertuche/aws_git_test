import logging
import socket
import time

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

        log_data = {
            "time_local": time.strftime('%d/%b/%Y:%H:%M:%S %z'),
            "remote_addr": request.META.get("REMOTE_ADDR", "-"),
            "request_method": request.method,
            "request": request.get_full_path(),
            "request_length": len(request.body),
            "status": response.status_code,
            "bytes_sent": "-",
            "body_bytes_sent": "-",
            "http_referer": request.META.get("HTTP_REFERER", "-"),
            "http_user_agent": request.META.get("HTTP_USER_AGENT", "-"),
            "upstream_addr": "-",
            "upstream_status": "-",
            "request_time": f"{response_time:.6f}",
            "upstream_response_time": f"{upstream_time:.6f}",
            "upstream_connect_time": "-",
            "upstream_header_time": "-",
            "request_body": request.body.decode() if request.body else "-",
        }

        log_message = ('"{time_local}" {remote_addr} '
                       '"{request_method} {request}" '
                       '{request_length} '
                       '{status} {bytes_sent} '
                       '{body_bytes_sent} '
                       '"{http_referer}" '
                       '"{http_user_agent}" '
                       '{upstream_addr} '
                       '{upstream_status} '
                       '{request_time} '
                       '{upstream_response_time} '
                       '{upstream_connect_time} '
                       '{upstream_header_time} '
                       '"{request_body}"').format(**log_data)

        request_logger.info(log_message)

        return response
