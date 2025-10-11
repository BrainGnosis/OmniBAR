# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any, List, Type, Tuple
from pydantic import Field, model_validator, BaseModel, ValidationError
from abc import ABC, abstractmethod
from dataclasses import dataclass
from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult,
    BoolEvalResult,
    InvalidEvalResult,
    FloatEvalResult
)
import json

@dataclass
class PathMatchResult:
    """Result of path matching operation."""
    success: bool
    matched_index: int = -1  # Index of matched path if success=True
    closest_index: int = -1  # Index of closest path if success=False
    errors: List[str] = None  # List of error messages from each path attempt
    similarity_scores: List[float] = None  # Similarity scores for each path (used by partial matching)
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.similarity_scores is None:
            self.similarity_scores = []

# Strategy Pattern Interfaces

class PathMatcher(ABC):
    """Abstract base class for path matching strategies."""
    
    @abstractmethod
    def match_paths(self, output_path: List[Tuple[str, Any]], 
                   valid_paths: List[List[Tuple[str, Type[BaseModel] | None]]]) -> PathMatchResult:
        """Match output path against valid paths and return result."""
        pass

class SimilarityCalculator(ABC):
    """Abstract base class for similarity calculation strategies."""
    
    @abstractmethod
    def calculate_similarity(self, output_path: List[Tuple[str, Any]], 
                           valid_path: List[Tuple[str, Type[BaseModel] | None]]) -> float:
        """Calculate similarity between output and valid path."""
        pass

class PathFormatter(ABC):
    """Abstract base class for path formatting strategies."""
    
    @abstractmethod
    def format_actual_path(self, path: List[Tuple[str, Any]]) -> str:
        """Format an actual output path for logging."""
        pass
        
    @abstractmethod
    def format_expected_path(self, path: List[Tuple[str, Type[BaseModel] | None]]) -> str:
        """Format an expected path for logging."""
        pass

class MessageBuilder(ABC):
    """Abstract base class for message building strategies."""
    
    @abstractmethod
    def build_success_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, expected_path_str: str, 
                            matched_index: int) -> str:
        """Build success message for path matching."""
        pass
        
    @abstractmethod
    def build_failure_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, closest_path_str: str, 
                            output_key: str) -> str:
        """Build failure message for path matching."""
        pass
        
    @abstractmethod
    def build_partial_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, best_path_str: str, 
                            best_index: int, max_similarity: float) -> str:
        """Build message for partial path matching with scores."""
        pass

# Default Strategy Implementations

class ExactPathMatcher(PathMatcher):
    """Default exact path matching strategy that preserves current behavior."""
    
    def match_paths(self, output_path: List[Tuple[str, Any]], 
                   valid_paths: List[List[Tuple[str, Type[BaseModel] | None]]]) -> PathMatchResult:
        """Match paths using exact matching logic from original implementation."""
        errors = []
        
        for path_index, valid_path in enumerate(valid_paths):
            matches, error_msg = self._check_single_path_match(output_path, valid_path, path_index)
            
            if matches:
                return PathMatchResult(success=True, matched_index=path_index, errors=[])
            else:
                errors.append(f"Path {path_index}: {error_msg}")
        
        # No matches found, find closest for debugging
        closest_index = self._find_closest_path_index(output_path, valid_paths)
        
        return PathMatchResult(
            success=False, 
            closest_index=closest_index, 
            errors=errors
        )
    
    def _check_single_path_match(self, output_path: List[Tuple[str, Any]], 
                                valid_path: List[Tuple[str, Type[BaseModel] | None]], 
                                path_index: int) -> Tuple[bool, str]:
        """Check if an output path matches a specific valid path - preserves original logic."""
        if len(output_path) != len(valid_path):
            return False, f"Length mismatch: output has {len(output_path)} steps, expected {len(valid_path)}"
        
        for i in range(len(output_path)):
            output_tool = output_path[i][0]
            output_args = output_path[i][1]
            expected_tool = valid_path[i][0]
            expected_schema = valid_path[i][1]
            
            # Check tool name match
            if expected_tool != output_tool:
                return False, f"Step {i}: tool name '{output_tool}' != expected '{expected_tool}'"
            
            # Check args validation if schema is provided
            if expected_schema is not None:
                try:
                    expected_schema(**output_args)
                except ValidationError as e:
                    # Format detailed validation error messages
                    error_messages = []
                    for error in e.errors():
                        field_path = ".".join(str(loc) for loc in error.get("loc", []))
                        error_type = error.get("type", "unknown")
                        error_msg = error.get("msg", "unknown error")
                        error_messages.append(f"Field '{field_path}': {error_msg} (type: {error_type})")
                    
                    detailed_errors = "; ".join(error_messages)
                    return False, f"Step {i}: args validation failed for tool '{output_tool}' with {len(error_messages)} error(s): {detailed_errors}"
                except Exception as e:
                    return False, f"Step {i}: error validating args for tool '{output_tool}': {e}"
        
        return True, ""
    
    def _find_closest_path_index(self, output_path: List[Tuple[str, Any]], 
                                valid_paths: List[List[Tuple[str, Type[BaseModel] | None]]]) -> int:
        """Find closest matching path index using simple similarity."""
        if not valid_paths:
            return -1
        
        best_similarity = 0.0
        best_index = 0
        
        for i, valid_path in enumerate(valid_paths):
            similarity = self._calculate_simple_similarity(output_path, valid_path)
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = i
        
        return best_index
    
    def _calculate_simple_similarity(self, output_path: List[Tuple[str, Any]], 
                                   valid_path: List[Tuple[str, Type[BaseModel] | None]]) -> float:
        """Simple similarity calculation for finding closest path."""
        if len(output_path) == 0 and len(valid_path) == 0:
            return 1.0
        
        if len(output_path) == 0 or len(valid_path) == 0:
            return 0.0
        
        max_length = max(len(output_path), len(valid_path))
        steps_to_check = min(len(output_path), len(valid_path))
        
        matching_tools = 0
        for i in range(steps_to_check):
            output_tool = output_path[i][0]
            valid_tool = valid_path[i][0]
            if output_tool == valid_tool:
                matching_tools += 1
        
        return matching_tools / max_length

