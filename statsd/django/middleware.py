import time

from django.conf import settings
from ..defaults.django import statsd


class StatsdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.service_name = settings.SERVICE_NAME


    def __call__(self, request):
        start = time.time() 
        response = self.get_response(request)
        response_time = int((time.time() - start) * 1000)

        tags = {
            "service": self.service_name,
            "path": request.path,
            "method": request.method,
            "status": response.status_code,
        }
        statsd.timing("http.requests", response_time, tags=tags)
        return response