#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Test script to verify the auto-evaluator assignment functionality in OmniBarmarker.
"""

from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.output import StringEqualityObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult
from omnibar.logging.evaluator import BaseEvaluator, BooleanEvaluator, FloatEvaluator
from omnibar.logging import LogEntry
from typing import Dict, Any, List


class MockAgent:
    def invoke(self, **kwargs) -> Dict[str, Any]:
        query = kwargs.get("query", "default")
        if "success" in query:
            return {"status": "success", "score": 0.85}
        elif "fail" in query:
            return {"status": "failed", "score": 0.45}
        else:
            return {"status": "unknown", "score": 0.60}


def create_mock_agent():
    return MockAgent()


class CustomFloatEvaluator(BaseEvaluator):
    """Custom evaluator for testing user-defined evaluators."""
    
    def _eval(self, log_entries: List["LogEntry"]) -> Dict[str, Any]:
        values = []
        for entry in log_entries:
            if hasattr(entry.eval_result, 'result') and isinstance(entry.eval_result.result, (int, float)):
                values.append(entry.eval_result.result)
        
        return {
            "custom_mean": sum(values) / len(values) if values else 0.0,
            "custom_max": max(values) if values else 0.0,
            "custom_min": min(values) if values else 0.0,
            "custom_count": len(values)
        }


class FloatObjective(StringEqualityObjective):
    """Mock objective that returns float results for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_eval_result_type = FloatEvalResult
    
    def _eval_fn(self, formatted_output: Dict[str, Any], **kwargs) -> FloatEvalResult:
        # Extract score and return as float result
        score = formatted_output.get(self.output_key, 0.0)
        if isinstance(score, (int, float)):
            return FloatEvalResult(result=float(score), message=f"Score: {score}")
        else:
            return FloatEvalResult(result=0.0, message="Invalid score format")


def test_default_auto_evaluator_assignment():
    """Test default auto-evaluator assignment behavior."""
    
    print("🧪 Testing Default Auto-Evaluator Assignment")
    print("=" * 50)
    
    # Create objectives with different result types
    bool_objective = StringEqualityObjective(
        name="BoolTest",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    float_objective = FloatObjective(
        name="FloatTest",
        goal="score",
        output_key="score"
    )
    
    benchmarks = [
        Benchmark(
            name="BoolBenchmark",
            input_kwargs={"query": "success_test"},
            objective=bool_objective,
            iterations=2,
            verbose=False
        ),
        Benchmark(
            name="FloatBenchmark", 
            input_kwargs={"query": "success_test"},
            objective=float_objective,
            iterations=2,
            verbose=False
        )
    ]
    
    # Test with default configuration (auto_assign_evaluators=True)
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True  # Default behavior
    )
    
    print(f"📋 Configuration:")
    print(f"   Auto-assign evaluators: {benchmarker.auto_assign_evaluators}")
    print(f"   Evaluator mapping: {benchmarker.evaluator_type_mapping}")
    
    # Run benchmarks
    results = benchmarker.benchmark()
    
    # Check that evaluators were auto-assigned
    all_logs = benchmarker.logger.get_all_logs()
    
    print(f"\n📊 Results:")
    print(f"   Total logs created: {len(all_logs)}")
    
    for i, log in enumerate(all_logs, 1):
        obj_name = log.metadata.get('objective_name', 'Unknown')
        evaluator_assigned = log.metadata.get('auto_evaluator_assigned', False)
        evaluator_type = type(log.evaluator).__name__ if log.evaluator else "None"
        
        print(f"   Log {i}: {obj_name}")
        print(f"      Evaluator assigned: {evaluator_assigned}")
        print(f"      Evaluator type: {evaluator_type}")
        
        # Test evaluation
        if log.evaluator:
            try:
                eval_results = log.eval()
                print(f"      Evaluation results: {eval_results}")
            except Exception as e:
                print(f"      Evaluation error: {e}")
        print()
    
    # Verify correct evaluator types were assigned
    bool_logs = [log for log in all_logs if log.metadata.get('objective_name') == 'BoolTest']
    float_logs = [log for log in all_logs if log.metadata.get('objective_name') == 'FloatTest']
    
    assert len(bool_logs) == 1, f"Expected 1 bool log, got {len(bool_logs)}"
    assert len(float_logs) == 1, f"Expected 1 float log, got {len(float_logs)}"
    
    bool_log = bool_logs[0]
    float_log = float_logs[0]
    
    assert isinstance(bool_log.evaluator, BooleanEvaluator), f"Expected BooleanEvaluator, got {type(bool_log.evaluator)}"
    assert isinstance(float_log.evaluator, FloatEvaluator), f"Expected FloatEvaluator, got {type(float_log.evaluator)}"
    
    print("✅ Default auto-evaluator assignment working correctly!")
    return benchmarker


