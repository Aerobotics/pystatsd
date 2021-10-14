import os
import time

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

from ..defaults.django import statsd
from ._transform import normalize_url_path



class StatsdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # If the settings are not set in Django settings, just
        # disable the middleware
        # TODO: Issue a warning via a logger
        try:
            self.service_name = settings.SERVICE_NAME
            self.environment = os.getenv("ENVIRONMENT_NAME", "dev")
        except:
            raise MiddlewareNotUsed


    def __call__(self, request):
        start = time.time() 
        response = self.get_response(request)
        response_time = int((time.time() - start) * 1000)

        tags = {
            "service": self.service_name,
            "path": normalize_url_path(request.get_full_path()),
            "method": request.method,
            "status": response.status_code,
            "environment": self.environment 
        }
        statsd.timing("http.requests", response_time, tags=tags)
        return response
