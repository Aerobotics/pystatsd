import os
import time

from django.core.exceptions import MiddlewareNotUsed

from ..defaults.django import statsd
from ._transform import normalize_url_path


class StatsdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # If the service name is not set, disable the middleware
        # TODO: Issue a warning via a logger
        self.service_name = os.getenv("SERVICE_NAME")
        if self.service_name is None:
            raise MiddlewareNotUsed
        self.environment = os.getenv("ENVIRONMENT_NAME", "dev")

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        response_time = int((time.time() - start) * 1000)

        tags = {
            "service": self.service_name,
            "path": normalize_url_path(request.get_full_path(), include_query_params=False),
            "method": request.method,
            "status": response.status_code,
            "environment": self.environment
        }

        statsd.timing("http.requests", response_time, tags=tags)
        return response