def test_custom_evaluator_mapping():
    """Test custom evaluator mapping configuration."""
    
    print("\n🧪 Testing Custom Evaluator Mapping")
    print("=" * 40)
    
    # Create float objective
    float_objective = FloatObjective(
        name="CustomFloatTest",
        goal="score",
        output_key="score"
    )
    
    benchmark = Benchmark(
        name="CustomBenchmark",
        input_kwargs={"query": "success_test"},
        objective=float_objective,
        iterations=3,
        verbose=False
    )
    
    # Test with custom evaluator mapping
    custom_mapping = {
        BoolEvalResult: BooleanEvaluator,
        FloatEvalResult: CustomFloatEvaluator  # Custom evaluator!
    }
    
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=[benchmark],
        enable_logging=True,
        auto_assign_evaluators=True,
        evaluator_type_mapping=custom_mapping
    )
    
    print(f"📋 Custom Configuration:")
    print(f"   Custom mapping for FloatEvalResult: {custom_mapping[FloatEvalResult].__name__}")
    
    # Run benchmark
    results = benchmarker.benchmark()
    
    # Check that custom evaluator was assigned
    all_logs = benchmarker.logger.get_all_logs()
    log = all_logs[0]
    
    print(f"\n📊 Results:")
    print(f"   Evaluator type: {type(log.evaluator).__name__}")
    
    assert isinstance(log.evaluator, CustomFloatEvaluator), f"Expected CustomFloatEvaluator, got {type(log.evaluator)}"
    
    # Test custom evaluation
    eval_results = log.eval()
    print(f"   Custom evaluation results: {eval_results}")
    
    # Verify custom evaluator produced expected keys
    expected_keys = ["custom_mean", "custom_max", "custom_min", "custom_count"]
    for key in expected_keys:
        assert key in eval_results, f"Expected key '{key}' in evaluation results"
    
    print("✅ Custom evaluator mapping working correctly!")
    return benchmarker


def test_disabled_auto_assignment():
    """Test disabled auto-evaluator assignment."""
    
    print("\n🧪 Testing Disabled Auto-Assignment")
    print("=" * 35)
    
    bool_objective = StringEqualityObjective(
        name="DisabledTest",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    benchmark = Benchmark(
        name="DisabledBenchmark",
        input_kwargs={"query": "success_test"},
        objective=bool_objective,
        iterations=2,
        verbose=False
    )
    
    # Disable auto-assignment
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=[benchmark],
        enable_logging=True,
        auto_assign_evaluators=False  # Disabled!
    )
    
    print(f"📋 Configuration:")
    print(f"   Auto-assign evaluators: {benchmarker.auto_assign_evaluators}")
    
    # Run benchmark
    results = benchmarker.benchmark()
    
    # Check that no evaluator was assigned
    all_logs = benchmarker.logger.get_all_logs()
    log = all_logs[0]
    
    print(f"\n📊 Results:")
    print(f"   Evaluator assigned: {log.evaluator is not None}")
    print(f"   Auto-assignment flag in metadata: {log.metadata.get('auto_evaluator_assigned', False)}")
    
    assert log.evaluator is None, f"Expected no evaluator, but got {type(log.evaluator)}"
    assert log.metadata.get('auto_evaluator_assigned') == False, "Expected auto_evaluator_assigned to be False"
    
    # Test evaluation (should return error)
    eval_results = log.eval()
    print(f"   Evaluation results: {eval_results}")
    
    assert "error" in eval_results, "Expected error in evaluation results when no evaluator"
    
    print("✅ Disabled auto-assignment working correctly!")
    return benchmarker


