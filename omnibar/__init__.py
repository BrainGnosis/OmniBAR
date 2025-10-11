# © 2023 BrainGnosis Inc. All rights reserved.

"""
OmniBAR - Comprehensive AI Agent Benchmarking Framework

A modern, flexible benchmarking framework for evaluating AI agents with support for:
- Multiple evaluation objectives (LLM-based, output-based, path-based, state-based)
- Synchronous and asynchronous execution
- Comprehensive logging and evaluation tracking
- Modular and extensible architecture

Quick Start:
    from omnibar import OmniBarmarker, Benchmark
    from omnibar.objectives import LLMJudgeObjective
    
    # Create a benchmark objective
    objective = LLMJudgeObjective(
        name="response_quality",
        output_key="response",
        goal="The response should be helpful and accurate",
        prompt="Is this response helpful and accurate?"
    )
    
    # Create benchmark
    benchmark = Benchmark(
        name="Test Agent Response",
        input_kwargs={"query": "What is the capital of France?"},
        objective=objective,
        iterations=5
    )
    
    # Run benchmarking
    benchmarker = OmniBarmarker(
        executor_fn=lambda: your_agent,
        executor_kwargs={},
        initial_input=[benchmark]
    )
    
    results = benchmarker.benchmark()

For more information, see the documentation at: https://github.com/BrainGnosis/OmniBAR
"""

from omnibar.version import __version__
from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.core.types import (
    EvalResult,
    ValidEvalResult,
    InvalidEvalResult,
    BoolEvalResult,
    FloatEvalResult,
    AgentOperationError,
    ExtractionError,
    FormattingError,
    EvaluationError,
    EvalTypeMismatchError,
    OutputKeyNotFoundError,
    InvalidRegexPatternError,
)

# Import objectives for easy access
from omnibar.objectives import (
    BaseBenchmarkObjective,
    CombinedBenchmarkObjective,
    LLMJudgeObjective,
    StringEqualityObjective,
    RegexMatchObjective,
    PathEqualityObjective,
    StateEqualityObjective,
)

# Import logging components
from omnibar.logging import BenchmarkLogger, BenchmarkLog, LogEntry

__all__ = [
    # Version
    "__version__",
    
    # Core classes
    "OmniBarmarker",
    "Benchmark",
    
    # Result types
    "EvalResult",
    "ValidEvalResult",
    "InvalidEvalResult",
    "BoolEvalResult",
    "FloatEvalResult",
    "AgentOperationError",
    "ExtractionError",
    "FormattingError",
    "EvaluationError",
    "EvalTypeMismatchError",
    "OutputKeyNotFoundError",
    "InvalidRegexPatternError",
    
    # Objectives
    "BaseBenchmarkObjective",
    "CombinedBenchmarkObjective",
    "LLMJudgeObjective",
    "StringEqualityObjective",
    "RegexMatchObjective", 
    "PathEqualityObjective",
    "StateEqualityObjective",
    
    # Logging
    "BenchmarkLogger",
    "BenchmarkLog",
    "LogEntry",
]
