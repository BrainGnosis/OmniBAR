# © 2023 BrainGnosis Inc. All rights reserved.

"""
Pydantic AI Integration for OmniBAR

This module provides seamless integration between OmniBAR and Pydantic AI agents.
It includes a specialized benchmarker that handles Pydantic AI's AgentRunResult objects
and converts them to the dictionary format expected by OmniBAR objectives.

Key components:
- PydanticAIOmniBarmarker: Custom benchmarker with output conversion for Pydantic AI
"""

from .benchmarker import PydanticAIOmniBarmarker

__all__ = ["PydanticAIOmniBarmarker"]
