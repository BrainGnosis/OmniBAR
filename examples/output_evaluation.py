#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Basic Output Evaluation Example
==============================

REAL-WORLD SCENARIO: You built a simple calculator agent and need to test
that it produces correct outputs for different mathematical operations.

This simple example demonstrates OmniBAR's most basic functionality:
evaluating agent outputs using string matching and regex patterns.

Perfect for beginners who want to understand:
- How to create simple agents
- StringEqualityObjective for exact matching
- RegexMatchObjective for pattern matching
- BoolEvalResult for pass/fail testing
- Basic benchmarking workflow

No complex frameworks or dependencies - just pure Python!

LEARNING VALUE:
✅ Start with the simplest possible OmniBAR usage
✅ Understand basic output evaluation patterns
✅ Learn exact matching vs pattern matching
✅ See how to test simple computational agents

Usage:
    python basic/output_evaluation.py
"""

# No environment variables needed for this example!
# This example uses only local string matching - no external APIs required.

from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import StringEqualityObjective, RegexMatchObjective, CombinedBenchmarkObjective
from omnibar.core.types import BoolEvalResult


class SimpleCalculatorAgent:
    """
    A basic calculator agent that performs simple math operations.
    
    This agent demonstrates the most straightforward agent pattern:
    - Takes input parameters
    - Processes them with simple logic
    - Returns structured output
    """
    
    def invoke(self, **kwargs):
        """Process a math operation and return the result."""
        operation = kwargs.get("operation", "")
        a = kwargs.get("a", 0)
        b = kwargs.get("b", 0)
        
        if operation == "add":
            result = a + b
            return {
                "answer": str(result),
                "explanation": f"Adding {a} + {b} = {result}",
                "status": "success"
            }
        elif operation == "multiply":
            result = a * b
            return {
                "answer": str(result),
                "explanation": f"Multiplying {a} × {b} = {result}",
                "status": "success"
            }
        else:
            return {
                "answer": "error",
                "explanation": "Unsupported operation",
                "status": "error"
            }


def create_calculator_agent():
    """Factory function to create the agent."""
    return SimpleCalculatorAgent()


def main():
    """Demonstrate basic output evaluation with different objective types."""
    
    print("🧮 Basic Output Evaluation Example")
    print("=" * 50)
    
    # =============================================================================
    # Example 1: Exact String Matching with BoolEvalResult
    # =============================================================================
    print("\n📋 Example 1: Exact String Matching")
    print("-" * 30)
    
    # Create an objective that checks for exact answer match
    exact_match_objective = StringEqualityObjective(
        name="exact_answer",
        output_key="answer",
        goal="15",  # We expect the answer to be exactly "15"
        valid_eval_result_type=BoolEvalResult  # Returns True/False
    )
    
    # Create a benchmark for addition: 7 + 8 = 15
    addition_benchmark = Benchmark(
        name="Simple Addition",
        input_kwargs={
            "operation": "add",
            "a": 7,
            "b": 8
        },
        objective=exact_match_objective,
        iterations=3  # Run 3 times for consistency
    )
    
    # Run the benchmark
    benchmarker = OmniBarmarker(
        executor_fn=create_calculator_agent,
        executor_kwargs={},
        initial_input=[addition_benchmark]
    )
    
    results = benchmarker.benchmark()
    benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 2: Pattern Matching with Regex
    # =============================================================================
    print("\n📋 Example 2: Pattern Matching with Regex")
    print("-" * 40)
    
    # Create an objective that checks if explanation contains expected patterns
    pattern_objective = RegexMatchObjective(
        name="explanation_pattern",
        output_key="explanation",
        goal=r"Multiplying \d+ × \d+ = \d+",  # Regex pattern for multiplication explanation
        valid_eval_result_type=BoolEvalResult
    )
    
    # Create a benchmark for multiplication: 4 × 6 = 24
    multiplication_benchmark = Benchmark(
        name="Pattern Recognition",
        input_kwargs={
            "operation": "multiply",
            "a": 4,
            "b": 6
        },
        objective=pattern_objective,
        iterations=2
    )
    
    # Run pattern matching benchmark
    pattern_benchmarker = OmniBarmarker(
        executor_fn=create_calculator_agent,
        executor_kwargs={},
        initial_input=[multiplication_benchmark]
    )
    
    results = pattern_benchmarker.benchmark()
    pattern_benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 3: Multiple Objectives Combined
    # =============================================================================
    print("\n📋 Example 3: Combined Multiple Objectives")
    print("-" * 42)
    
    # Create multiple objectives to test different aspects
    answer_objective = StringEqualityObjective(
        name="correct_answer",
        output_key="answer",
        goal="24",
        valid_eval_result_type=BoolEvalResult
    )
    
    status_objective = StringEqualityObjective(
        name="success_status",
        output_key="status", 
        goal="success",
        valid_eval_result_type=BoolEvalResult
    )
    
    explanation_objective = RegexMatchObjective(
        name="valid_explanation",
        output_key="explanation",
        goal=r".*\d+.*=.*\d+.*",  # Contains numbers and equals sign
        valid_eval_result_type=BoolEvalResult
    )
    
    # Combine all objectives
    combined_objective = CombinedBenchmarkObjective(
        name="comprehensive_evaluation",
        objectives=[answer_objective, status_objective, explanation_objective]
    )
    
    # Create a comprehensive benchmark
    comprehensive_benchmark = Benchmark(
        name="Comprehensive Calculator Test",
        input_kwargs={
            "operation": "multiply",
            "a": 4,
            "b": 6
        },
        objective=combined_objective,
        iterations=1
    )
    
    # Run comprehensive benchmark
    comprehensive_benchmarker = OmniBarmarker(
        executor_fn=create_calculator_agent,
        executor_kwargs={},
        initial_input=[comprehensive_benchmark]
    )
    
    results = comprehensive_benchmarker.benchmark()
    comprehensive_benchmarker.print_logger_summary()
    
    print("\n" + "=" * 50)
    print("✅ Basic Output Evaluation Examples Complete!")
    print("\n🎓 Key Learnings:")
    print("   • StringEqualityObjective for exact matching")
    print("   • RegexMatchObjective for pattern matching")
    print("   • BoolEvalResult for pass/fail evaluation")
    print("   • CombinedBenchmarkObjective for multi-aspect testing")
    print("   • Simple agent patterns with structured output")


if __name__ == "__main__":
    main()
