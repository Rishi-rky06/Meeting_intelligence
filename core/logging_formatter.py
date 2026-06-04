"""
Custom structured logging formatter.
Produces: timestamp | trace_id | level | method | path | status | message
"""

import logging
import threading

_local = threading.local()


def set_trace_context(trace_id: str, method: str = '', path: str = ''):
    """Store request context in thread-local for log lines."""
    _local.trace_id = trace_id
    _local.method = method
    _local.path = path
    _local.status = ''


def set_response_status(status: str):
    """Update the response status in thread-local after the view runs."""
    _local.status = status


class StructuredFormatter(logging.Formatter):
    """Formats log records with trace context fields."""

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(_local, 'trace_id', '-')
        method = getattr(_local, 'method', '-')
        path = getattr(_local, 'path', '-')
        status = getattr(_local, 'status', '-')

        timestamp = self.formatTime(record, '%Y-%m-%dT%H:%M:%S')
        level = record.levelname

        message = record.getMessage()
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)

        return f"{timestamp} | {trace_id} | {level} | {method} | {path} | {status} | {message}"
