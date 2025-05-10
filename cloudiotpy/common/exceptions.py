"""
Common error handling utilities for CloudIoTPy.
"""

import functools
import logging
from typing import Any, Callable, TypeVar, cast

try:
    from azure.iot.device.exceptions import ClientError
except ImportError:
    ClientError = None

try:
    from paho.mqtt.client import MQTTException
except ImportError:
    MQTTException = None

try:
    from botocore.exceptions import ClientError as BotoClientError
except ImportError:
    BotoClientError = None


T = TypeVar("T")

logger = logging.getLogger(__name__)


class IoTClientError(Exception):
    """
    Custom exception class for IoT client errors.
    """

    pass


def handle_exceptions(
    default_return_value: Any = None, log_exception: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for standardized exception handling across the codebase.

    Parameters
    ----------
    default_return_value : Any, optional
        Value to return if an exception occurs, by default None.
        Should match the expected return type of the decorated function.
        Common values include None, False, [], {}, or 0 depending on context.
    log_exception : bool, optional
        Whether to log the full exception traceback (True) or just the message
        (False), by default True.

    Returns
    -------
    Callable[[Callable[..., T]], Callable[..., T]]
        The decorated function with standardized exception handling.

    Examples
    --------
    .. code-block:: python

        @handle_exceptions(default_return_value={})
        def get_data():
            return fetch_data_from_external_source()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                if log_exception:
                    logger.exception("Connection error in %s: %s", func.__name__, e)
                else:
                    logger.error("Connection error in %s: %s", func.__name__, e)
                return default_return_value
            except ValueError as e:
                if log_exception:
                    logger.exception("Value error in %s: %s", func.__name__, e)
                else:
                    logger.error("Value error in %s: %s", func.__name__, e)
                return default_return_value
            except FileNotFoundError as e:
                if log_exception:
                    logger.exception("File not found error in %s: %s", func.__name__, e)
                else:
                    logger.error("File not found error in %s: %s", func.__name__, e)
                return default_return_value
            except PermissionError as e:
                if log_exception:
                    logger.exception("Permission error in %s: %s", func.__name__, e)
                else:
                    logger.error("Permission error in %s: %s", func.__name__, e)
                return default_return_value
            except BotoClientError as e:
                if log_exception:
                    logger.exception("AWS Client error in %s: %s", func.__name__, e)
                else:
                    logger.error("AWS Client error in %s: %s", func.__name__, e)
                return default_return_value
            except MQTTException as e:
                if log_exception:
                    logger.exception("MQTT error in %s: %s", func.__name__, e)
                else:
                    logger.error("MQTT error in %s: %s", func.__name__, e)
                return default_return_value
            except Exception as e:
                if ClientError is not None and isinstance(e, ClientError):
                    if log_exception:
                        logger.exception("Azure Client error in %s: %s", func.__name__, e)
                    else:
                        logger.error("Azure Client error in %s: %s", func.__name__, e)
                    return default_return_value
                else:
                    if log_exception:
                        logger.exception("Unexpected error in %s: %s", func.__name__, e)
                    else:
                        logger.error("Unexpected error in %s: %s", func.__name__, e)
                    return default_return_value

        return cast(Callable[..., T], wrapper)

    return decorator
