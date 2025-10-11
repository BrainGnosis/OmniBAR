# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any
from omnibar.core.benchmarker import OmniBarmarker

__all__ = ["PydanticAIOmniBarmarker"]

class PydanticAIOmniBarmarker(OmniBarmarker):
    """
    Custom OmniBarmarker that handles Pydantic AI agent output conversion.
    
    Pydantic AI returns AgentRunResult objects, but OmniBAR expects dictionaries.
    This class overrides convert_agent_output to handle the conversion.
    """
    
    def convert_agent_output(self, agent_output: Any) -> Dict[str, Any]:
        """
        Convert Pydantic AI AgentRunResult to dictionary format.
        """
        # Handle Pydantic AI AgentRunResult
        if hasattr(agent_output, 'output'):
            output_obj = agent_output.output
            
            # If the output is a Pydantic model, convert to dict
            if hasattr(output_obj, '__dict__'):
                return output_obj.__dict__
            elif hasattr(output_obj, 'model_dump'):
                return output_obj.model_dump()
            elif isinstance(output_obj, dict):
                return output_obj
            else:
                # Fallback: wrap in a generic format
                return {"response": str(output_obj)}
        
        # Fallback to default behavior for other agent types
        return agent_output if isinstance(agent_output, dict) else {"response": str(agent_output)}