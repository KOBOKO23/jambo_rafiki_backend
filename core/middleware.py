import uuid

from .request_context import reset_request_id, set_request_id


class RequestIdMiddleware:
    """Attach a request id to context/logging and propagate it in responses."""

    header_name = 'HTTP_X_REQUEST_ID'
    response_header_name = 'X-Request-ID'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or uuid.uuid4().hex
        token = set_request_id(request_id)
        request.request_id = request_id
        try:
            response = self.get_response(request)
        finally:
            reset_request_id(token)

        response[self.response_header_name] = request_id
        return response
