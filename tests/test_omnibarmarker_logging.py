#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Test script demonstrating the OmniBarmarker with integrated logging,
specifically showing how combined objectives are handled with separate logs
for each sub-objective.
"""

import uuid
from typing import Dict, Any
from datetime import datetime

# Import the updated OmniBarmarker and related classes
from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.output import StringEqualityObjective
from omnibar.objectives.output import RegexMatchObjective
from omnibar.core.types import BoolEvalResult


class MockAgent:
    """Simple mock agent for testing purposes."""
    
    def __init__(self, name: str = "MockAgent"):
        self.name = name
    
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """Mock invoke method that returns predictable results."""
        query = kwargs.get("query", "default")
        
        # Simulate different responses based on input
        if "success" in query.lower():
            return {
                "status": "success",
                "message": "Operation completed successfully",
                "result": True
            }
        elif "test" in query.lower():
            return {
                "status": "test",
                "message": "This is a test response",
                "result": True
            }
        else:
            return {
                "status": "unknown",
                "message": "Default response",
                "result": False
            }
    
    async def ainvoke(self, **kwargs) -> Dict[str, Any]:
        """Async version of invoke."""
        return self.invoke(**kwargs)


def create_mock_agent() -> MockAgent:
    """Factory function to create mock agents."""
    return MockAgent()


def test_combined_objective_logging():
    """
    Test the OmniBarmarker with combined objectives to demonstrate
    that each sub-objective gets its own separate log entry.
    """
    print("🧪 Testing OmniBarmarker with Combined Objective Logging")
    print("=" * 60)
    
    # Create individual objectives that will be combined
    string_objective = StringEqualityObjective(
        name="StatusCheck",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    regex_objective = RegexMatchObjective(
        name="MessageCheck", 
        goal="test|success",  # Regex pattern matching "test" or "success"
        output_key="message",
        valid_eval_result_type=BoolEvalResult
    )
    
    # Create combined objective
    combined_objective = CombinedBenchmarkObjective(
        name="ComprehensiveCheck",
        description="Check both status and message content",
        objectives=[string_objective, regex_objective]
    )
    
    print(f"📋 Created combined objective with {len(combined_objective.objectives)} sub-objectives:")
    for i, obj in enumerate(combined_objective.objectives, 1):
        print(f"   {i}. {obj.name} (UUID: {str(obj.uuid)[:8]}...)")
    print()
    
    # Create benchmarks using the combined objective
    benchmarks = [
        Benchmark(
            name="SuccessTest",
            input_kwargs={"query": "success_test"},
            objective=combined_objective,
            iterations=2,
            verbose=True,
            active=True
        ),
        Benchmark(
            name="TestCase",
            input_kwargs={"query": "test_case"},
            objective=combined_objective,
            iterations=2,
            verbose=True,
            active=True
        )
    ]
    
    print(f"📊 Created {len(benchmarks)} benchmarks, each with {benchmarks[0].iterations} iterations")
    print()
    
    # Create OmniBarmarker with logging enabled
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=benchmarks,
        enable_logging=True,  # Enable comprehensive logging
        notebook=False
    )
    
    print("🚀 Running benchmarks...")
    print("-" * 40)
    
    # Run the benchmarks
    results = benchmarker.benchmark()
    
    print("-" * 40)
    print("✅ Benchmarks completed!")
    print()
    
    # Display logging results
    print("📊 LOGGING ANALYSIS")
    print("=" * 40)
    
    # Show summary statistics
    print("📈 Logger Summary:")
    benchmarker.print_logger_summary()
    print()
    
    # Show detailed logs
    print("📋 Detailed Logs:")
    benchmarker.print_logger_details(detail_level="detailed")
    print()
    
    # Demonstrate specific log retrieval
    print("🔍 SPECIFIC LOG ANALYSIS")
    print("=" * 40)
    
    # Get logs for each benchmark
    for benchmark in benchmarks:
        print(f"\n📋 Logs for Benchmark: {benchmark.name} (UUID: {str(benchmark.uuid)[:8]}...)")
        try:
            benchmark_logs = benchmarker.get_logs_for_benchmark(benchmark.uuid)
            print(f"   Found {len(benchmark_logs)} logs for this benchmark:")
            
            for objective_id, log in benchmark_logs.items():
                print(f"   • Objective {str(objective_id)[:8]}...: {len(log.entries)} entries")
                
                # Find the objective name
                obj_name = "Unknown"
                for obj in combined_objective.objectives:
                    if obj.uuid == objective_id:
                        obj_name = obj.name
                        break
                
                print(f"     - Objective Name: {obj_name}")
                print(f"     - Duration: {log.time_ended - log.time_started if log.time_ended else 'Still running'}")
                print(f"     - Metadata: {log.metadata}")
                
        except KeyError as e:
            print(f"   ❌ No logs found: {e}")
    
    # Get logs for each sub-objective across all benchmarks
    print(f"\n🎯 Logs by Sub-Objective:")
    for sub_objective in combined_objective.objectives:
        print(f"\n   📊 Sub-objective: {sub_objective.name} (UUID: {str(sub_objective.uuid)[:8]}...)")
        try:
            objective_logs = benchmarker.get_logs_for_objective(sub_objective.uuid)
            print(f"      Found in {len(objective_logs)} benchmarks:")
            
            for benchmark_id, log in objective_logs.items():
                benchmark_name = "Unknown"
                for b in benchmarks:
                    if b.uuid == benchmark_id:
                        benchmark_name = b.name
                        break
                
                print(f"      • Benchmark {benchmark_name}: {len(log.entries)} entries")
                
                # Show evaluation results summary
                valid_count = sum(1 for entry in log.entries 
                                if hasattr(entry.eval_result, 'result') and entry.eval_result.result)
                print(f"        - Valid results: {valid_count}/{len(log.entries)}")
                
        except KeyError as e:
            print(f"      ❌ No logs found: {e}")
    
    # Final statistics
    print(f"\n📈 FINAL STATISTICS")
    print("=" * 40)
    print(f"Total Iterations: {benchmarker.total_iter}")
    print(f"Successful: {benchmarker.success_iter}")
    print(f"Failed: {benchmarker.fail_iter}")
    print(f"Success Rate: {benchmarker.success_rate:.1f}%")
    print()
    print(f"Total Logs: {len(benchmarker.logger)}")
    print(f"Unique Benchmarks: {len(benchmarker.logger.get_all_benchmark_ids())}")
    print(f"Unique Objectives: {len(benchmarker.logger.get_all_objective_ids())}")
    
    return benchmarker


def test_single_objective_logging():
    """Test logging with single objectives for comparison."""
    print("\n🧪 Testing Single Objective Logging (for comparison)")
    print("=" * 60)
    
    # Create a simple single objective benchmark
    single_objective = StringEqualityObjective(
        name="SimpleStatusCheck",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    benchmark = Benchmark(
        name="SingleObjectiveTest",
        input_kwargs={"query": "success_test"},
        objective=single_objective,
        iterations=2,
        verbose=True,
        active=True
    )
    
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=[benchmark],
        enable_logging=True,
        notebook=False
    )
    
    # Run the benchmark
    results = benchmarker.benchmark()
    
    print("📊 Single Objective Results:")
    benchmarker.print_logger_summary()
    
    return benchmarker


if __name__ == "__main__":
    print("🚀 OmniBarmarker Logging Integration Test")
    print("=" * 60)
    print()
    
    # Test combined objectives
    combined_benchmarker = test_combined_objective_logging()
    
    print("\n" + "="*80 + "\n")
    
    # Test single objectives for comparison
    single_benchmarker = test_single_objective_logging()
    
    print(f"\n✅ All tests completed successfully!")
    print(f"   Combined Objective Benchmarker: {len(combined_benchmarker.logger)} logs")
    print(f"   Single Objective Benchmarker: {len(single_benchmarker.logger)} logs")
