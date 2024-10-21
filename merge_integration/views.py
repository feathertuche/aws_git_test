from django.http import JsonResponse


def health_check(request):
    # Perform any necessary health check logic
    # You can check database connectivity, external dependencies, etc.
    # Return a JSON response indicating the health status
    # For health check

    health_status = {
        "status": "ok",
        "details": "Application is healthy",
    }

    return JsonResponse(health_status)
