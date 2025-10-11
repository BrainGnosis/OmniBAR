# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Callable, Dict, Any, Type
from pydantic import Field, model_validator
from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult,
    BoolEvalResult,
    InvalidRegexPatternError,
)
import re

class StringEqualityObjective(BaseBenchmarkObjective):
    """
    Benchmark objective that checks if the value of a specified output key in the agent's output
    exactly matches the expected goal string.

    Attributes:
        name (str): The name of the benchmark objective.
        goal (str): The expected string value to compare against.
        output_key (str): The key in the agent's output dictionary to check.
    """
    goal: str
    output_key: str

    # Hide eval_fn and eval_fn_kwargs from users by excluding them from the model schema
    eval_fn_kwargs: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    # Specify the expected type of a valid evaluation result
    valid_eval_result_type: Type[BoolEvalResult] = BoolEvalResult

    @model_validator(mode='after')
    def _validate_objective(self):
        """
        Initialize eval_fn_kwargs after model initialization.
        """
        self.eval_fn_kwargs = {}
        return self

    def _eval_fn(self, goal: str, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Evaluation function that checks if the agent's output for the specified key
        is equal to the goal string.

        Args:
            goal (str): The expected string value.
            formatted_output (Dict[str, Any]): The agent's output dictionary containing the single output key.

        Returns:
            EvalResult: BoolEvalResult indicating whether the output matches the goal.
        """
        # Since formatted_output now contains only one key-value pair, get the single value
        actual_output = next(iter(formatted_output.values()))
        return BoolEvalResult(result=actual_output == goal)

    async def _eval_fn_async(self, goal: str, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)


class RegexMatchObjective(BaseBenchmarkObjective):
    """
    Benchmark objective that checks if the value of a specified output key in the agent's output
    matches a given regular expression pattern.

    Attributes:
        name (str): The name of the benchmark objective.
        goal (str): The regex pattern to match.
        output_key (str): The key in the agent's output dictionary to check.
    """
    goal: str  # The regex pattern to match
    output_key: str

    # Hide eval_fn_kwargs from users by excluding them from the model schema
    eval_fn_kwargs: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    # Specify the expected type of a valid evaluation result
    valid_eval_result_type: Type[BoolEvalResult] = BoolEvalResult

    @model_validator(mode='after')
    def _set_eval_fn(self):
        """
        Initialize eval_fn_kwargs after model initialization.
        """
        self.eval_fn_kwargs = {}
        return self

    def _eval_fn(self, goal: str, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Evaluation function that checks if the agent's output for the specified key
        matches the provided regex pattern.

        Args:
            goal (str): The regex pattern to match.
            formatted_output (Dict[str, Any]): The filtered agent output dictionary containing the single output key.

        Returns:
            BoolEvalResult: True if the output matches the regex, False otherwise.
            InvalidRegexPatternError: If the regex pattern is invalid.
        """
        try:
            # Since formatted_output now contains only one key-value pair, get the single value
            actual_output = next(iter(formatted_output.values()))
            match = re.search(goal, str(actual_output)) is not None
            return BoolEvalResult(result=match)
        except re.error as e:
            return InvalidRegexPatternError(
                result=None,
                message=f"Invalid regex pattern: {e}"
            )

    async def _eval_fn_async(self, goal: str, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Async wrapper that calls the sync evaluation function.
        """
        return self._eval_fn(goal, formatted_output, **kwargs)

