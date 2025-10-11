#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Visual Test for _print_single_log_clean Method

This script demonstrates the visual output of the _print_single_log_clean method
with various scenarios including different detail levels, colors, and data.

Usage:
    python utils/logger/visual_test_clean_print.py
    
Or from the logger directory:
    cd utils/logger && python visual_test_clean_print.py
"""

import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from omnibar.logging.logger import BenchmarkLogger, BenchmarkLog, LogEntry, Colors
from omnibar.logging.evaluator import BaseEvaluator
from omnibar.core.types import (
    FloatEvalResult, BoolEvalResult, InvalidEvalResult,
    AgentOperationError, ExtractionError, FormattingError,
    EvaluationError, EvalTypeMismatchError, OutputKeyNotFoundError,
    InvalidRegexPatternError
)

class MockEvaluator(BaseEvaluator):
    """Mock evaluator for demonstration purposes."""
    
    def _eval(self, log_entries):
        """Implement the required _eval method."""
        return {
            "average_score": 0.85,
            "total_entries": len(log_entries),
            "success_rate": 0.92,
            "evaluation_time": "2024-01-15 10:30:00"
        }

def create_sample_log_entry(objective_id: uuid.UUID, result_value: Any, result_type: str = "auto", metadata: Dict[str, Any] = None) -> LogEntry:
    """Create a sample log entry with specified result type for testing."""
    
    # Auto-detect type if not specified
    if result_type == "auto":
        if isinstance(result_value, float):
            result_type = "float"
        elif isinstance(result_value, bool):
            result_type = "bool"
        else:
            result_type = "invalid"
    
    # Create appropriate EvalResult type
    if result_type == "float":
        eval_result = FloatEvalResult(float(result_value))
    elif result_type == "bool":
        eval_result = BoolEvalResult(bool(result_value))
    elif result_type == "invalid":
        eval_result = InvalidEvalResult(None, "Sample invalid result")
    elif result_type == "agent_error":
        eval_result = AgentOperationError(None, "Sample agent operation error")
    elif result_type == "extraction_error":
        eval_result = ExtractionError(None, "Sample data extraction error")
    elif result_type == "formatting_error":
        eval_result = FormattingError(None, "Sample formatting error")
    elif result_type == "evaluation_error":
        eval_result = EvaluationError(None, "Sample evaluation error")
    elif result_type == "type_mismatch_error":
        eval_result = EvalTypeMismatchError(None, "Sample type mismatch error")
    elif result_type == "key_not_found_error":
        eval_result = OutputKeyNotFoundError(None, "Sample key not found error")
    elif result_type == "regex_error":
        eval_result = InvalidRegexPatternError(None, "Sample regex pattern error")
    else:
        eval_result = InvalidEvalResult(None, f"Unknown result type: {result_type}")
    
    return LogEntry(
        objective_id=objective_id,
        eval_result=eval_result,
        evaluated_output={
            "model_response": f"This is a sample model response with result: {result_value}",
            "processing_time": round(0.1 + (hash(str(result_value)) % 100) / 1000, 3),
            "tokens_used": 150 + (hash(str(result_value)) % 50),
            "result_type": result_type
        },
        timestamp=datetime.now() - timedelta(minutes=hash(str(result_value)) % 60),
        metadata=metadata or {"batch_id": f"batch_{hash(str(result_value)) % 10}", "version": "1.0", "result_type": result_type}
    )

def create_sample_benchmark_log(entries_count: int = 3, with_evaluator: bool = True) -> BenchmarkLog:
    """Create a sample benchmark log for testing."""
    benchmark_id = uuid.uuid4()
    objective_id = uuid.uuid4()
    
    # Create log with timing
    log = BenchmarkLog(
        benchmark_id=benchmark_id,
        objective_id=objective_id,
        time_started=datetime.now() - timedelta(minutes=30),
        time_ended=datetime.now() - timedelta(minutes=5),
        entries=[],
        metadata={
            "experiment_name": "Text Classification Benchmark",
            "model": "gpt-4o-mini",
            "dataset": "emotion_classification_v2",
            "batch_size": 32
        },
        evaluator=MockEvaluator() if with_evaluator else None
    )
    
    # Add sample entries
    for i in range(entries_count):
        entry = create_sample_log_entry(
            objective_id, 
            0.7 + (i * 0.1), 
            {"entry_index": i, "difficulty": "medium" if i % 2 == 0 else "hard"}
        )
        log.entries.append(entry)
    
    return log

def test_single_log_clean_basic():
    """Basic test of _print_single_log_clean method."""
    print("=" * 80)
    print("BASIC TEST: _print_single_log_clean Method")
    print("=" * 80)
    print()
    
    logger = BenchmarkLogger()
    log = create_sample_benchmark_log(3, False)
    
    print("Testing with detailed level:")
    logger._print_single_log_clean(
        log=log,
        index=1,
        detail_level="detailed",
        include_evaluations=False,
        max_entries=3
    )

def test_all_detail_levels():
    """Test all detail levels with the same data."""
    print("\n" + "=" * 80)
    print("DETAIL LEVELS COMPARISON")
    print("=" * 80)
    
    logger = BenchmarkLogger()
    log = create_sample_benchmark_log(5, False)
    
    detail_levels = ["summary", "detailed", "full"]
    for i, detail_level in enumerate(detail_levels, 1):
        print(f"\n{'-' * 50}")
        print(f"Detail Level: {detail_level.upper()}")
        print(f"{'-' * 50}")
        
        logger._print_single_log_clean(
            log=log,
            index=i,
            detail_level=detail_level,
            include_evaluations=False,
            max_entries=3
        )

def test_color_variations():
    """Test with and without colors."""
    print("\n" + "=" * 80)
    print("COLOR VARIATIONS TEST")
    print("=" * 80)
    
    logger = BenchmarkLogger()
    log = create_sample_benchmark_log(2, False)
    
    print("\n--- WITH COLORS ---")
    Colors.enable_colors()
    logger._print_single_log_clean(log, 1, "detailed", False, 2)
    
    print("\n--- WITHOUT COLORS ---")
    Colors.disable_colors()
    logger._print_single_log_clean(log, 1, "detailed", False, 2)
    
    # Reset colors
    Colors.enable_colors()

def test_comprehensive_scenarios():
    """Comprehensive test with various scenarios."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SCENARIOS TEST")
    print("=" * 80)
    print()
    
    logger = BenchmarkLogger()
    
    scenarios = [
        {
            "name": "Scenario 1: Basic Log with Colors",
            "entries_count": 3,
            "detail_level": "detailed",
            "include_evaluations": False,
            "max_entries": 5,
            "use_colors": True,
        },
        {
            "name": "Scenario 2: Summary Level (No Entries Shown)",
            "entries_count": 5,
            "detail_level": "summary",
            "include_evaluations": False,
            "max_entries": 3,
            "use_colors": True,
        },
        {
            "name": "Scenario 3: Full Detail Level with Many Entries",
            "entries_count": 7,
            "detail_level": "full",
            "include_evaluations": False,
            "max_entries": 3,
            "use_colors": True,
        },
        {
            "name": "Scenario 4: No Colors (Production Mode)",
            "entries_count": 4,
            "detail_level": "detailed",
            "include_evaluations": False,
            "max_entries": 4,
            "use_colors": False,
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'-' * 80}")
        print(f"{scenario['name']}")
        print(f"{'-' * 80}")
        print(f"Config: entries={scenario['entries_count']}, detail={scenario['detail_level']}, "
              f"evals={scenario['include_evaluations']}, max={scenario['max_entries']}, "
              f"colors={scenario['use_colors']}")
        print()
        
        # Set color mode
        if scenario['use_colors']:
            Colors.enable_colors()
        else:
            Colors.disable_colors()
        
        # Create sample log
        log = create_sample_benchmark_log(scenario['entries_count'], False)
        
        # Call the _print_single_log_clean method directly
        try:
            logger._print_single_log_clean(
                log=log,
                index=i,
                detail_level=scenario['detail_level'],
                include_evaluations=scenario['include_evaluations'],
                max_entries=scenario['max_entries']
            )
        except Exception as e:
            print(f"❌ Error in scenario {i}: {e}")
            import traceback
            traceback.print_exc()
    
    # Reset colors
    Colors.enable_colors()

def test_color_palette():
    """Test the color palette."""
    print("\n" + "=" * 80)
    print("COLOR PALETTE TEST")
    print("=" * 80)
    
    print("\nTesting individual color functions:")
    print(f"Primary: {Colors.primary('Sample primary text', bold=True)}")
    print(f"Success: {Colors.success('Sample success text', bold=True)}")
    print(f"Warning: {Colors.warning('Sample warning text', bold=True)}")
    print(f"Error: {Colors.error('Sample error text', bold=True)}")
    print(f"Info: {Colors.info('Sample info text', bold=True)}")
    print(f"Muted: {Colors.muted('Sample muted text', dim=True)}")
    print(f"Accent: {Colors.accent('Sample accent text', bold=True)}")

def test_all_eval_result_types():
    """Test all EvalResult types to see color coding."""
    print("\n" + "=" * 80)
    print("ALL EVAL RESULT TYPES WITH COLOR CODING")
    print("=" * 80)
    print("Testing valid (green) and invalid (red) result types")
    print()
    
    logger = BenchmarkLogger()
    
    # Create a log with all different result types
    log = BenchmarkLog(
        benchmark_id=uuid.uuid4(),
        objective_id=uuid.uuid4(),
        time_started=datetime.now() - timedelta(minutes=10),
        time_ended=datetime.now(),
        entries=[],
        metadata={"test": "all_eval_result_types", "purpose": "color_demonstration"},
        evaluator=None
    )
    
    # Valid result types (should be GREEN)
    valid_types = [
        ("float", 0.95),
        ("bool", True),
    ]
    
    # Invalid result types (should be RED)
    invalid_types = [
        "invalid",
        "agent_error", 
        "extraction_error",
        "formatting_error",
        "evaluation_error", 
        "type_mismatch_error",
        "key_not_found_error",
        "regex_error"
    ]
    
    print("Creating entries with all result types...")
    
    # Add valid entries
    for i, (result_type, value) in enumerate(valid_types):
        entry = create_sample_log_entry(
            log.objective_id, 
            value,
            result_type,
            {"entry_index": i, "category": "valid"}
        )
        log.entries.append(entry)
    
    # Add invalid entries
    for i, result_type in enumerate(invalid_types):
        entry = create_sample_log_entry(
            log.objective_id,
            None,
            result_type,
            {"entry_index": i + len(valid_types), "category": "invalid"}
        )
        log.entries.append(entry)
    
    print(f"Created {len(log.entries)} entries total")
    print(f"Valid types (GREEN): {len(valid_types)}")
    print(f"Invalid types (RED): {len(invalid_types)}")
    print()
    
    # Display the log with full details
    logger._print_single_log_clean(
        log=log,
        index=1,
        detail_level="full",
        include_evaluations=False,
        max_entries=len(log.entries)  # Show all entries
    )

def interactive_mode():
    """Interactive mode for custom testing."""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("You can modify this section to test specific scenarios")
    
    logger = BenchmarkLogger()
    
    # Example: Create your own custom log for testing
    custom_log = create_sample_benchmark_log(
        entries_count=4,      # Change this
        with_evaluator=False  # Change this
    )
    
    print("\nCustom test log:")
    logger._print_single_log_clean(
        log=custom_log,
        index=1,
        detail_level="full",    # Change this: "summary", "detailed", "full"
        include_evaluations=False,  # Change this
        max_entries=5          # Change this
    )

if __name__ == "__main__":
    print("Visual Test Suite for _print_single_log_clean Method")
    print("====================================================")
    
    try:
        # Run all tests
        test_single_log_clean_basic()
        test_all_detail_levels()
        test_color_variations()
        test_color_palette()
        test_comprehensive_scenarios()
        test_all_eval_result_types()
        interactive_mode()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nThe _print_single_log_clean method provides clean, professional")
        print("formatting with modern colors and proper information hierarchy.")
        print("It supports multiple detail levels and graceful color handling.")
        print("\nYou can modify the interactive_mode() function above to test")
        print("specific scenarios or add your own test cases.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
