#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Simple example showing how to use OmniBarmarker with integrated logging,
particularly demonstrating combined objective handling.
"""

from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.output import StringEqualityObjective
from omnibar.objectives.output import RegexMatchObjective
from omnibar.core.types import BoolEvalResult
from typing import Dict, Any


def create_simple_agent():
    """Create a simple agent that returns predictable responses."""
    class SimpleAgent:
        def invoke(self, **kwargs):
            query = kwargs.get("query", "")
            return {
                "status": "success" if "success" in query else "failed",
                "message": f"Processed: {query}",
                "data": {"processed": True}
            }
        
        async def ainvoke(self, **kwargs):
            return self.invoke(**kwargs)
    
    return SimpleAgent()


def main():
    """Main example function."""
    print("🚀 OmniBarmarker with Logging - Simple Example")
    print("=" * 50)
    
    # 1. Create individual objectives
    status_check = StringEqualityObjective(
        name="StatusValidation",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    message_check = RegexMatchObjective(
        name="MessageValidation",
        goal="Processed:.*",  # Regex to match "Processed: ..."
        output_key="message", 
        valid_eval_result_type=BoolEvalResult
    )
    
    # 2. Create combined objective
    combined_objective = CombinedBenchmarkObjective(
        name="ComprehensiveValidation",
        description="Validates both status and message format",
        objectives=[status_check, message_check]
    )
    
    print(f"📋 Created combined objective with sub-objectives:")
    for i, obj in enumerate(combined_objective.objectives, 1):
        print(f"   {i}. {obj.name} - checks '{obj.goal}' in '{obj.output_key}'")
    
    # 3. Create benchmarks
    benchmarks = [
        Benchmark(
            name="SuccessCase",
            input_kwargs={"query": "success_test_1"},
            objective=combined_objective,
            iterations=3,
            verbose=True
        ),
        Benchmark(
            name="MixedCase", 
            input_kwargs={"query": "mixed_test_2"},
            objective=combined_objective,
            iterations=2,
            verbose=True
        )
    ]
    
    # 4. Create benchmarker with logging enabled
    benchmarker = OmniBarmarker(
        executor_fn=create_simple_agent,
        executor_kwargs={},
        initial_input=benchmarks,
        enable_logging=True,  # 🔑 Key: Enable logging
        notebook=False
    )
    
    print(f"\n📊 Running {len(benchmarks)} benchmarks...")
    
    # 5. Run benchmarks
    results = benchmarker.benchmark()
    
    print(f"\n✅ Completed! Results: {results}")
    
    # 6. Access logging results
    print(f"\n📊 LOGGING RESULTS")
    print("-" * 30)
    
    # Quick summary
    print("📈 Summary:")
    benchmarker.print_logger_summary()
    
    print(f"\n🔍 Key Insights:")
    print(f"   • Total logs created: {len(benchmarker.logger)}")
    print(f"   • Unique benchmarks: {len(benchmarker.logger.get_all_benchmark_ids())}")
    print(f"   • Unique objectives: {len(benchmarker.logger.get_all_objective_ids())}")
    
    # Show that each sub-objective has its own log
    print(f"\n🎯 Sub-objective Logs:")
    for sub_obj in combined_objective.objectives:
        obj_logs = benchmarker.get_logs_for_objective(sub_obj.uuid)
        total_entries = sum(len(log.entries) for log in obj_logs.values())
        print(f"   • {sub_obj.name}: {total_entries} total entries across {len(obj_logs)} benchmarks")
    
    # 7. Access specific logs
    print(f"\n📋 Detailed Log Access:")
    for benchmark in benchmarks:
        print(f"\n   Benchmark: {benchmark.name}")
        benchmark_logs = benchmarker.get_logs_for_benchmark(benchmark.uuid)
        
        for obj_id, log in benchmark_logs.items():
            # Find objective name
            obj_name = next(
                (obj.name for obj in combined_objective.objectives if obj.uuid == obj_id),
                "Unknown"
            )
            print(f"     • {obj_name}: {len(log.entries)} entries")
            
            # Show success rate for this objective in this benchmark
            if log.entries:
                successes = sum(1 for entry in log.entries 
                              if hasattr(entry.eval_result, 'result') and entry.eval_result.result)
                success_rate = (successes / len(log.entries)) * 100
                print(f"       Success rate: {success_rate:.1f}% ({successes}/{len(log.entries)})")
    
    return benchmarker


if __name__ == "__main__":
    benchmarker = main()
    
    print(f"\n🎉 Example completed!")
    print(f"   Final success rate: {benchmarker.success_rate:.1f}%")
    print(f"   Access benchmarker.logger for full logging interface")
