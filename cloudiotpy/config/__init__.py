"""Expose the shared ConfigLoader instance."""

import logging
from cloudiotpy.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

config = ConfigLoader()
config.load_config()

__all__ = ["config"]
