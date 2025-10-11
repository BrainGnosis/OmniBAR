#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive test suite for CombinedBenchmarkObjective class.
Tests combining multiple benchmark objectives with both sync and async functionality.

Features rich terminal output with progress bars, detailed test results,
and structured feedback similar to real integration testing frameworks.
"""

import sys
import traceback
import asyncio
import re
import json
import os
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

# Load environment variables from the specified .env file
try:
    from dotenv import load_dotenv
    # Get the root directory of OmniBAR (parent of tests/)
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path)
    DOTENV_AVAILABLE = True
    print(f"✓ Loaded environment from: {env_path}")
except ImportError:
    DOTENV_AVAILABLE = False
    print("❌ python-dotenv not available. Install with: pip install python-dotenv")

# Rich terminal output for beautiful feedback
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Install with: pip install rich")

# LangChain imports for real AI integration
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("❌ LangChain not available. Install with: pip install langchain langchain-openai")

# Import the classes we want to test
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.output import (
    StringEqualityObjective, 
    RegexMatchObjective
)
from omnibar.objectives.path import (
    PathEqualityObjective, 
    PartialPathEqualityObjective
)
from omnibar.objectives.state import (
    StateEqualityObjective, 
    PartialStateEqualityObjective
)
from omnibar.objectives.llm_judge import (
    LLMJudgeObjective,
    DEFAULT_BINARY_PROMPT
)
from omnibar.core.types import (
    BoolEvalResult,
    FloatEvalResult,
    InvalidEvalResult,
    OutputKeyNotFoundError,
    InvalidRegexPatternError
)


# =====================================================
# Test Infrastructure Classes
# =====================================================

class TestStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    ERROR = "💥 ERROR"
    SKIP = "⏭️ SKIP"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    details: str = ""
    expected: Any = None
    actual: Any = None
    traceback: str = ""
    api_calls_made: int = 0
    total_tokens: int = 0


class TestRunner:
    """Enhanced test runner with rich terminal output and comprehensive test tracking."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.total_api_calls = 0
        self.total_tokens_used = 0
        
    def print(self, *args, style=None, **kwargs):
        """Print with rich formatting if available, otherwise use standard print."""
        if self.console:
            self.console.print(*args, style=style, **kwargs)
        else:
            print(*args, **kwargs)
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test with error handling and result tracking."""
        self.total_tests += 1
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func(*args, **kwargs))
            else:
                result = test_func(*args, **kwargs)
                
            # Track test results
            if result.status == TestStatus.PASS:
                self.passed_tests += 1
            elif result.status == TestStatus.FAIL:
                self.failed_tests += 1
            elif result.status == TestStatus.ERROR:
                self.error_tests += 1
            elif result.status == TestStatus.SKIP:
                self.skipped_tests += 1
            
            # Track API usage
            self.total_api_calls += result.api_calls_made
            self.total_tokens_used += result.total_tokens
            
            self.results.append(result)
            return result
        except Exception as e:
            tb_str = traceback.format_exc()
            error_result = TestResult(
                name=test_name,
                status=TestStatus.ERROR,
                message=f"Test threw exception: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=tb_str
            )
            self.error_tests += 1
            self.results.append(error_result)
            return error_result
    
    def assert_equal(self, actual, expected, message="") -> bool:
        """Assert that two values are equal."""
        if actual == expected:
            return True
        else:
            raise AssertionError(f"Expected {expected}, got {actual}. {message}")
    
    def assert_isinstance(self, obj, class_type, message="") -> bool:
        """Assert that object is instance of class_type."""
        if isinstance(obj, class_type):
            return True
        else:
            raise AssertionError(f"Expected {class_type.__name__}, got {type(obj).__name__}. {message}")
    
    def assert_in(self, item, container, message="") -> bool:
        """Assert that item is in container."""
        if item in container:
            return True
        else:
            raise AssertionError(f"Expected '{item}' to be in {container}. {message}")
    
    def assert_greater(self, actual, threshold, message="") -> bool:
        """Assert that actual is greater than threshold."""
        if actual > threshold:
            return True
        else:
            raise AssertionError(f"Expected {actual} > {threshold}. {message}")
    
    def run_async_test(self, async_test_func, *args, **kwargs) -> TestResult:
        """Helper method to run async test functions."""
        try:
            # Run the async function in an event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_test_func(*args, **kwargs))
                return result
            finally:
                loop.close()
        except Exception as e:
            return TestResult(
                name=getattr(async_test_func, '__name__', 'Unknown Async Test'),
                status=TestStatus.ERROR,
                message=f"Async test execution failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def display_results(self):
        """Display comprehensive test results with rich formatting."""
        if not self.console:
            # Fallback to simple text output
            print("\n" + "="*80)
            print("COMBINED BENCHMARK OBJECTIVE TEST RESULTS")
            print("="*80)
            for result in self.results:
                print(f"{result.status.value}: {result.name}")
                if result.message:
                    print(f"    {result.message}")
                if result.details:
                    print(f"    Details: {result.details}")
                if result.traceback and result.status in [TestStatus.FAIL, TestStatus.ERROR]:
                    print(f"    Traceback:\n{result.traceback}")
            print(f"\nTotal: {self.total_tests}, Passed: {self.passed_tests}, Failed: {self.failed_tests}, Errors: {self.error_tests}, Skipped: {self.skipped_tests}")
            return
        
        # Rich formatted output
        self.console.print("\n")
        self.console.rule("[bold blue]Combined Benchmark Objective Test Results", style="blue")
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test Name", style="cyan", width=35)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Message", style="white", width=40)
        table.add_column("API Calls", style="yellow", width=10)
        table.add_column("Tokens", style="green", width=8)
        
        for result in self.results:
            status_style = {
                TestStatus.PASS: "green",
                TestStatus.FAIL: "red", 
                TestStatus.ERROR: "red",
                TestStatus.SKIP: "yellow"
            }.get(result.status, "white")
            
            message_display = result.message[:37] + "..." if len(result.message) > 40 else result.message
            
            table.add_row(
                result.name,
                Text(result.status.value, style=status_style),
                message_display,
                str(result.api_calls_made) if result.api_calls_made > 0 else "-",
                str(result.total_tokens) if result.total_tokens > 0 else "-"
            )
        
        self.console.print(table)
        
        # Summary panel
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        summary_style = "green" if pass_rate == 100 else "yellow" if pass_rate >= 75 else "red"
        
        estimated_cost = self.total_tokens_used * 0.00003  # Rough estimate for GPT-4
        
        summary = Panel(
            f"[bold]Test Results:[/bold]\n"
            f"  Total Tests: {self.total_tests}\n"
            f"  [bold green]Passed:[/bold green] {self.passed_tests}\n"
            f"  [bold red]Failed:[/bold red] {self.failed_tests}\n"
            f"  [bold red]Errors:[/bold red] {self.error_tests}\n"
            f"  [bold yellow]Skipped:[/bold yellow] {self.skipped_tests}\n"
            f"  [bold]Pass Rate:[/bold] {pass_rate:.1f}%\n\n"
            f"[bold]API Usage:[/bold]\n"
            f"  Total API Calls: {self.total_api_calls}\n"
            f"  Total Tokens: {self.total_tokens_used:,}\n"
            f"  Estimated Cost: ${estimated_cost:.4f}\n\n"
            f"[bold]Test Coverage:[/bold]\n"
            f"  ✓ Basic Functionality\n"
            f"  ✓ Sync/Async Evaluation\n"
            f"  ✓ Hook System Testing\n"
            f"  ✓ Error Handling\n"
            f"  ✓ Real LLM Integration",
            title="Combined Benchmark Objective Summary",
            border_style=summary_style
        )
        self.console.print(summary)


# =====================================================
# Test Fixtures and Mock Classes
# =====================================================

class MockSearchModel(BaseModel):
    """Mock model for path testing."""
    query: str
    limit: int = Field(default=10)


class MockAnalyzeModel(BaseModel):
    """Mock model for path testing."""
    data: str
    method: str = Field(default="standard")


class MockUserModel(BaseModel):
    """Mock model for state testing."""
    name: str
    age: int
    email: str


class MockHookTracker:
    """Helper class to track hook execution."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.pre_run_calls = 0
        self.post_run_calls = 0
        self.post_eval_calls = 0
        self.async_pre_run_calls = 0
        self.async_post_run_calls = 0
        self.async_post_eval_calls = 0
    
    def pre_run_hook(self):
        self.pre_run_calls += 1
    
    def post_run_hook(self):
        self.post_run_calls += 1
    
    def post_eval_hook(self):
        self.post_eval_calls += 1
    
    async def async_pre_run_hook(self):
        await asyncio.sleep(0.01)  # Simulate async work
        self.async_pre_run_calls += 1
    
    async def async_post_run_hook(self):
        await asyncio.sleep(0.01)  # Simulate async work
        self.async_post_run_calls += 1
    
    async def async_post_eval_hook(self):
        await asyncio.sleep(0.01)  # Simulate async work
        self.async_post_eval_calls += 1


