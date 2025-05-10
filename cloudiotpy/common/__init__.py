"""
Common utilities for CloudIoTPy.

Notes
-----
This package contains utilities and helper functions that are used across
multiple modules in the CloudIoTPy project. It centralizes exception classes,
logging configurations, and other cross-cutting concerns.
"""

from cloudiotpy.common.exceptions import IoTClientError, handle_exceptions
from cloudiotpy.common.logging_setup import setup_global_logging

__all__ = [
    "IoTClientError",
    "handle_exceptions",
    "setup_global_logging",
]
