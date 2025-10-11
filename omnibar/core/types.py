# © 2023 BrainGnosis Inc. All rights reserved.

"""
Type definitions for benchmark evaluation results.

This module defines the type hierarchy for evaluation results used throughout
the OmniBAR framework.
"""

from typing import NamedTuple, Optional, Any

# Base eval result class
class EvalResult(NamedTuple):
    """Base class for all evaluation results."""
    result: Any
    message: Optional[str] = None

# Valid eval result classes
class ValidEvalResult(EvalResult):
    """Base class for valid evaluation results."""
    result: Any

class FloatEvalResult(ValidEvalResult):
    """Evaluation result containing a float value."""
    result: float

class BoolEvalResult(ValidEvalResult):
    """Evaluation result containing a boolean value."""
    result: bool


# Invalid eval result classes
class InvalidEvalResult(EvalResult):
    """Base class for invalid evaluation results."""
    result: None = None

class AgentOperationError(InvalidEvalResult):
    """Error during agent operation."""
    result: None = None

class ExtractionError(InvalidEvalResult):
    """Error during output extraction."""
    result: None = None

class FormattingError(InvalidEvalResult):
    """Error during output formatting."""
    result: None = None

class EvaluationError(InvalidEvalResult):
    """Error during evaluation."""
    result: None = None

class EvalTypeMismatchError(InvalidEvalResult):
    """Error when evaluation result type doesn't match expected type."""
    result: None = None

class OutputKeyNotFoundError(InvalidEvalResult):
    """Error when expected output key is not found."""
    result: None = None

class InvalidRegexPatternError(InvalidEvalResult):
    """Error when regex pattern is invalid."""
    result: None = None

