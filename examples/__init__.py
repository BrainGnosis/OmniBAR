# © 2023 BrainGnosis Inc. All rights reserved.

"""
Example usage patterns for OmniBAR.

This module contains comprehensive examples demonstrating various ways to use
the OmniBAR framework for benchmarking AI agents.
"""

import os
from pathlib import Path

# Load environment variables from the root .env file
try:
    from dotenv import load_dotenv
    # Get the root directory of OmniBAR (parent of examples/)
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available
except Exception:
    pass  # .env file not found or other error