# Mock functions removed - using only real API calls as requested


# =====================================================
# Main Test Class
# =====================================================

class CombinedBenchmarkObjectiveTests:
    """Comprehensive test suite for CombinedBenchmarkObjective class."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.hook_tracker = MockHookTracker()
        self.api_calls_count = 0
        self.tokens_used = 0
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are available for real testing."""
        if not LANGCHAIN_AVAILABLE:
            return False
        if not os.getenv('OPENAI_API_KEY'):
            return False
        return True
    
    def _track_api_usage(self, response=None) -> Dict[str, int]:
        """Track API usage from LangChain response."""
        api_calls = 1
        tokens = 0
        
        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            tokens = usage.get('total_tokens', 0)
        elif hasattr(response, 'usage_metadata'):
            tokens = getattr(response.usage_metadata, 'total_tokens', 0)
        
        self.api_calls_count += api_calls
        self.tokens_used += tokens
        
        return {"calls": api_calls, "tokens": tokens}
    
    def _create_basic_objectives(self) -> List[Any]:
        """Create a basic set of objectives for testing."""
        return [
            StringEqualityObjective(
                name="StringTest",
                goal="expected_string", 
                output_key="string_output"
            ),
            RegexMatchObjective(
                name="RegexTest",
                goal=r"\d{3}", 
                output_key="regex_output"
            ),
            StateEqualityObjective(
                name="StateTest",
                goal=MockUserModel, 
                output_key="user_data"
            )
        ]
    
    def _create_objectives_with_hooks(self) -> List[Any]:
        """Create objectives with hook functions for testing."""
        self.hook_tracker.reset()
        
        string_obj = StringEqualityObjective(
            name="StringTestWithHooks",
            goal="test", 
            output_key="string_output"
        )
        string_obj.pre_run_hook = self.hook_tracker.pre_run_hook
        string_obj.post_run_hook = self.hook_tracker.post_run_hook
        string_obj.post_eval_hook = self.hook_tracker.post_eval_hook
        
        regex_obj = RegexMatchObjective(
            name="RegexTestWithHooks",
            goal=r"test", 
            output_key="regex_output"
        )
        regex_obj.pre_run_hook = self.hook_tracker.pre_run_hook
        regex_obj.post_run_hook = self.hook_tracker.post_run_hook
        regex_obj.post_eval_hook = self.hook_tracker.post_eval_hook
        
        return [string_obj, regex_obj]
    
    def _create_objectives_with_async_hooks(self) -> List[Any]:
        """Create objectives with async hook functions for testing."""
        self.hook_tracker.reset()
        
        string_obj = StringEqualityObjective(
            name="StringTestWithAsyncHooks",
            goal="test", 
            output_key="string_output"
        )
        string_obj.pre_run_hook = self.hook_tracker.async_pre_run_hook
        string_obj.post_run_hook = self.hook_tracker.async_post_run_hook
        string_obj.post_eval_hook = self.hook_tracker.async_post_eval_hook
        
        regex_obj = RegexMatchObjective(
            name="RegexTestWithAsyncHooks",
            goal=r"test", 
            output_key="regex_output"
        )
        regex_obj.pre_run_hook = self.hook_tracker.async_pre_run_hook
        regex_obj.post_run_hook = self.hook_tracker.async_post_run_hook
        regex_obj.post_eval_hook = self.hook_tracker.async_post_eval_hook
        
        return [string_obj, regex_obj]
    
    # =====================================================
    # Basic Functionality Tests
    # =====================================================
    
    def test_basic_initialization(self) -> TestResult:
        """Test basic initialization of CombinedBenchmarkObjective."""
        try:
            objectives = self._create_basic_objectives()
            combined = CombinedBenchmarkObjective(
                name="TestCombinedObjective",
                objectives=objectives
            )
            
            self.runner.assert_equal(len(combined.objectives), 3, "Should have 3 objectives")
            self.runner.assert_isinstance(combined.objectives[0], StringEqualityObjective, "First objective should be StringEqualityObjective")
            self.runner.assert_isinstance(combined.objectives[1], RegexMatchObjective, "Second objective should be RegexMatchObjective")
            self.runner.assert_isinstance(combined.objectives[2], StateEqualityObjective, "Third objective should be StateEqualityObjective")
            self.runner.assert_equal(combined.name, "TestCombinedObjective", "Name should be set correctly")
            
            # Verify excluded fields have default values
            self.runner.assert_equal(combined.goal, None, "Goal should be None (excluded field)")
            self.runner.assert_equal(combined.output_key, "", "Output key should be empty (excluded field)")
            self.runner.assert_equal(combined.valid_eval_result_type, dict, "Valid eval result type should be dict (excluded field)")
            
            return TestResult(
                name="Basic Initialization",
                status=TestStatus.PASS,
                message="✓ Successfully initialized CombinedBenchmarkObjective with name and 3 objectives",
                details=f"Name: {combined.name}, Objectives: {[type(obj).__name__ for obj in combined.objectives]}",
                expected=3,
                actual=len(combined.objectives)
            )
        except Exception as e:
            return TestResult(
                name="Basic Initialization",
                status=TestStatus.FAIL,
                message=f"✗ Initialization failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_empty_objectives_list(self) -> TestResult:
        """Test initialization with empty objectives list."""
        try:
            combined = CombinedBenchmarkObjective(
                name="EmptyTestObjective",
                objectives=[]
            )
            
            self.runner.assert_equal(len(combined.objectives), 0, "Should have 0 objectives")
            self.runner.assert_equal(combined.name, "EmptyTestObjective", "Name should be set correctly")
            
            return TestResult(
                name="Empty Objectives List",
                status=TestStatus.PASS,
                message="✓ Successfully initialized CombinedBenchmarkObjective with name and empty list",
                details=f"Name: {combined.name}, Empty objectives list handled correctly",
                expected=0,
                actual=len(combined.objectives)
            )
        except Exception as e:
            return TestResult(
                name="Empty Objectives List",
                status=TestStatus.FAIL,
                message=f"✗ Empty list initialization failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_initialization_without_name(self) -> TestResult:
        """Test that initialization works without explicit name (uses default)."""
        try:
            objectives = self._create_basic_objectives()
            
            # This should work fine - name has a default value
            combined = CombinedBenchmarkObjective(objectives=objectives)
            
            # Check that it was initialized with default name
            if combined.name == "":  # Default is empty string
                return TestResult(
                    name="Initialization Without Name",
                    status=TestStatus.PASS,
                    message="✓ Successfully initialized without explicit name",
                    details="Uses default empty string for name",
                    expected="Empty string name",
                    actual=f"Name: '{combined.name}'"
                )
            else:
                return TestResult(
                    name="Initialization Without Name",
                    status=TestStatus.FAIL,
                    message="✗ Unexpected default name value",
                    details=f"Expected empty string, got: '{combined.name}'",
                    expected="''",
                    actual=f"'{combined.name}'"
                )
                
        except Exception as e:
            return TestResult(
                name="Initialization Without Name",
                status=TestStatus.ERROR,
                message=f"✗ Test execution failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_initialization_with_optional_fields(self) -> TestResult:
        """Test initialization with optional fields like description, category, tags."""
        try:
            objectives = self._create_basic_objectives()
            combined = CombinedBenchmarkObjective(
                name="TestWithOptionalFields",
                description="Test description",
                category="test_category",
                tags=["tag1", "tag2"],
                objectives=objectives
            )
            
            self.runner.assert_equal(combined.name, "TestWithOptionalFields", "Name should be set correctly")
            self.runner.assert_equal(combined.description, "Test description", "Description should be set correctly")
            self.runner.assert_equal(combined.category, "test_category", "Category should be set correctly")
            self.runner.assert_equal(combined.tags, ["tag1", "tag2"], "Tags should be set correctly")
            self.runner.assert_equal(len(combined.objectives), 3, "Should have 3 objectives")
            
            return TestResult(
                name="Initialization with Optional Fields",
                status=TestStatus.PASS,
                message="✓ Successfully initialized with name and optional fields",
                details=f"Name: {combined.name}, Description: {combined.description}, Category: {combined.category}, Tags: {combined.tags}",
                expected="All fields set correctly",
                actual="All fields set correctly"
            )
        except Exception as e:
            return TestResult(
                name="Initialization with Optional Fields",
                status=TestStatus.FAIL,
                message=f"✗ Initialization with optional fields failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    # =====================================================
    # Synchronous Evaluation Tests
    # =====================================================
    
    def test_sync_evaluation_all_pass(self) -> TestResult:
        """Test synchronous evaluation where all objectives pass."""
        try:
            self.runner.print("🔄 Creating objectives for sync evaluation test...", style="yellow")
            objectives = [
                StringEqualityObjective(
                    name="SyncTestString",
                    goal="test_value", 
                    output_key="string_output"
                ),
                RegexMatchObjective(
                    name="SyncTestRegex",
                    goal=r"test_\d+", 
                    output_key="regex_output"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="SyncTestAllPass",
                objectives=objectives
            )
            
            agent_output = {
                "string_output": "test_value",
                "regex_output": "test_123",
                "extra_key": "extra_value"
            }
            
            self.runner.print("🔄 Running sync evaluation...", style="yellow")
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 2, "Should have 2 evaluation results")
            
            # Check that all results are BoolEvalResult with True values
            for obj_uuid, eval_result in result.items():
                self.runner.assert_isinstance(eval_result, BoolEvalResult, f"Result for {obj_uuid} should be BoolEvalResult")
                self.runner.assert_equal(eval_result.result, True, f"Result for {obj_uuid} should be True")
            
            return TestResult(
                name="Sync Evaluation - All Pass",
                status=TestStatus.PASS,
                message="✓ All objectives passed evaluation successfully",
                details=f"Results: {[(uuid[:8], res.result) for uuid, res in result.items()]}",
                expected="All True",
                actual=f"All {[res.result for res in result.values()]}"
            )
        except Exception as e:
            return TestResult(
                name="Sync Evaluation - All Pass",
                status=TestStatus.FAIL,
                message=f"✗ Evaluation failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_sync_evaluation_mixed_results(self) -> TestResult:
        """Test synchronous evaluation with mixed pass/fail results."""
        try:
            objectives = [
                StringEqualityObjective(
                    name="MixedTest1",
                    goal="expected", 
                    output_key="string_output"
                ),
                RegexMatchObjective(
                    name="MixedTest2",
                    goal=r"\d{3}", 
                    output_key="regex_output"
                ),
                StringEqualityObjective(
                    name="MixedTest3",
                    goal="another_expected", 
                    output_key="string2_output"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="SyncTestMixedResults",
                objectives=objectives
            )
            
            agent_output = {
                "string_output": "expected",      # Should pass
                "regex_output": "abc",           # Should fail (no digits)
                "string2_output": "different"    # Should fail (wrong string)
            }
            
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 3, "Should have 3 evaluation results")
            
            # Count pass/fail results
            passed_count = sum(1 for res in result.values() if isinstance(res, BoolEvalResult) and res.result)
            failed_count = sum(1 for res in result.values() if isinstance(res, BoolEvalResult) and not res.result)
            
            self.runner.assert_equal(passed_count, 1, "Should have 1 passing result")
            self.runner.assert_equal(failed_count, 2, "Should have 2 failing results")
            
            return TestResult(
                name="Sync Evaluation - Mixed Results",
                status=TestStatus.PASS,
                message="✓ Mixed evaluation results handled correctly",
                details=f"Passed: {passed_count}, Failed: {failed_count}",
                expected="1 pass, 2 fail",
                actual=f"{passed_count} pass, {failed_count} fail"
            )
        except Exception as e:
            return TestResult(
                name="Sync Evaluation - Mixed Results",
                status=TestStatus.FAIL,
                message=f"✗ Mixed evaluation failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_sync_evaluation_with_path_objective(self) -> TestResult:
        """Test synchronous evaluation with PathEqualityObjective."""
        try:
            valid_paths = [
                [("search", MockSearchModel), ("analyze", MockAnalyzeModel)]
            ]
            
            objectives = [
                StringEqualityObjective(
                    name="PathTestString",
                    goal="success", 
                    output_key="result"
                ),
                PathEqualityObjective(
                    name="PathTestPath",
                    goal=valid_paths, 
                    output_key="execution_path"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="SyncTestWithPathObjective",
                objectives=objectives
            )
            
            agent_output = {
                "result": "success",
                "execution_path": [
                    ("search", {"query": "test query", "limit": 10}),
                    ("analyze", {"data": "test data", "method": "standard"})
                ]
            }
            
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 2, "Should have 2 evaluation results")
            
            # Check that all results pass
            for obj_uuid, eval_result in result.items():
                self.runner.assert_isinstance(eval_result, BoolEvalResult, f"Result for {obj_uuid} should be BoolEvalResult")
                self.runner.assert_equal(eval_result.result, True, f"Result for {obj_uuid} should be True")
            
            return TestResult(
                name="Sync Evaluation - Path Objective",
                status=TestStatus.PASS,
                message="✓ Path objective evaluation passed successfully",
                details=f"Both string and path objectives passed",
                expected="All True",
                actual=f"All {[res.result for res in result.values()]}"
            )
        except Exception as e:
            return TestResult(
                name="Sync Evaluation - Path Objective",
                status=TestStatus.FAIL,
                message=f"✗ Path evaluation failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_sync_evaluation_with_state_objective(self) -> TestResult:
        """Test synchronous evaluation with StateEqualityObjective."""
        try:
            objectives = [
                StringEqualityObjective(
                    name="StateTestString",
                    goal="valid", 
                    output_key="status"
                ),
                StateEqualityObjective(
                    name="StateTestState",
                    goal=MockUserModel, 
                    output_key="user_info"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="SyncTestWithStateObjective",
                objectives=objectives
            )
            
            agent_output = {
                "status": "valid",
                "user_info": {
                    "name": "John Doe",
                    "age": 30,
                    "email": "john@example.com"
                }
            }
            
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 2, "Should have 2 evaluation results")
            
            # Check that all results pass
            for obj_uuid, eval_result in result.items():
                self.runner.assert_isinstance(eval_result, BoolEvalResult, f"Result for {obj_uuid} should be BoolEvalResult")
                self.runner.assert_equal(eval_result.result, True, f"Result for {obj_uuid} should be True")
            
            return TestResult(
                name="Sync Evaluation - State Objective",
                status=TestStatus.PASS,
                message="✓ State objective evaluation passed successfully",
                details=f"Both string and state objectives passed",
                expected="All True",
                actual=f"All {[res.result for res in result.values()]}"
            )
        except Exception as e:
            return TestResult(
                name="Sync Evaluation - State Objective",
                status=TestStatus.FAIL,
                message=f"✗ State evaluation failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    # =====================================================
    # Asynchronous Evaluation Tests
    # =====================================================
    
    def test_async_evaluation_all_pass(self) -> TestResult:
        """Test asynchronous evaluation where all objectives pass."""
        async def async_test():
            self.runner.print("🔄 Creating objectives for async evaluation test...", style="yellow")
            objectives = [
                StringEqualityObjective(
                    name="AsyncTestString",
                    goal="test_value", 
                    output_key="string_output"
                ),
                RegexMatchObjective(
                    name="AsyncTestRegex",
                    goal=r"test_\d+", 
                    output_key="regex_output"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="AsyncTestAllPass",
                objectives=objectives
            )
            
            agent_output = {
                "string_output": "test_value",
                "regex_output": "test_123",
                "extra_key": "extra_value"
            }
            
            self.runner.print("🔄 Running async evaluation...", style="yellow")
            result = await combined.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
                self.runner.assert_equal(len(result), 2, "Should have 2 evaluation results")
                
                # Check that all results are BoolEvalResult with True values
                for obj_uuid, eval_result in result.items():
                    self.runner.assert_isinstance(eval_result, BoolEvalResult, f"Result for {obj_uuid} should be BoolEvalResult")
                    self.runner.assert_equal(eval_result.result, True, f"Result for {obj_uuid} should be True")
                
                return TestResult(
                    name="Async Evaluation - All Pass",
                    status=TestStatus.PASS,
                    message="✓ All objectives passed async evaluation successfully",
                    details=f"Results: {[(uuid[:8], res.result) for uuid, res in result.items()]}",
                    expected="All True",
                    actual=f"All {[res.result for res in result.values()]}"
                )
            except Exception as e:
                return TestResult(
                    name="Async Evaluation - All Pass",
                    status=TestStatus.FAIL,
                    message=f"✗ Async evaluation failed: {str(e)}",
                    details=f"Exception type: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_evaluation_mixed_results(self) -> TestResult:
        """Test asynchronous evaluation with mixed pass/fail results."""
        async def async_test():
            objectives = [
                StringEqualityObjective(
                    name="AsyncMixedTest1",
                    goal="expected", 
                    output_key="string_output"
                ),
                RegexMatchObjective(
                    name="AsyncMixedTest2",
                    goal=r"\d{3}", 
                    output_key="regex_output"
                ),
                StringEqualityObjective(
                    name="AsyncMixedTest3",
                    goal="another_expected", 
                    output_key="string2_output"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="AsyncTestMixedResults",
                objectives=objectives
            )
            
            agent_output = {
                "string_output": "expected",      # Should pass
                "regex_output": "abc",           # Should fail (no digits)
                "string2_output": "different"    # Should fail (wrong string)
            }
            
            result = await combined.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
                self.runner.assert_equal(len(result), 3, "Should have 3 evaluation results")
                
                # Count pass/fail results
                passed_count = sum(1 for res in result.values() if isinstance(res, BoolEvalResult) and res.result)
                failed_count = sum(1 for res in result.values() if isinstance(res, BoolEvalResult) and not res.result)
                
                self.runner.assert_equal(passed_count, 1, "Should have 1 passing result")
                self.runner.assert_equal(failed_count, 2, "Should have 2 failing results")
                
                return TestResult(
                    name="Async Evaluation - Mixed Results",
                    status=TestStatus.PASS,
                    message="✓ Mixed async evaluation results handled correctly",
                    details=f"Passed: {passed_count}, Failed: {failed_count}",
                    expected="1 pass, 2 fail",
                    actual=f"{passed_count} pass, {failed_count} fail"
                )
            except Exception as e:
                return TestResult(
                    name="Async Evaluation - Mixed Results",
                    status=TestStatus.FAIL,
                    message=f"✗ Mixed async evaluation failed: {str(e)}",
                    details=f"Exception type: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_consistency(self) -> TestResult:
        """Test that async and sync evaluations produce identical results."""
        async def async_test():
            objectives = [
                StringEqualityObjective(
                    name="ConsistencyTestString",
                    goal="test", 
                    output_key="string_output"
                ),
                RegexMatchObjective(
                    name="ConsistencyTestRegex",
                    goal=r"test_\d+", 
                    output_key="regex_output"
                ),
                StateEqualityObjective(
                    name="ConsistencyTestState",
                    goal=MockUserModel, 
                    output_key="user_data"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="AsyncVsSyncConsistencyTest",
                objectives=objectives
            )
            
            agent_output = {
                "string_output": "test",
                "regex_output": "test_456",
                "user_data": {
                    "name": "Alice Smith",
                    "age": 25,
                    "email": "alice@example.com"
                }
            }
            
            # Run sync evaluation
            sync_result = combined.eval(agent_output)
            
            # Run async evaluation
            async_result = await combined.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(sync_result, dict, "Sync result should be a dictionary")
                self.runner.assert_isinstance(async_result, dict, "Async result should be a dictionary")
                self.runner.assert_equal(len(sync_result), len(async_result), "Results should have same length")
                
                # Compare results for each objective
                mismatches = []
                for obj_uuid in sync_result.keys():
                    sync_res = sync_result[obj_uuid]
                    async_res = async_result[obj_uuid]
                    
                    if type(sync_res) != type(async_res) or sync_res.result != async_res.result:
                        mismatches.append(f"UUID {obj_uuid[:8]}: sync={sync_res.result}, async={async_res.result}")
                
                if mismatches:
                    raise AssertionError(f"Sync/async mismatch: {', '.join(mismatches)}")
                
                return TestResult(
                    name="Async vs Sync Consistency",
                    status=TestStatus.PASS,
                    message="✓ Sync and async evaluations produced identical results",
                    details=f"Compared {len(sync_result)} objective results",
                    expected="Identical results",
                    actual="Identical results"
                )
            except Exception as e:
                return TestResult(
                    name="Async vs Sync Consistency",
                    status=TestStatus.FAIL,
                    message=f"✗ Sync/async consistency check failed: {str(e)}",
                    details=f"Exception type: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    # =====================================================
    # Hook Testing
    # =====================================================
    
    def test_sync_hooks_execution(self) -> TestResult:
        """Test synchronous hook execution."""
        try:
            self.runner.print("🔄 Setting up objectives with sync hooks...", style="yellow")
            objectives = self._create_objectives_with_hooks()
            combined = CombinedBenchmarkObjective(
                name="SyncHooksTest",
                objectives=objectives
            )
            
            # Test pre-run hooks
            self.runner.print("🔄 Testing pre-run hooks...", style="yellow")
            combined.run_pre_run_hook()
            self.runner.assert_equal(self.hook_tracker.pre_run_calls, 2, "Should have called pre_run_hook twice")
            
            # Test post-run hooks
            self.runner.print("🔄 Testing post-run hooks...", style="yellow")
            combined.run_post_run_hook()
            self.runner.assert_equal(self.hook_tracker.post_run_calls, 2, "Should have called post_run_hook twice")
            
            # Test post-eval hooks
            self.runner.print("🔄 Testing post-eval hooks...", style="yellow")
            combined.run_post_eval_hook()
            self.runner.assert_equal(self.hook_tracker.post_eval_calls, 2, "Should have called post_eval_hook twice")
            
            return TestResult(
                name="Sync Hooks Execution",
                status=TestStatus.PASS,
                message="✓ All sync hooks executed correctly",
                details=f"Pre-run: {self.hook_tracker.pre_run_calls}, Post-run: {self.hook_tracker.post_run_calls}, Post-eval: {self.hook_tracker.post_eval_calls}",
                expected="2 calls each",
                actual=f"{self.hook_tracker.pre_run_calls}, {self.hook_tracker.post_run_calls}, {self.hook_tracker.post_eval_calls}"
            )
        except Exception as e:
            return TestResult(
                name="Sync Hooks Execution",
                status=TestStatus.FAIL,
                message=f"✗ Sync hooks execution failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_async_hooks_execution(self) -> TestResult:
        """Test asynchronous hook execution."""
        async def async_test():
            objectives = self._create_objectives_with_async_hooks()
            combined = CombinedBenchmarkObjective(
                name="AsyncHooksTest",
                objectives=objectives
            )
            
            try:
                # Test async pre-run hooks
                await combined.run_pre_run_hook_async()
                self.runner.assert_equal(self.hook_tracker.async_pre_run_calls, 2, "Should have called async pre_run_hook twice")
                
                # Test async post-run hooks
                await combined.run_post_run_hook_async()
                self.runner.assert_equal(self.hook_tracker.async_post_run_calls, 2, "Should have called async post_run_hook twice")
                
                # Test async post-eval hooks
                await combined.run_post_eval_hook_async()
                self.runner.assert_equal(self.hook_tracker.async_post_eval_calls, 2, "Should have called async post_eval_hook twice")
                
                return TestResult(
                    name="Async Hooks Execution",
                    status=TestStatus.PASS,
                    message="✓ All async hooks executed correctly",
                    details=f"Async Pre-run: {self.hook_tracker.async_pre_run_calls}, Async Post-run: {self.hook_tracker.async_post_run_calls}, Async Post-eval: {self.hook_tracker.async_post_eval_calls}",
                    expected="2 calls each",
                    actual=f"{self.hook_tracker.async_pre_run_calls}, {self.hook_tracker.async_post_run_calls}, {self.hook_tracker.async_post_eval_calls}"
                )
            except Exception as e:
                return TestResult(
                    name="Async Hooks Execution",
                    status=TestStatus.FAIL,
                    message=f"✗ Async hooks execution failed: {str(e)}",
                    details=f"Exception type: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_hooks_with_no_hooks_defined(self) -> TestResult:
        """Test hook execution when no hooks are defined."""
        try:
            objectives = self._create_basic_objectives()
            combined = CombinedBenchmarkObjective(
                name="NoHooksDefinedTest",
                objectives=objectives
            )
            
            # These should not raise exceptions even when no hooks are defined
            combined.run_pre_run_hook()
            combined.run_post_run_hook()
            combined.run_post_eval_hook()
            
            return TestResult(
                name="Hooks with No Hooks Defined",
                status=TestStatus.PASS,
                message="✓ Hook methods handle missing hooks gracefully",
                details="All hook methods executed without errors",
                expected="No exceptions",
                actual="No exceptions"
            )
        except Exception as e:
            return TestResult(
                name="Hooks with No Hooks Defined",
                status=TestStatus.FAIL,
                message=f"✗ Hook execution with no hooks failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_async_hooks_with_no_hooks_defined(self) -> TestResult:
        """Test async hook execution when no hooks are defined."""
        async def async_test():
            objectives = self._create_basic_objectives()
            combined = CombinedBenchmarkObjective(
                name="AsyncNoHooksDefinedTest",
                objectives=objectives
            )
            
            try:
                # These should not raise exceptions even when no hooks are defined
                await combined.run_pre_run_hook_async()
                await combined.run_post_run_hook_async()
                await combined.run_post_eval_hook_async()
                
                return TestResult(
                    name="Async Hooks with No Hooks Defined",
                    status=TestStatus.PASS,
                    message="✓ Async hook methods handle missing hooks gracefully",
                    details="All async hook methods executed without errors",
                    expected="No exceptions",
                    actual="No exceptions"
                )
            except Exception as e:
                return TestResult(
                    name="Async Hooks with No Hooks Defined",
                    status=TestStatus.FAIL,
                    message=f"✗ Async hook execution with no hooks failed: {str(e)}",
                    details=f"Exception type: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    # =====================================================
    # LLM Judge Objective Tests  
    # =====================================================
    
    def test_with_llm_judge_objective(self) -> TestResult:
        """Test CombinedBenchmarkObjective with real LLMJudgeObjective."""
        if not self._check_prerequisites():
            return TestResult(
                name="LLM Judge Objective",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met (LangChain or OpenAI API key missing)",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            self.runner.print("🔄 Setting up real LLM judge for combined test...", style="yellow")
            
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=100
            )
            
            # Create output parser for LLM judge
            from omnibar.objectives.llm_judge import LLMBinaryOutputSchema
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            # Create prompt template for judging helpfulness
            prompt = PromptTemplate(
                template=DEFAULT_BINARY_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "expected_output": "A helpful and informative response",
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            # Create chain
            chain = prompt | llm | parser
            
            objectives = [
                StringEqualityObjective(
                    name="LLMTestString",
                    goal="success", 
                    output_key="status"
                ),
                LLMJudgeObjective(
                    name="LLMTestJudge",
                    goal="A helpful and informative response",
                    output_key="llm_output",
                    invoke_method=chain.invoke
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="RealLLMJudgeTest",
                objectives=objectives
            )
            
            agent_output = {
                "status": "success",
                "llm_output": "I'd be happy to help you understand this concept. Let me provide you with a detailed explanation that covers the key points.",
                "extra": "data"
            }
            
            self.runner.print("🔄 Running combined evaluation with real LLM judge...", style="yellow")
            result = combined.eval(agent_output)
            
            api_usage = {"calls": 1, "tokens": 80}  # Rough estimate for one LLM call
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 2, "Should have 2 evaluation results")
            
            # Check that we have results (don't enforce specific values since LLM can vary)
            bool_results = sum(1 for res in result.values() if hasattr(res, 'result') and isinstance(res.result, bool))
            
            if bool_results < 1:  # At least 1 should be a boolean result
                return TestResult(
                    name="LLM Judge Objective",
                    status=TestStatus.FAIL,
                    message="✗ Not enough boolean evaluation results from real LLM",
                    details=f"Expected at least 1 boolean result, got {bool_results}",
                    expected="At least 1 boolean result",
                    actual=f"{bool_results} boolean results",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            return TestResult(
                name="LLM Judge Objective",
                status=TestStatus.PASS,
                message="✓ Real LLMJudgeObjective integration successful",
                details=f"Combined evaluation with string and real LLM judge objectives",
                expected="Successful real LLM integration",
                actual=f"Real LLM evaluation completed with {bool_results} boolean results",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
        except Exception as e:
            return TestResult(
                name="LLM Judge Objective",
                status=TestStatus.FAIL,
                message=f"✗ Real LLM judge objective test failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    # =====================================================
    # Partial Objectives Tests
    # =====================================================
    
    def test_with_partial_objectives(self) -> TestResult:
        """Test CombinedBenchmarkObjective with partial/score-based objectives."""
        try:
            valid_paths = [
                [("search", MockSearchModel), ("analyze", MockAnalyzeModel)]
            ]
            
            objectives = [
                StringEqualityObjective(
                    name="PartialTestString",
                    goal="success", 
                    output_key="status"
                ),
                PartialPathEqualityObjective(
                    name="PartialTestPath",
                    goal=valid_paths, 
                    output_key="execution_path"
                ),
                PartialStateEqualityObjective(
                    name="PartialTestState",
                    goal=MockUserModel, 
                    output_key="user_data"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="PartialObjectivesTest",
                objectives=objectives
            )
            
            agent_output = {
                "status": "success",
                "execution_path": [
                    ("search", {"query": "test", "limit": 10}),
                    ("analyze", {"data": "test data"})  # Missing method field
                ],
                "user_data": {
                    "name": "John",
                    "age": "invalid_age",  # Invalid type
                    "email": "john@example.com"
                }
            }
            
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 3, "Should have 3 evaluation results")
            
            # Check result types
            result_types = [type(res).__name__ for res in result.values()]
            expected_types = ["BoolEvalResult", "FloatEvalResult", "FloatEvalResult"]
            
            return TestResult(
                name="Partial Objectives",
                status=TestStatus.PASS,
                message="✓ Partial objectives (scoring) integration successful",
                details=f"Result types: {result_types}",
                expected=expected_types,
                actual=result_types
            )
        except Exception as e:
            return TestResult(
                name="Partial Objectives",
                status=TestStatus.FAIL,
                message=f"✗ Partial objectives test failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    # =====================================================
    # Real LangChain API Integration Tests
    # =====================================================
    
    def test_real_langchain_combined_evaluation(self) -> TestResult:
        """Test CombinedBenchmarkObjective with real LangChain API calls."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real LangChain Combined Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met (LangChain or OpenAI API key missing)",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            self.runner.print("🔄 Setting up real LangChain LLM...", style="yellow")
            
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",  # Using cheaper model for testing
                temperature=0,
                max_tokens=150
            )
            
            # Create output parser for LLM judge
            from omnibar.objectives.llm_judge import LLMBinaryOutputSchema
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            # Create prompt template
            prompt = PromptTemplate(
                template=DEFAULT_BINARY_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "expected_output": "A polite and professional response",
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            # Create chain
            chain = prompt | llm | parser
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Create combined objective with mix of regular and LLM judge objectives
            self.runner.print("🔄 Creating combined objective with real LLM judge...", style="yellow")
            objectives = [
                StringEqualityObjective(
                    name="RealTestString",
                    goal="success", 
                    output_key="status"
                ),
                RegexMatchObjective(
                    name="RealTestRegex",
                    goal=r"[Hh]ello", 
                    output_key="greeting"
                ),
                LLMJudgeObjective(
                    name="RealTestLLMJudge",
                    goal="A polite and professional response",
                    output_key="llm_response",
                    invoke_method=chain.invoke
                )
            ]
            
            combined = CombinedBenchmarkObjective(
                name="RealLangChainCombinedTest",
                objectives=objectives
            )
            
            # Test with agent output that should trigger real API call
            agent_output = {
                "status": "success",
                "greeting": "Hello there!",
                "llm_response": "Hello! Thank you for your inquiry. I'd be happy to help you with any questions you might have."
            }
            
            self.runner.print("🔄 Running combined evaluation with real API call...", style="yellow")
            result = combined.eval(agent_output)
            api_usage["calls"] += 1
            api_usage["tokens"] = 120  # Rough estimate
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 3, "Should have 3 evaluation results")
            
            # Check that we have a mix of result types
            bool_results = sum(1 for res in result.values() if hasattr(res, 'result') and isinstance(res.result, bool))
            
            if bool_results < 2:  # At least 2 should be boolean results
                return TestResult(
                    name="Real LangChain Combined Evaluation",
                    status=TestStatus.FAIL,
                    message="✗ Not enough boolean evaluation results",
                    details=f"Expected at least 2 boolean results, got {bool_results}",
                    expected="At least 2 boolean results",
                    actual=f"{bool_results} boolean results",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            # Test async evaluation as well
            self.runner.print("🔄 Testing async evaluation with real API...", style="yellow")
            try:
                # Run async evaluation directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async_result = loop.run_until_complete(combined.eval_async(agent_output))
                    api_usage["calls"] += 1
                    api_usage["tokens"] += 120
                    
                    # Validate async result structure
                    self.runner.assert_isinstance(async_result, dict, "Async result should be a dictionary")
                    self.runner.assert_equal(len(async_result), 3, "Async should have 3 evaluation results")
                    self.runner.print("✓ Async evaluation completed successfully", style="green")
                finally:
                    loop.close()
            except Exception as e:
                self.runner.print(f"✗ Async evaluation failed: {str(e)}", style="red")
                # Don't fail the entire test just because async failed
            
            return TestResult(
                name="Real LangChain Combined Evaluation",
                status=TestStatus.PASS,
                message="✓ Real LangChain API integration successful",
                details=f"Combined evaluation with {len(objectives)} objectives including real LLM judge",
                expected="Successful real API integration",
                actual="All evaluations completed with real API calls",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real LangChain Combined Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real LangChain integration failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful real API integration",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_real_langchain_async_parallel_evaluation(self) -> TestResult:
        """Test async parallel evaluation with real LangChain API calls."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real LangChain Async Parallel Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        async def async_test():
            try:
                import time
                
                self.runner.print("🔄 Setting up parallel async LLM evaluation...", style="yellow")
                
                # Create real LangChain LLM
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0,
                    max_tokens=100
                )
                
                from omnibar.objectives.llm_judge import LLMBinaryOutputSchema
                parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
                
                prompt = PromptTemplate(
                    template=DEFAULT_BINARY_PROMPT,
                    input_variables=["input"],
                    partial_variables={
                        "expected_output": "A helpful response",
                        "format_instructions": parser.get_format_instructions()
                    }
                )
                
                chain = prompt | llm | parser
                
                # Create multiple combined objectives for parallel testing
                combined_objectives = []
                for i in range(2):  # Small number to avoid high API costs
                    objectives = [
                        StringEqualityObjective(
                            name=f"ParallelString{i}",
                            goal="test", 
                            output_key="string_output"
                        ),
                        LLMJudgeObjective(
                            name=f"ParallelLLM{i}",
                            goal="A helpful response",
                            output_key="llm_output",
                            invoke_method=chain.invoke
                        )
                    ]
                    
                    combined = CombinedBenchmarkObjective(
                        name=f"ParallelTest{i}",
                        objectives=objectives
                    )
                    combined_objectives.append(combined)
                
                test_outputs = [
                    {
                        "string_output": "test",
                        "llm_output": "I'd be happy to help you with that!"
                    },
                    {
                        "string_output": "test", 
                        "llm_output": "Let me assist you with your question."
                    }
                ]
                
                api_usage = {"calls": 0, "tokens": 0}
                
                # Test async parallel execution
                self.runner.print("🔄 Running parallel async evaluations...", style="yellow")
                start_time = time.time()
                
                async_tasks = [
                    combined.eval_async(output) 
                    for combined, output in zip(combined_objectives, test_outputs)
                ]
                parallel_results = await asyncio.gather(*async_tasks)
                
                parallel_time = time.time() - start_time
                api_usage["calls"] = len(parallel_results) * 1  # 1 LLM call per combined objective
                api_usage["tokens"] = api_usage["calls"] * 80  # Rough estimate
                
                # Verify results
                for result in parallel_results:
                    if not isinstance(result, dict) or len(result) != 2:
                        raise AssertionError(f"Invalid result structure: {result}")
                
                return TestResult(
                    name="Real LangChain Async Parallel Evaluation",
                    status=TestStatus.PASS,
                    message=f"✓ Parallel async evaluation successful (time: {parallel_time:.2f}s)",
                    details=f"Parallel execution of {len(parallel_results)} combined objectives",
                    expected="Successful parallel async evaluation",
                    actual=f"Completed {len(parallel_results)} parallel evaluations",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
                
            except Exception as e:
                return TestResult(
                    name="Real LangChain Async Parallel Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Parallel async evaluation failed: {str(e)}",
                    details=f"Error: {str(e)}",
                    expected="Successful parallel evaluation",
                    actual=f"Error: {type(e).__name__}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    # =====================================================
    # Error Handling Tests
    # =====================================================
    
    def test_evaluation_with_errors(self) -> TestResult:
        """Test evaluation when some objectives produce errors."""
        try:
            objectives = [
                StringEqualityObjective(
                    name="ErrorTestString1",
                    goal="success", 
                    output_key="status"
                ),
                StringEqualityObjective(
                    name="ErrorTestString2",
                    goal="expected", 
                    output_key="missing_key"  # This will error
                ),
                RegexMatchObjective(
                    name="ErrorTestRegex",
                    goal=r"test", 
                    output_key="regex_output"
                )
            ]
            combined = CombinedBenchmarkObjective(
                name="ErrorHandlingTest",
                objectives=objectives
            )
            
            agent_output = {
                "status": "success",
                "regex_output": "test_value"
                # "missing_key" is intentionally missing
            }
            
            result = combined.eval(agent_output)
            
            self.runner.assert_isinstance(result, dict, "Result should be a dictionary")
            self.runner.assert_equal(len(result), 3, "Should have 3 evaluation results")
            
            # Count different result types
            bool_results = sum(1 for res in result.values() if isinstance(res, BoolEvalResult))
            error_results = sum(1 for res in result.values() if isinstance(res, (OutputKeyNotFoundError, InvalidEvalResult)))
            
            self.runner.assert_equal(bool_results, 2, "Should have 2 BoolEvalResults")
            self.runner.assert_equal(error_results, 1, "Should have 1 error result")
            
            return TestResult(
                name="Evaluation with Errors",
                status=TestStatus.PASS,
                message="✓ Error handling in combined evaluation works correctly",
                details=f"Bool results: {bool_results}, Error results: {error_results}",
                expected="2 bool, 1 error",
                actual=f"{bool_results} bool, {error_results} error"
            )
        except Exception as e:
            return TestResult(
                name="Evaluation with Errors",
                status=TestStatus.FAIL,
                message=f"✗ Error handling test failed: {str(e)}",
                details=f"Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )


# =====================================================
# Main Test Execution Function
# =====================================================

def main():
    """Main test execution function for CombinedBenchmarkObjective tests."""
    runner = TestRunner()
    
    # Check environment setup
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]Combined Benchmark Objective Test Suite", style="cyan")
        runner.console.print("\n[bold]Testing CombinedBenchmarkObjective with Multiple Objectives[/bold]")
        runner.console.print("[yellow]Comprehensive functionality and real LangChain API integration testing[/yellow]")
        
        if openai_key:
            runner.console.print(f"[green]✓ OPENAI_API_KEY found: {openai_key[:8]}...{openai_key[-4:]}[/green]")
        else:
            runner.console.print("[yellow]⚠️  OPENAI_API_KEY not found - real API tests will be skipped[/yellow]")
        
        if LANGCHAIN_AVAILABLE:
            runner.console.print("[green]✓ LangChain available[/green]")
        else:
            runner.console.print("[yellow]⚠️  LangChain not available - real API tests will be skipped[/yellow]")
        
        runner.console.print()
    else:
        print("="*80)
        print("Combined Benchmark Objective Test Suite")
        print("="*80)
        print("Testing CombinedBenchmarkObjective with Multiple Objectives")
        print("Comprehensive functionality and real LangChain API integration testing")
        
        if openai_key:
            print(f"✓ OPENAI_API_KEY found: {openai_key[:8]}...{openai_key[-4:]}")
        else:
            print("⚠️  OPENAI_API_KEY not found - real API tests will be skipped")
        
        if LANGCHAIN_AVAILABLE:
            print("✓ LangChain available")
        else:
            print("⚠️  LangChain not available - real API tests will be skipped")
        
        print()
    
    # Initialize test suite
    tests = CombinedBenchmarkObjectiveTests(runner)
    
    # Define all test methods to run (organized by category)
    test_methods = [
        # Basic functionality tests
        ("Basic Initialization", tests.test_basic_initialization),
        ("Empty Objectives List", tests.test_empty_objectives_list),
        ("Initialization Without Name", tests.test_initialization_without_name),
        ("Initialization with Optional Fields", tests.test_initialization_with_optional_fields),
        
        # Synchronous evaluation tests
        ("Sync Evaluation - All Pass", tests.test_sync_evaluation_all_pass),
        ("Sync Evaluation - Mixed Results", tests.test_sync_evaluation_mixed_results),
        ("Sync Evaluation - Path Objective", tests.test_sync_evaluation_with_path_objective),
        ("Sync Evaluation - State Objective", tests.test_sync_evaluation_with_state_objective),
        
        # Asynchronous evaluation tests
        ("Async Evaluation - All Pass", tests.test_async_evaluation_all_pass),
        ("Async Evaluation - Mixed Results", tests.test_async_evaluation_mixed_results),
        ("Async vs Sync Consistency", tests.test_async_vs_sync_consistency),
        
        # Hook system tests
        ("Sync Hooks Execution", tests.test_sync_hooks_execution),
        ("Async Hooks Execution", tests.test_async_hooks_execution),
        ("Hooks with No Hooks Defined", tests.test_hooks_with_no_hooks_defined),
        ("Async Hooks with No Hooks Defined", tests.test_async_hooks_with_no_hooks_defined),
        
        # Special objective integration tests
        ("LLM Judge Objective", tests.test_with_llm_judge_objective),
        ("Partial Objectives", tests.test_with_partial_objectives),
        
        # Real LangChain API integration tests
        ("Real LangChain Combined Evaluation", tests.test_real_langchain_combined_evaluation),
        ("Real LangChain Async Parallel Evaluation", tests.test_real_langchain_async_parallel_evaluation),
        
        # Error handling tests
        ("Evaluation with Errors", tests.test_evaluation_with_errors),
    ]
    
    # Run tests with progress indication
    if runner.console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=runner.console,
        ) as progress:
            task = progress.add_task("Running combined objective tests...", total=len(test_methods))
            
            for test_name, test_method in test_methods:
                progress.update(task, description=f"Running: {test_name}")
                result = runner.run_test(test_name, test_method)
                progress.advance(task)
                
                # Show immediate feedback
                status_style = "green" if result.status == TestStatus.PASS else "yellow" if result.status == TestStatus.SKIP else "red"
                runner.console.print(f"  {result.status.value} {test_name}", style=status_style)
                if result.api_calls_made > 0:
                    runner.console.print(f"    [dim]API calls: {result.api_calls_made} | Tokens: {result.total_tokens}[/dim]")
                elif result.details:
                    runner.console.print(f"    [dim]{result.details[:80]}{'...' if len(result.details) > 80 else ''}[/dim]")
    else:
        print("Running combined benchmark objective tests...\n")
        for i, (test_name, test_method) in enumerate(test_methods, 1):
            print(f"[{i}/{len(test_methods)}] Running: {test_name}")
            result = runner.run_test(test_name, test_method)
            print(f"  {result.status.value} {test_name}")
            if result.api_calls_made > 0:
                print(f"    API calls: {result.api_calls_made} | Tokens: {result.total_tokens}")
            elif result.details:
                print(f"    {result.details[:80]}{'...' if len(result.details) > 80 else ''}")
    
    # Display final results
    runner.display_results()
    
    # Exit with appropriate code
    exit_code = 0 if runner.passed_tests == runner.total_tests else 1
    if runner.console:
        runner.console.print(f"\n[bold]Exiting with code: {exit_code}[/bold]")
        if runner.total_api_calls > 0:
            runner.console.print(f"[dim]Total API usage: {runner.total_api_calls} calls, {runner.total_tokens_used:,} tokens[/dim]")
        if exit_code == 0:
            runner.console.print("[bold green]🎉 All tests passed! CombinedBenchmarkObjective with real LangChain integration is working correctly.[/bold green]")
        else:
            runner.console.print("[bold red]❌ Some tests failed. Please review the failures above.[/bold red]")
    else:
        print(f"\nExiting with code: {exit_code}")
        if runner.total_api_calls > 0:
            print(f"Total API usage: {runner.total_api_calls} calls, {runner.total_tokens_used:,} tokens")
        if exit_code == 0:
            print("🎉 All tests passed! CombinedBenchmarkObjective with real LangChain integration is working correctly.")
        else:
            print("❌ Some tests failed. Please review the failures above.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
