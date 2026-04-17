import logging

from .request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """Attach request id from context to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
