# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any, List, Type
from pydantic import Field, model_validator, BaseModel, ValidationError
from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult,
    BoolEvalResult,
    InvalidEvalResult,
    FloatEvalResult
)
import json

class StateEqualityObjective(BaseBenchmarkObjective):
    """
    Benchmark objective that validates if the agent's output matches a Pydantic model schema.

    Attributes:
        name (str): The name of the benchmark objective.
        goal: The Pydantic model type to validate against.
        output_key (str): The key in the agent's output dictionary to check.
    """
    goal: Type[BaseModel]
    output_key: str

    eval_fn_kwargs: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    valid_eval_result_type: Type[BoolEvalResult] = BoolEvalResult

    @model_validator(mode='after')
    def _validate_objective(self):
        """
        Automatically set eval_fn to the private _eval_fn method after model initialization.
        """
        self.eval_fn_kwargs = {}
        return self
    
    def _format_filtered_output(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        '''
        Helper function to format filtered output after extrace
        '''
        for key, value in filtered_output.items():
            if isinstance(value, str):
                filtered_output[key] = json.loads(value, **kwargs)
            elif isinstance(value, BaseModel):
                filtered_output[key] = value.model_dump(**kwargs)
        return filtered_output

    async def _format_filtered_output_async(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Async wrapper that calls the sync format function.
        """
        return self._format_filtered_output(filtered_output, **kwargs)

    def _eval_fn(self, goal: Type[BaseModel], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        # Since formatted_output now contains only one key-value pair, get the single value
        element = next(iter(formatted_output.values()))
        try:
            goal(**element)
            return BoolEvalResult(result=True)
        except (ValidationError, Exception) as e:
            if isinstance(e, ValidationError):
                # Format validation error messages
                error_messages = []
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error.get("loc", []))
                    error_type = error.get("type", "unknown")
                    error_msg = error.get("msg", "unknown error")
                    error_messages.append(f"Field '{field_path}': {error_msg} (type: {error_type})")
                
                validation_message = f"Validation failed with {len(error_messages)} error(s): " + "; ".join(error_messages)
                return BoolEvalResult(result=False, message=validation_message)
            else:
                return InvalidEvalResult(result=None, message=str(e))

    async def _eval_fn_async(self, goal: Type[BaseModel], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)
    

class PartialStateEqualityObjective(StateEqualityObjective):
    """
    Partial state equality objective that returns a similarity score (0.0 to 1.0)
    based on how many fields pass validation.

    Attributes:
        name (str): The name of the benchmark objective.
        goal: The Pydantic model type to validate against.
        output_key (str): The key in the agent's output dictionary to check.
    """
    valid_eval_result_type: Type[FloatEvalResult] = FloatEvalResult

    def _eval_fn(self, goal: Type[BaseModel], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        # Calculate the number of fields defined in the goal Pydantic model
        def count_fields(model: Type[BaseModel]) -> int:
            count = 0
            for field in model.model_fields.values():
                field_type = field.annotation
                # Check for nested BaseModel (Pydantic v2+)
                origin = getattr(field_type, "__origin__", None)
                if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                    count += count_fields(field_type)
                elif origin in (list, List):
                    # Handle List[BaseModel] or similar
                    args = getattr(field_type, "__args__", ())
                    if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                        count += count_fields(args[0])
                    else:
                        count += 1
                else:
                    count += 1
            return count

        # Since formatted_output now contains only one key-value pair, get the single value
        element = next(iter(formatted_output.values()))
        total_fields = count_fields(goal)
        failed_fields = 0
        
        validation_message = None
        try:
            goal(**element)
        except ValidationError as e:
            # Count unique field paths that failed, not total errors
            unique_failed_fields = set()
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error.get("loc", []))
                error_type = error.get("type", "unknown")
                error_msg = error.get("msg", "unknown error")
                unique_failed_fields.add(field_path)
                error_messages.append(f"Field '{field_path}': {error_msg} (type: {error_type})")
            
            failed_fields += len(unique_failed_fields)
            validation_message = f"Validation failed with {len(error_messages)} error(s): " + "; ".join(error_messages)
        except Exception as e:
            # If a non-ValidationError occurs, this will be invalid eval result
            return InvalidEvalResult(result=None, message=str(e))
        
        # Calculate the pass rate for this element (ensure non-negative)
        passed_fields = max(0, total_fields - failed_fields)
        result = passed_fields / total_fields if total_fields > 0 else 0.0
        return FloatEvalResult(result=float(result), message=validation_message)

    async def _eval_fn_async(self, goal: Type[BaseModel], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)