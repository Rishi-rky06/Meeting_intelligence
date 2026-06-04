"""
TraceID middleware — reads X-Trace-ID header or generates one, attaches to request.
"""

import uuid
import logging
from core.logging_formatter import set_trace_context, set_response_status

logger = logging.getLogger(__name__)


class TraceIDMiddleware:
    """Injects a trace_id into every request and logs basic request/response info."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = request.META.get('HTTP_X_TRACE_ID') or str(uuid.uuid4())
        request.trace_id = trace_id

        set_trace_context(
            trace_id=trace_id,
            method=request.method,
            path=request.path,
        )

        logger.info(f"Request started: {request.method} {request.path}")

        response = self.get_response(request)

        set_response_status(str(response.status_code))
        logger.info(f"Request completed: {response.status_code}")

        response['X-Trace-ID'] = trace_id
        return response
