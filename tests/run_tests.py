#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Simple Test Runner for OmniBAR

A lightweight alternative to test_all.py for quick test execution.
Useful for development and CI/CD pipelines.

Usage:
    python run_tests.py                # Run all tests sequentially
    python run_tests.py imports        # Run only import tests
    python run_tests.py core           # Run core functionality tests
    python run_tests.py objectives     # Run objective tests
    python run_tests.py --help         # Show help
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Test organization mapping
TEST_CATEGORIES = {
    'imports': [
        'test_imports.py'
    ],
    'core': [
        'test_omnibarmarker.py'
    ],
    'objectives': [
        'test_output_benchmark_objective.py',
        'test_combined_benchmark_objective.py',
        'test_path_benchmark_objective.py', 
        'test_state_benchmark_objective.py'
    ],
    'integrations': [
        'test_llm_judge_objective_real_langchain.py',
        'test_llm_judge_objective_real_pydantic_ai.py',
        'test_diet_schedule_llm_judge.py'
    ],
    'logging': [
        'test_omnibarmarker_logging.py',
        'test_omnibarmarker_logging_integration.py',
        'test_auto_evaluators.py',
        'test_auto_evaluator.py',
        'test_logger.py'
    ],
    'fast': [  # Fast tests only (no slow integrations)
        'test_imports.py',
        'test_output_benchmark_objective.py',
        'test_path_benchmark_objective.py',
        'test_state_benchmark_objective.py',
        'test_omnibarmarker_logging.py',
        'test_omnibarmarker_logging_integration.py',
        'test_auto_evaluator.py',
        'test_logger.py'
    ],
    'all': []  # Will be populated with all test files
}


class SimpleTestRunner:
    """Lightweight test runner for OmniBAR."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results: List[Tuple[str, bool, float, str]] = []  # (name, passed, duration, details)
        
        # Populate 'all' category with all available test files
        all_tests = set()
        for tests in TEST_CATEGORIES.values():
            all_tests.update(tests)
        
        # Add any test files we might have missed
        for test_file in self.test_dir.glob('test_*.py'):
            if test_file.name != 'test_all.py':  # Exclude the master test runner
                all_tests.add(test_file.name)
        
        TEST_CATEGORIES['all'] = sorted(list(all_tests))
    
    def run_test(self, test_file: str, timeout: int = 300) -> Tuple[bool, float, str]:
        """Run a single test file and return (success, duration, details)."""
        test_path = self.test_dir / test_file
        
        if not test_path.exists():
            return False, 0.0, f"Test file not found: {test_file}"
        
        print(f"🧪 Running {test_file}...")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_file} PASSED ({duration:.1f}s)")
                return True, duration, "Success"
            else:
                print(f"❌ {test_file} FAILED ({duration:.1f}s)")
                
                # Try to extract useful error information
                error_info = "Failed"
                if "ImportError" in result.stderr:
                    error_info = "Import Error"
                elif "AssertionError" in result.stderr:
                    error_info = "Assertion Failed"
                elif "ConnectionError" in result.stderr or "requests.exceptions" in result.stderr:
                    error_info = "Network Error"
                elif "API" in result.stderr and "key" in result.stderr.lower():
                    error_info = "API Key Error"
                elif result.stderr.strip():
                    # Get the first line of stderr for context
                    first_error_line = result.stderr.strip().split('\n')[0]
                    if len(first_error_line) > 50:
                        first_error_line = first_error_line[:50] + "..."
                    error_info = first_error_line
                
                return False, duration, error_info
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"⏰ {test_file} TIMEOUT ({timeout}s)")
            return False, duration, f"Timeout ({timeout}s)"
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {test_file} ERROR ({duration:.1f}s): {e}")
            return False, duration, f"Exception: {type(e).__name__}"
    
    def run_category(self, category: str) -> Dict[str, any]:
        """Run all tests in a category."""
        if category not in TEST_CATEGORIES:
            available = ', '.join(TEST_CATEGORIES.keys())
            print(f"❌ Unknown category '{category}'. Available: {available}")
            return {'success': False, 'results': []}
        
        test_files = TEST_CATEGORIES[category]
        if not test_files:
            print(f"⚠️ No tests found for category '{category}'")
            return {'success': True, 'results': []}
        
        print(f"🚀 Running {category} tests ({len(test_files)} files)...")
        print("=" * 60)
        
        start_time = time.time()
        results = []
        
        for test_file in test_files:
            passed, duration, details = self.run_test(test_file)
            results.append((test_file, passed, duration, details))
            self.results.append((test_file, passed, duration, details))
        
        total_duration = time.time() - start_time
        passed_count = sum(1 for _, passed, _, _ in results if passed)
        total_count = len(results)
        
        print("\n" + "=" * 60)
        print(f"📊 {category.upper()} RESULTS:")
        print(f"✅ Passed: {passed_count}/{total_count}")
        print(f"⏱️ Total Time: {total_duration:.1f}s")
        
        if passed_count < total_count:
            print("\n❌ FAILED TESTS:")
            for test_file, passed, duration, details in results:
                if not passed:
                    print(f"  - {test_file}: {details}")
        
        return {
            'success': passed_count == total_count,
            'results': results,
            'passed': passed_count,
            'total': total_count,
            'duration': total_duration
        }
    
    def print_summary(self):
        """Print a summary of all test results."""
        if not self.results:
            print("❌ No tests were run")
            return
        
        passed = sum(1 for _, p, _, _ in self.results if p)
        total = len(self.results)
        total_time = sum(d for _, _, d, _ in self.results)
        
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY:")
        print(f"✅ Total Passed: {passed}/{total}")
        print(f"⏱️ Total Time: {total_time:.1f}s")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            failed = total - passed
            print(f"⚠️ {failed} test(s) failed")
    
    def list_categories(self):
        """List all available test categories."""
        print("📋 Available Test Categories:")
        print("=" * 60)
        
        for category, tests in TEST_CATEGORIES.items():
            print(f"\n📁 {category} ({len(tests)} tests):")
            for test in tests:
                print(f"  - {test}")


def main():
    """Main entry point."""
    runner = SimpleTestRunner()
    
    if len(sys.argv) == 1:
        # Run all tests by default
        category = 'all'
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ['--help', '-h']:
            print(__doc__)
            runner.list_categories()
            return 0
        elif arg in ['--list', '-l']:
            runner.list_categories()
            return 0
        else:
            category = arg
    else:
        print("❌ Too many arguments. Use --help for usage information.")
        return 1
    
    # Print header
    print("🧪 OmniBAR Simple Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not (Path.cwd() / 'test_imports.py').exists():
        print("❌ Please run this script from the tests/ directory")
        return 1
    
    # Run the specified category
    result = runner.run_category(category)
    
    # Print final summary
    runner.print_summary()
    
    # Return appropriate exit code
    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
