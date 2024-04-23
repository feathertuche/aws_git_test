from django.http import JsonResponse

from merge_integration.helper_functions import api_log, request_log


def health_check(request):
    # Perform any necessary health check logic
    # You can check database connectivity, external dependencies, etc.
    # Return a JSON response indicating the health status
    # For health check

    api_log(msg="HEALTHCHECK: Performing health check")
    request_log(
        msg=f"HEALTHCHECK: Request received for health check from {request.META.get('REMOTE_ADDR')}"
    )

    health_status = {
        "status": "ok",
        "details": "Application is healthy",
    }

    return JsonResponse(health_status)