def test_combined_objectives_evaluators():
    """Test auto-evaluator assignment with combined objectives."""
    
    print("\n🧪 Testing Combined Objectives with Auto-Evaluators")
    print("=" * 50)
    
    # Create combined objective with different result types
    bool_objective = StringEqualityObjective(
        name="CombinedBool",
        goal="success",
        output_key="status",
        valid_eval_result_type=BoolEvalResult
    )
    
    float_objective = FloatObjective(
        name="CombinedFloat",
        goal="score",
        output_key="score"
    )
    
    combined_objective = CombinedBenchmarkObjective(
        name="CombinedTest",
        objectives=[bool_objective, float_objective]
    )
    
    benchmark = Benchmark(
        name="CombinedBenchmark",
        input_kwargs={"query": "success_test"},
        objective=combined_objective,
        iterations=2,
        verbose=False
    )
    
    benchmarker = OmniBarmarker(
        executor_fn=create_mock_agent,
        executor_kwargs={},
        initial_input=[benchmark],
        enable_logging=True,
        auto_assign_evaluators=True
    )
    
    print(f"📋 Combined Objective:")
    print(f"   Sub-objectives: {len(combined_objective.objectives)}")
    for i, obj in enumerate(combined_objective.objectives, 1):
        print(f"      {i}. {obj.name} ({obj.valid_eval_result_type.__name__})")
    
    # Run benchmark
    results = benchmarker.benchmark()
    
    # Check that each sub-objective got appropriate evaluator
    all_logs = benchmarker.logger.get_all_logs()
    
    print(f"\n📊 Results:")
    print(f"   Total logs created: {len(all_logs)} (should be 2 for combined objective)")
    
    bool_logs = [log for log in all_logs if log.metadata.get('objective_name') == 'CombinedBool']
    float_logs = [log for log in all_logs if log.metadata.get('objective_name') == 'CombinedFloat']
    
    assert len(bool_logs) == 1, f"Expected 1 bool log, got {len(bool_logs)}"
    assert len(float_logs) == 1, f"Expected 1 float log, got {len(float_logs)}"
    
    bool_log = bool_logs[0]
    float_log = float_logs[0]
    
    print(f"   Bool objective log:")
    print(f"      Evaluator: {type(bool_log.evaluator).__name__}")
    print(f"      Entries: {len(bool_log.entries)}")
    
    print(f"   Float objective log:")
    print(f"      Evaluator: {type(float_log.evaluator).__name__}")
    print(f"      Entries: {len(float_log.entries)}")
    
    # Verify correct evaluator types
    assert isinstance(bool_log.evaluator, BooleanEvaluator), f"Expected BooleanEvaluator, got {type(bool_log.evaluator)}"
    assert isinstance(float_log.evaluator, FloatEvaluator), f"Expected FloatEvaluator, got {type(float_log.evaluator)}"
    
    # Test evaluations
    bool_eval = bool_log.eval()
    float_eval = float_log.eval()
    
    print(f"   Bool evaluation: {bool_eval}")
    print(f"   Float evaluation: {float_eval}")
    
    print("✅ Combined objectives auto-evaluator assignment working correctly!")
    return benchmarker


def main():
    """Run all tests."""
    
    print("🚀 Auto-Evaluator Assignment Test Suite")
    print("=" * 60)
    
    try:
        # Test default behavior
        test_default_auto_evaluator_assignment()
        
        # Test custom mapping
        test_custom_evaluator_mapping()
        
        # Test disabled assignment
        test_disabled_auto_assignment()
        
        # Test combined objectives
        test_combined_objectives_evaluators()
        
        print(f"\n🎉 All Tests Passed!")
        print(f"✅ Auto-evaluator assignment working reliably")
        print(f"✅ Custom evaluator mapping supported")
        print(f"✅ Can disable auto-assignment")
        print(f"✅ Combined objectives handled correctly")
        print(f"✅ Modular and configurable system implemented")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