class DefaultSimilarityCalculator(SimilarityCalculator):
    """Default similarity calculator that preserves current PartialPathEqualityObjective behavior."""
    
    def calculate_similarity(self, output_path: List[Tuple[str, Any]], 
                           valid_path: List[Tuple[str, Type[BaseModel] | None]]) -> float:
        """Calculate similarity using the original algorithm."""
        if len(output_path) == 0 and len(valid_path) == 0:
            return 1.0
        
        if len(output_path) == 0 or len(valid_path) == 0:
            return 0.0
        
        # Use length of valid path as the denominator for scoring
        max_length = len(valid_path)
        
        # Score based on matching steps at the same positions
        matching_steps = 0
        steps_to_check = min(len(output_path), len(valid_path))
        
        for i in range(steps_to_check):
            step_score = self._calculate_step_similarity(
                output_path[i], 
                valid_path[i] if i < len(valid_path) else None
            )
            matching_steps += step_score
        
        # Penalize for length mismatch
        length_penalty = abs(len(output_path) - len(valid_path)) / max_length
        
        # Calculate final similarity
        base_similarity = matching_steps / max_length
        final_similarity = max(0.0, base_similarity - length_penalty)
        
        return min(1.0, final_similarity)
    
    def _calculate_step_similarity(self, output_step: Tuple[str, Any], 
                                  valid_step: Tuple[str, Type[BaseModel] | None] | None) -> float:
        """Calculate similarity between a single step - preserves original logic."""
        if valid_step is None:
            return 0.0
        
        output_tool, output_args = output_step
        valid_tool, valid_schema = valid_step
        
        # Tool name must match exactly
        if output_tool != valid_tool:
            return 0.0
        
        # If no schema validation required, tool name match = full score
        if valid_schema is None:
            return 1.0
        
        # Try to validate args against schema
        try:
            valid_schema(**output_args)
            return 1.0  # Perfect match
        except ValidationError as e:
            # Partial credit based on how many fields are valid
            return self._calculate_validation_similarity(output_args, valid_schema, e)
        except Exception:
            return 0.5  # Tool name matches but args are problematic
    
    def _calculate_validation_similarity(self, output_args: Dict[str, Any], 
                                       valid_schema: Type[BaseModel], 
                                       validation_error: ValidationError) -> float:
        """Calculate partial similarity when validation fails - preserves original logic."""
        try:
            total_fields = len(valid_schema.model_fields)
            if total_fields == 0:
                return 0.5  # No fields to validate
            
            # Count the number of validation errors
            error_count = len(validation_error.errors())
            
            # Calculate similarity as (total_fields - error_count) / total_fields
            valid_fields = max(0, total_fields - error_count)
            similarity = valid_fields / total_fields
            
            # Ensure we give some credit for tool name match
            return max(0.1, similarity)
        except:
            return 0.1  # Minimal credit for tool name match

