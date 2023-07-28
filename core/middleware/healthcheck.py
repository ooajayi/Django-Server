from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class HealthCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if (request.META["PATH_INFO"] == "/hc/"
                or request.META["PATH_INFO"] == "/hc"):
            return HttpResponse("Alive")
            # return redirect("/health")
