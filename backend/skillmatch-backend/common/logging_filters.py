"""Logging filter that guarantees every record carries a ``request_id``.

The verbose log formatter references ``{request_id}``. Records emitted outside a
request (or by third-party libraries) won't set that attribute, which would make
the formatter raise. This filter supplies a default so logging never fails.
"""
import logging


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id") or record.request_id is None:
            record.request_id = "-"
        return True
