#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Quick test to verify that all import paths work correctly with the new package structure.
"""

def test_core_imports():
    """Test core module imports."""
    print("🧪 Testing core imports...")
    try:
        from omnibar.core.benchmarker import OmniBarmarker, Benchmark
        from omnibar.core.types import EvalResult, ValidEvalResult, BoolEvalResult
        print("✅ Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        return False

def test_objectives_imports():
    """Test objectives module imports."""
    print("🧪 Testing objectives imports...")
    try:
        from omnibar.objectives.base import BaseBenchmarkObjective
        from omnibar.objectives.combined import CombinedBenchmarkObjective
        from omnibar.objectives.llm_judge import LLMJudgeObjective
        from omnibar.objectives.output import StringEqualityObjective
        from omnibar.objectives.path import PathEqualityObjective
        from omnibar.objectives.state import StateEqualityObjective
        print("✅ Objectives imports successful")
        return True
    except ImportError as e:
        print(f"❌ Objectives import failed: {e}")
        return False

def test_logging_imports():
    """Test logging module imports."""
    print("🧪 Testing logging imports...")
    try:
        from omnibar.logging.logger import BenchmarkLogger, BenchmarkLog, LogEntry
        from omnibar.logging.evaluator import BaseEvaluator, BooleanEvaluator
        print("✅ Logging imports successful")
        return True
    except ImportError as e:
        print(f"❌ Logging import failed: {e}")
        return False

def test_top_level_imports():
    """Test top-level package imports."""
    print("🧪 Testing top-level imports...")
    try:
        from omnibar import OmniBarmarker, Benchmark
        from omnibar import BenchmarkLogger, EvalResult
        from omnibar.objectives import BaseBenchmarkObjective
        print("✅ Top-level imports successful")
        return True
    except ImportError as e:
        print(f"❌ Top-level import failed: {e}")
        return False

def test_version_import():
    """Test version import."""
    print("🧪 Testing version import...")
    try:
        from omnibar.version import __version__
        print(f"✅ Version import successful: {__version__}")
        return True
    except ImportError as e:
        print(f"❌ Version import failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("🚀 Running import tests for OmniBAR package structure...")
    print("=" * 60)
    
    tests = [
        test_version_import,
        test_core_imports,
        test_objectives_imports,
        test_logging_imports,
        test_top_level_imports,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    print("📊 Test Results Summary:")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All import tests passed! Package structure is working correctly.")
        return True
    else:
        print("❌ Some import tests failed. Please check the package structure.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
