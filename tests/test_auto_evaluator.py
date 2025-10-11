#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Auto-Evaluator Assignment Examples for OmniBAR
================================================

This test file demonstrates how to use OmniBAR's automatic evaluator assignment
feature to automatically analyze benchmark results without manual configuration.

Key Features Demonstrated:
- Default auto-evaluator assignment based on result types
- Custom evaluator mapping for specialized analysis
- Disabling auto-assignment when not needed
- Accessing evaluation results for post-processing

Use Cases:
- Automated pass/fail rate calculation
- Custom metrics generation
- Integration with monitoring systems
- Batch analysis of benchmark results

Author: OmniBAR Team
License: Apache 2.0
"""

from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.output import StringEqualityObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult
from omnibar.logging.evaluator import BaseEvaluator, BooleanEvaluator
from omnibar.logging import LogEntry
from typing import Dict, Any, List


class SimpleAgent:
    """
    Example agent that processes queries with varying success rates.
    
    This agent demonstrates a realistic scenario where performance varies
    based on input characteristics. It's designed to generate both successful
    and failed results for comprehensive testing.
    """
    
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Process a query and return structured results.
        
        Args:
            **kwargs: Input parameters. Expected to contain 'query' key.
            
        Returns:
            Dict containing:
            - status: 'success' or 'failed' based on processing outcome
            - confidence: Float between 0.0-1.0 indicating confidence level
            - message: Descriptive message about the processing result
        """
        query = kwargs.get("query", "")
        
        # Simulate varying success rates based on input
        success_rate = 0.8 if "good" in query else 0.3
        
        return {
            "status": "success" if success_rate > 0.5 else "failed",
            "confidence": success_rate,
            "message": f"Processed: {query}"
        }


def create_agent():
    return SimpleAgent()


class CustomBooleanEvaluator(BaseEvaluator):
    """
    Custom evaluator that extends BooleanEvaluator with additional metrics.
    
    This example demonstrates how to create custom evaluators that build upon
    existing ones while adding domain-specific metrics. Useful for:
    - Adding business-specific KPIs
    - Integrating with monitoring systems
    - Generating specialized reports
    """
    
    def _eval(self, log_entries: List["LogEntry"]) -> Dict[str, Any]:
        """
        Evaluate log entries and return extended metrics.
        
        Args:
            log_entries: List of LogEntry objects from benchmark execution
            
        Returns:
            Dict containing standard BooleanEvaluator metrics plus:
            - custom_success_percentage: Pass rate as percentage (0-100)
            - custom_total_attempts: Total number of attempts evaluated
        """
        # Get standard boolean evaluation metrics
        bool_eval = BooleanEvaluator()
        results = bool_eval._eval(log_entries)
        
        # Add custom metrics for specialized use cases
        results["custom_success_percentage"] = results["pass_rate"] * 100
        results["custom_total_attempts"] = len(log_entries)
        
        return results


def main():
    """
    Demonstrate auto-evaluator assignment with different configurations.
    
    This function shows three different ways to use auto-evaluators:
    1. Default assignment - automatic evaluator selection based on result types
    2. Custom assignment - mapping specific result types to custom evaluators
    3. Disabled assignment - manual control over evaluation process
    """
    
    print("🚀 Auto-Evaluator Assignment Example")
    print("=" * 40)
    
    # Create objectives that will generate BoolEvalResult outputs
    # This allows us to demonstrate evaluator assignment for boolean results
    status_objective = StringEqualityObjective(
        name="StatusCheck",
        goal="success",  # Looking for "success" in the status field
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    # Create test benchmarks with different expected outcomes
    # These will generate different success/failure patterns for evaluation
    benchmarks = [
        Benchmark(
            name="GoodCase",
            input_kwargs={"query": "good_test_case"},  # Will trigger success behavior
            objective=status_objective,
            iterations=3,
            verbose=False
        ),
        Benchmark(
            name="BadCase", 
            input_kwargs={"query": "bad_test_case"},   # Will trigger failure behavior
            objective=status_objective,
            iterations=2,
            verbose=False
        )
    ]
    
    # ============================================================================
    # EXAMPLE 1: Default Auto-Assignment
    # ============================================================================
    print("📋 Example 1: Default Auto-Assignment")
    print("-" * 35)
    
    # When auto_assign_evaluators=True (default), OmniBAR automatically
    # assigns appropriate evaluators based on the result types:
    # - BoolEvalResult → BooleanEvaluator
    # - FloatEvalResult → FloatEvaluator (if available)
    # - etc.
    benchmarker = OmniBarmarker(
        executor_fn=create_agent,
        executor_kwargs={},
        initial_input=benchmarks,
        auto_assign_evaluators=True  # Enable automatic evaluator assignment
    )
    
    # Run benchmarks
    results = benchmarker.benchmark()
    
    print(f"Results: {len(benchmarker.logger)} logs created")
    
    # Show evaluation results
    for i, log in enumerate(benchmarker.logger.get_all_logs(), 1):
        if log.evaluator:
            eval_results = log.eval()
            print(f"  Log {i} evaluation: {eval_results}")
    
    print(f"\n📋 Example 2: Custom Evaluator Mapping")
    print("-" * 40)
    
    # Custom evaluator mapping
    custom_benchmarker = OmniBarmarker(
        executor_fn=create_agent,
        executor_kwargs={},
        initial_input=benchmarks[:1],  # Just one benchmark
        auto_assign_evaluators=True,
        evaluator_type_mapping={
            BoolEvalResult: CustomBooleanEvaluator  # Use custom evaluator
        }
    )
    
    # Run with custom evaluator
    custom_results = custom_benchmarker.benchmark()
    
    # Show custom evaluation results
    custom_log = custom_benchmarker.logger.get_all_logs()[0]
    if custom_log.evaluator:
        custom_eval = custom_log.eval()
        print(f"Custom evaluation: {custom_eval}")
    
    print(f"\n📋 Example 3: Disabled Auto-Assignment")
    print("-" * 38)
    
    # Disabled auto-assignment
    manual_benchmarker = OmniBarmarker(
        executor_fn=create_agent,
        executor_kwargs={},
        initial_input=benchmarks[:1],
        auto_assign_evaluators=False  # Disabled
    )
    
    # Run without auto-evaluators
    manual_results = manual_benchmarker.benchmark()
    
    manual_log = manual_benchmarker.logger.get_all_logs()[0]
    print(f"Evaluator assigned: {manual_log.evaluator is not None}")
    print(f"Evaluation result: {manual_log.eval()}")
    
    print(f"\n🎨 Pretty Print with Evaluations:")
    print("-" * 32)
    benchmarker.print_logger_details(detail_level="summary")
    
    print(f"\n✅ Auto-evaluator assignment examples completed!")
    print(f"   • Default mapping: BoolEvalResult → BooleanEvaluator")
    print(f"   • Custom mapping: BoolEvalResult → CustomBooleanEvaluator") 
    print(f"   • Disabled: No automatic evaluator assignment")


if __name__ == "__main__":
    main()