class DefaultPathFormatter(PathFormatter):
    """Default path formatter that preserves current behavior."""
    
    def format_actual_path(self, path: List[Tuple[str, Any]]) -> str:
        """Format actual output path - preserves original logic."""
        if not path:
            return "[]"
        
        formatted_steps = []
        for i, (tool_name, args) in enumerate(path):
            # Truncate args if too long to keep logs readable
            args_str = str(args)
            if len(args_str) > 100:
                args_str = args_str[:100] + "..."
            formatted_steps.append(f"Step {i}: {tool_name}({args_str})")
        
        return "[" + " -> ".join(formatted_steps) + "]"
    
    def format_expected_path(self, path: List[Tuple[str, Type[BaseModel] | None]]) -> str:
        """Format expected path - preserves original logic."""
        if not path:
            return "[]"
        
        formatted_steps = []
        for i, (tool_name, schema) in enumerate(path):
            schema_name = schema.__name__ if schema is not None else "Any"
            formatted_steps.append(f"Step {i}: {tool_name}({schema_name})")
        
        return "[" + " -> ".join(formatted_steps) + "]"

class DefaultMessageBuilder(MessageBuilder):
    """Default message builder that preserves current behavior."""
    
    def build_success_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, expected_path_str: str, 
                            matched_index: int) -> str:
        """Build success message - preserves original logic."""
        return f"Output path matches valid path {matched_index}. " \
               f"Actual path: {actual_path_str}. " \
               f"Matched expected path: {expected_path_str}"
    
    def build_failure_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, closest_path_str: str, 
                            output_key: str) -> str:
        """Build failure message - preserves original logic."""
        error_details = "; ".join(match_result.errors)
        return f"Output path for key {output_key} does not match any valid paths. " \
               f"Actual path: {actual_path_str}. " \
               f"Closest expected path: {closest_path_str}. " \
               f"Errors: {error_details}"
    
    def build_partial_message(self, match_result: PathMatchResult, 
                            actual_path_str: str, best_path_str: str, 
                            best_index: int, max_similarity: float) -> str:
        """Build message for partial path matching - preserves original logic."""
        path_scores = [f"Path {i}: {score:.3f}" for i, score in enumerate(match_result.similarity_scores)]
        scores_summary = "; ".join(path_scores)
        
        if best_index >= 0:
            return f"Best match: Path {best_index} with score {max_similarity:.3f}. " \
                   f"Actual path: {actual_path_str}. " \
                   f"Best expected path: {best_path_str}. " \
                   f"All path scores: {scores_summary}"
        else:
            return f"No valid paths found. " \
                   f"Actual path: {actual_path_str}. " \
                   f"All path scores: {scores_summary}"

