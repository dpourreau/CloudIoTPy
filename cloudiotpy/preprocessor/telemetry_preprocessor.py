"""
Telemetry Preprocessor module for CloudIoTPy.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TelemetryPreprocessor:
    """
    Provides placeholder methods for telemetry preprocessing.

    The class currently implements three no-op methods:
    1. should_send : always returns True (no filtering).
    2. preprocess_data : returns the data as-is.
    3. _flatten_data : also returns data as-is, but includes placeholder logic
       for flattening nested dictionaries.

    Examples
    --------
    .. code-block:: python

        tp = TelemetryPreprocessor()
        data = {"sensor": {"temperature": 25}}
        if tp.should_send(data):
            processed = tp.preprocess_data(data)
            # proceed with sending...
    """

    def should_send(self, data: Dict[str, Any]) -> bool:
        """
        Decide if the data should be sent to the cloud.

        Parameters
        ----------
        data : Dict[str, Any]
            A dictionary containing telemetry or sensor data.

        Returns
        -------
        bool
            True if data should be sent; currently always True.
        """
        logger.debug("TelemetryPreprocessor.should_send called (no-op)")
        return True

    def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply additional preprocessing steps to the data.

        Parameters
        ----------
        data : Dict[str, Any]
            The dictionary to preprocess.

        Returns
        -------
        Dict[str, Any]
            The possibly transformed/preprocessed dictionary. (Currently
            no changes; returns data as-is.)
        """
        logger.debug("TelemetryPreprocessor.preprocess_data called (no-op)")
        return self._flatten_data(data)

    def _flatten_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten or simplify a data dictionary prior to sending.

        Parameters
        ----------
        data : Dict[str, Any]
            The dictionary of telemetry or sensor data.

        Returns
        -------
        Dict[str, Any]
            The flattened dictionary if any nested structures are found.
            Currently, it returns data as-is unless it can be recursively
            flattened.
        """

        def flatten_dict(d: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
            items = {}
            for k, v in d.items():
                # Replace any '.' in the key with '_'
                k = k.replace(".", "_")
                new_key = f"{parent_key}_{k}" if parent_key else k

                if isinstance(v, dict):
                    # Recurse if the value is another dict
                    items.update(flatten_dict(v, new_key))
                else:
                    items[new_key] = v
            return items

        flattened = flatten_dict(data)
        logger.debug("Flattened data: %s", flattened)
        return flattened
