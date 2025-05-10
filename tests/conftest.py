"""
Configuration file for pytest.

This file is automatically loaded by pytest and helps with test configuration.
It adds the project root directory to the Python path, allowing imports from the sensorpy directory.
"""

from pathlib import Path
import sys

# Add the project root directory to the Python path (one level above tests)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