class PathEqualityObjective(BaseBenchmarkObjective):
    """
    Extensible benchmark objective that checks if the agent's output path matches any of the valid goal paths.
    
    Uses strategy pattern for customizable path matching, formatting, and messaging.

    Attributes:
        name (str): The name of the benchmark objective.
        goal: List of possible valid paths, each path is a list of (tool_name, schema) tuples
        output_key (str): The key in the agent's output dictionary to check.
        path_matcher: Strategy for matching paths (defaults to exact matching)
        path_formatter: Strategy for formatting paths in messages
        message_builder: Strategy for building result messages
    """
    # Model configuration to allow arbitrary types (strategy classes)
    model_config = {"arbitrary_types_allowed": True}
    
    # List of possible valid paths, each path is a list of (tool_name, schema) tuples
    # str is the tool name, Type[BaseModel] is the schema of the tool input
    goal: List[List[Tuple[str, Type[BaseModel] | None]]]
    output_key: str

    # Pluggable strategies with sensible defaults
    path_matcher: PathMatcher = Field(default_factory=ExactPathMatcher)
    path_formatter: PathFormatter = Field(default_factory=DefaultPathFormatter)
    message_builder: MessageBuilder = Field(default_factory=DefaultMessageBuilder)

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
        for key, value in filtered_output.items():
            if not isinstance(value, list):
                raise ValueError(f"Value for key {key} is not a list")
            # Go through each element in the path
            for i in range(len(value)):
                elem = value[i]
                # If the element is not a tuple, raise an error
                if not isinstance(elem, tuple):
                    raise ValueError(f"Element {elem} is not a tuple")
                # If the second index of the tuple is a BaseModel, convert it to a dict
                if isinstance(elem[1], dict):
                    continue
                if isinstance(elem[1], BaseModel):
                    filtered_output[key][i] = (elem[0], elem[1].model_dump(**kwargs))
                # If the second index of the tuple is a string, convert it to a dict
                elif isinstance(elem[1], str):
                    # Try to convert the string to a dict
                    try:
                        filtered_output[key][i] = (elem[0], json.loads(elem[1], **kwargs))
                    except json.JSONDecodeError:
                        raise ValueError(f"Element {elem} is not a valid JSON string")
                # If the second index of the tuple is not a BaseModel or a string, raise an error
                else:
                    raise ValueError(f"Element {elem} is not a valid type")

        return filtered_output

    async def _format_filtered_output_async(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Async wrapper that calls the sync format function.
        """
        return self._format_filtered_output(filtered_output, **kwargs)

    def _eval_fn(self, goal: List[List[Tuple[str, Type[BaseModel] | None]]], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Evaluate if the output path matches any of the valid goal paths using pluggable strategies.
        
        Args:
            goal: List of valid paths, each path is a list of (tool_name, schema) tuples
            formatted_output: Dict containing the actual output path (single key-value pair)
            
        Returns:
            BoolEvalResult with success/failure and detailed message
        """
        # Extract path and key from formatted output
        key = next(iter(formatted_output.keys()))
        value = next(iter(formatted_output.values()))
        
        if not isinstance(value, list):
            return InvalidEvalResult(result=None, message=f"Value for key {key} is not a list")
        
        # Use strategy pattern for path matching
        match_result = self.path_matcher.match_paths(value, goal)
        
        # Use strategy pattern for path formatting
        actual_path_str = self.path_formatter.format_actual_path(value)
        
        # Use strategy pattern for message building
        if match_result.success:
            expected_path_str = self.path_formatter.format_expected_path(goal[match_result.matched_index])
            message = self.message_builder.build_success_message(
                match_result, actual_path_str, expected_path_str, match_result.matched_index
            )
            return BoolEvalResult(result=True, message=message)
        else:
            closest_path_str = "N/A"
            if match_result.closest_index >= 0 and match_result.closest_index < len(goal):
                closest_path_str = self.path_formatter.format_expected_path(goal[match_result.closest_index])
                
            message = self.message_builder.build_failure_message(
                match_result, actual_path_str, closest_path_str, key
            )
            return BoolEvalResult(result=False, message=message)
    

    async def _eval_fn_async(self, goal: List[List[Tuple[str, Type[BaseModel] | None]]], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)


class PartialPathEqualityObjective(PathEqualityObjective):
    """
    Extensible path equality objective that returns a similarity score instead of binary pass/fail.
    Returns the best match score across all valid paths (0.0 to 1.0).
    
    Uses strategy pattern for customizable similarity calculation, formatting, and messaging.

    Attributes:
        name (str): The name of the benchmark objective.
        goal: List of possible valid paths, each path is a list of (tool_name, schema) tuples
        output_key (str): The key in the agent's output dictionary to check.
        similarity_calculator: Strategy for calculating path similarities
    """
    # Model configuration to allow arbitrary types (strategy classes)
    model_config = {"arbitrary_types_allowed": True}
    
    # Additional strategy for similarity calculation
    similarity_calculator: SimilarityCalculator = Field(default_factory=DefaultSimilarityCalculator)
    
    valid_eval_result_type: Type[FloatEvalResult] = FloatEvalResult

    def _eval_fn(self, goal: List[List[Tuple[str, Type[BaseModel] | None]]], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Evaluate similarity between output paths and valid paths using pluggable strategies.
        
        Returns:
            FloatEvalResult with the best similarity score (0.0 to 1.0) and detailed message
        """
        # Handle empty output
        if not formatted_output:
            return FloatEvalResult(result=0.0, message="Empty formatted output")
        
        # Extract path and key from formatted output
        key = next(iter(formatted_output.keys()))
        value = next(iter(formatted_output.values()))
        
        if not isinstance(value, list):
            return InvalidEvalResult(result=None, message=f"Value for key {key} is not a list")
        
        # Calculate similarity scores using strategy pattern
        max_similarity = 0.0
        similarity_scores = []
        best_path_index = -1
        
        for path_index, valid_path in enumerate(goal):
            similarity = self.similarity_calculator.calculate_similarity(value, valid_path)
            similarity_scores.append(similarity)
            if similarity > max_similarity:
                max_similarity = similarity
                best_path_index = path_index
        
        # Create match result with similarity scores
        match_result = PathMatchResult(
            success=max_similarity > 0.0,
            matched_index=best_path_index if max_similarity > 0.0 else -1,
            closest_index=best_path_index,
            similarity_scores=similarity_scores
        )
        
        # Use strategy pattern for formatting and message building
        actual_path_str = self.path_formatter.format_actual_path(value)
        
        best_path_str = ""
        if best_path_index >= 0:
            best_path_str = self.path_formatter.format_expected_path(goal[best_path_index])
        
        message = self.message_builder.build_partial_message(
            match_result, actual_path_str, best_path_str, best_path_index, max_similarity
        )
        
        return FloatEvalResult(result=max_similarity, message=message)
    

    async def _eval_fn_async(self, goal: List[List[Tuple[str, Type[BaseModel] | None]]], formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)