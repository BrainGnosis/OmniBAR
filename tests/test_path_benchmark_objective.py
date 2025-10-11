#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive test suite for PathBenchmarkObjective classes.
Tests PathEqualityObjective with multiple valid paths and rich terminal feedback.
"""

import sys
import traceback
import asyncio
from typing import Any, List
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

# Rich terminal output for beautiful feedback
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Install with: pip install rich")

# Import the classes we want to test
from omnibar.objectives.path import (
    PathEqualityObjective,
    PartialPathEqualityObjective
)
from omnibar.core.types import (
    BoolEvalResult,
    FloatEvalResult,
    InvalidEvalResult,
    OutputKeyNotFoundError,
    FormattingError
)


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


class TestRunner:
    """Enhanced test runner with rich terminal output."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
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
            result = test_func(*args, **kwargs)
            if result.status == TestStatus.PASS:
                self.passed_tests += 1
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
    
    def display_results(self):
        """Display comprehensive test results."""
        if not self.console:
            # Fallback to simple text output
            print("\n" + "="*60)
            print("TEST RESULTS SUMMARY")
            print("="*60)
            for result in self.results:
                print(f"{result.status.value}: {result.name}")
                if result.message:
                    print(f"    {result.message}")
                if result.details:
                    print(f"    Details: {result.details}")
                if result.traceback and result.status in [TestStatus.FAIL, TestStatus.ERROR]:
                    print(f"    Traceback:\n{result.traceback}")
            print(f"\nTotal: {self.total_tests}, Passed: {self.passed_tests}, Failed: {self.total_tests - self.passed_tests}")
            return
        
        # Rich formatted output
        self.console.print("\n")
        self.console.rule("[bold blue]Test Results Summary", style="blue")
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test Name", style="cyan", width=40)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Message", style="white", width=50)
        
        for result in self.results:
            status_style = {
                TestStatus.PASS: "green",
                TestStatus.FAIL: "red", 
                TestStatus.ERROR: "red",
                TestStatus.SKIP: "yellow"
            }.get(result.status, "white")
            
            message_display = result.message[:47] + "..." if len(result.message) > 50 else result.message
            
            table.add_row(
                result.name,
                Text(result.status.value, style=status_style),
                message_display
            )
        
        self.console.print(table)
        
        # Summary panel
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        summary_style = "green" if pass_rate == 100 else "yellow" if pass_rate >= 75 else "red"
        
        summary = Panel(
            f"[bold]Total Tests:[/bold] {self.total_tests}\n"
            f"[bold green]Passed:[/bold green] {self.passed_tests}\n"
            f"[bold red]Failed:[/bold red] {self.total_tests - self.passed_tests}\n"
            f"[bold]Pass Rate:[/bold] {pass_rate:.1f}%",
            title="Summary",
            border_style=summary_style
        )
        self.console.print(summary)
    
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


# Test Models for PathEqualityObjective
class SearchModel(BaseModel):
    query: str
    limit: int = 10

class FilterModel(BaseModel):
    field: str
    value: str

class AnalyzeModel(BaseModel):
    data: str
    method: str = "default"


class PathBenchmarkObjectiveTests:
    """Comprehensive test suite for PathEqualityObjective class."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    def test_path_equality_single_valid_path_match(self) -> TestResult:
        """Test PathEqualityObjective with single valid path that matches."""
        # Define one valid path: search -> filter -> analyze
        valid_paths = [
            [
                ("search", SearchModel),
                ("filter", FilterModel),
                ("analyze", AnalyzeModel)
            ]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Matching output path
        output_path = [
            ("search", {"query": "test query", "limit": 5}),
            ("filter", {"field": "name", "value": "test"}),
            ("analyze", {"data": "result", "method": "advanced"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should match the valid path")
            
            return TestResult(
                name="Path Equality - Single Valid Path Match",
                status=TestStatus.PASS,
                message="✓ Output path matched the single valid path successfully",
                details=f"Valid paths: 1 | Output matched path 0 | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Single Valid Path Match",
                status=TestStatus.FAIL,
                message=f"✗ Expected path match failed: {str(e)}",
                details=f"Valid paths: 1 | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_multiple_valid_paths_match_first(self) -> TestResult:
        """Test PathEqualityObjective with multiple valid paths, matching the first one."""
        # Define multiple valid paths
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],  # Path 0: search -> analyze
            [("filter", FilterModel), ("search", SearchModel), ("analyze", AnalyzeModel)],  # Path 1: filter -> search -> analyze
            [("analyze", AnalyzeModel)]  # Path 2: just analyze
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output that matches the first valid path
        output_path = [
            ("search", {"query": "test query", "limit": 10}),
            ("analyze", {"data": "search results"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should match the first valid path")
            
            return TestResult(
                name="Path Equality - Multiple Paths Match First",
                status=TestStatus.PASS,
                message="✓ Output path matched the first of multiple valid paths",
                details=f"Valid paths: 3 | Output matched path 0 | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Multiple Paths Match First",
                status=TestStatus.FAIL,
                message=f"✗ Expected first path match failed: {str(e)}",
                details=f"Valid paths: 3 | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_multiple_valid_paths_match_second(self) -> TestResult:
        """Test PathEqualityObjective with multiple valid paths, matching the second one."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],  # Path 0
            [("filter", FilterModel), ("search", SearchModel), ("analyze", AnalyzeModel)],  # Path 1
            [("analyze", AnalyzeModel)]  # Path 2
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output that matches the second valid path
        output_path = [
            ("filter", {"field": "status", "value": "active"}),
            ("search", {"query": "filtered query"}),
            ("analyze", {"data": "filtered results"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should match the second valid path")
            
            return TestResult(
                name="Path Equality - Multiple Paths Match Second",
                status=TestStatus.PASS,
                message="✓ Output path matched the second of multiple valid paths",
                details=f"Valid paths: 3 | Output matched path 1 | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Multiple Paths Match Second",
                status=TestStatus.FAIL,
                message=f"✗ Expected second path match failed: {str(e)}",
                details=f"Valid paths: 3 | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_no_valid_path_matches(self) -> TestResult:
        """Test PathEqualityObjective where output doesn't match any valid path."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],
            [("filter", FilterModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output that doesn't match any valid path (wrong tool order)
        output_path = [
            ("analyze", {"data": "premature analysis"}),
            ("search", {"query": "search after analyze"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should not match any valid path")
            
            return TestResult(
                name="Path Equality - No Valid Path Matches",
                status=TestStatus.PASS,
                message="✓ Correctly identified that output doesn't match any valid path",
                details=f"Valid paths: 2 | No matches found | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - No Valid Path Matches",
                status=TestStatus.FAIL,
                message=f"✗ Expected no match detection failed: {str(e)}",
                details=f"Valid paths: 2 | Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_wrong_tool_name(self) -> TestResult:
        """Test PathEqualityObjective with wrong tool name in output."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output with wrong tool name
        output_path = [
            ("wrong_search", {"query": "test"}),  # Wrong tool name
            ("analyze", {"data": "result"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should fail due to wrong tool name")
            
            return TestResult(
                name="Path Equality - Wrong Tool Name",
                status=TestStatus.PASS,
                message="✓ Correctly detected wrong tool name in path",
                details=f"Expected 'search', got 'wrong_search' | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Wrong Tool Name",
                status=TestStatus.FAIL,
                message=f"✗ Wrong tool name detection failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_invalid_args(self) -> TestResult:
        """Test PathEqualityObjective with invalid arguments for tool."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output with invalid args for SearchModel
        output_path = [
            ("search", {"query": "test", "limit": "not_an_int"}),  # limit should be int
            ("analyze", {"data": "result"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should fail due to invalid args")
            
            return TestResult(
                name="Path Equality - Invalid Args",
                status=TestStatus.PASS,
                message="✓ Correctly detected invalid arguments for tool",
                details=f"Invalid limit type in SearchModel | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Invalid Args",
                status=TestStatus.FAIL,
                message=f"✗ Invalid args detection failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_length_mismatch(self) -> TestResult:
        """Test PathEqualityObjective with different path lengths."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],  # Length 2
            [("filter", FilterModel), ("search", SearchModel), ("analyze", AnalyzeModel)]  # Length 3
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output with length 1 (doesn't match any valid path length)
        output_path = [
            ("search", {"query": "lone search"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should fail due to length mismatch")
            
            return TestResult(
                name="Path Equality - Length Mismatch",
                status=TestStatus.PASS,
                message="✓ Correctly detected path length mismatch",
                details=f"Output length: 1, Valid path lengths: [2, 3] | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Length Mismatch",
                status=TestStatus.FAIL,
                message=f"✗ Length mismatch detection failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_none_schema(self) -> TestResult:
        """Test PathEqualityObjective with None schema (no validation required)."""
        valid_paths = [
            [("tool1", None), ("tool2", SearchModel)]  # tool1 has no schema validation
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output with any args for tool1 (should be accepted)
        output_path = [
            ("tool1", {"any": "args", "should": "work"}),
            ("tool2", {"query": "test"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should pass with None schema")
            
            return TestResult(
                name="Path Equality - None Schema",
                status=TestStatus.PASS,
                message="✓ Correctly handled tool with None schema (no validation)",
                details=f"tool1 has no schema validation | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - None Schema",
                status=TestStatus.FAIL,
                message=f"✗ None schema handling failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    

    
    def test_path_equality_missing_output_key(self) -> TestResult:
        """Test PathEqualityObjective with missing output key."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="missing_key")
        
        # Agent output doesn't contain the expected key
        agent_output = {"other_key": [("search", {"query": "test"})]}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError")
            
            return TestResult(
                name="Path Equality - Missing Output Key",
                status=TestStatus.PASS,
                message="✓ Correctly detected missing output key",
                details=f"Expected key 'missing_key' not found | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Missing Output Key",
                status=TestStatus.FAIL,
                message=f"✗ Missing key detection failed: {str(e)}",
                details=f"Result type: {type(result).__name__}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_empty_agent_output(self) -> TestResult:
        """Test PathEqualityObjective with completely empty agent output."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        agent_output = {}  # Completely empty
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError for empty output")
            
            return TestResult(
                name="Path Equality - Empty Agent Output",
                status=TestStatus.PASS,
                message="✓ Correctly handled empty agent output",
                details=f"Expected key 'test_path' not found in empty output | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Empty Agent Output",
                status=TestStatus.FAIL,
                message=f"✗ Empty agent output handling failed: {str(e)}",
                details=f"Result type: {type(result).__name__}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_none_agent_output(self) -> TestResult:
        """Test PathEqualityObjective with None as agent output."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        try:
            result = objective.eval(None)
            
            # Should handle None gracefully (likely with an error)
            if hasattr(result, '__class__') and ('Error' in str(type(result)) or 'Exception' in str(type(result))):
                return TestResult(
                    name="Path Equality - None Agent Output",
                    status=TestStatus.PASS,
                    message=f"✓ Correctly handled None agent output with {type(result).__name__}",
                    details=f"Input: None | Result type: {type(result).__name__} | Message: {getattr(result, 'message', 'N/A')}",
                    expected="Error type or Exception",
                    actual=type(result).__name__
                )
            else:
                return TestResult(
                    name="Path Equality - None Agent Output",
                    status=TestStatus.FAIL,
                    message=f"✗ Expected error type but got {type(result).__name__}",
                    details=f"Input: None | Result type: {type(result).__name__}",
                    expected="Error type",
                    actual=type(result).__name__
                )
        except Exception as e:
            # Exception is also acceptable behavior
            return TestResult(
                name="Path Equality - None Agent Output",
                status=TestStatus.PASS,
                message=f"✓ Correctly raised exception for None agent output: {type(e).__name__}",
                details=f"Input: None | Exception: {str(e)}",
                expected="Exception or Error",
                actual=f"Exception: {type(e).__name__}"
            )
    
    def test_async_path_equality_basic(self) -> TestResult:
        """Test basic async functionality of PathEqualityObjective."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)]
            ]
            objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            # Valid matching path
            output_path = [
                ("search", {"query": "async test", "limit": 5}),
                ("analyze", {"data": "async results"})
            ]
            agent_output = {"test_path": output_path}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, True, "Should return True for valid async path")
                
                return TestResult(
                    name="Async Path Equality - Basic",
                    status=TestStatus.PASS,
                    message="✓ Async path evaluation successful",
                    details=f"Valid paths: 1 | Output matched | Result: {result.result}",
                    expected=True,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Path Equality - Basic",
                    status=TestStatus.FAIL,
                    message=f"✗ Async path evaluation failed: {str(e)}",
                    details=f"Valid paths: 1 | Result type: {type(result).__name__}",
                    expected=True,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_path_equality_validation_failure(self) -> TestResult:
        """Test async functionality with path validation failure."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)]
            ]
            objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            # Invalid path - wrong tool name
            output_path = [
                ("wrong_search", {"query": "async test"}),  # Wrong tool name
                ("analyze", {"data": "async results"})
            ]
            agent_output = {"test_path": output_path}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, False, "Should return False for invalid async path")
                
                return TestResult(
                    name="Async Path Equality - Validation Failure",
                    status=TestStatus.PASS,
                    message="✓ Async path validation failure correctly detected",
                    details=f"Wrong tool name detected | Result: {result.result}",
                    expected=False,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Path Equality - Validation Failure",
                    status=TestStatus.FAIL,
                    message=f"✗ Async validation failure test failed: {str(e)}",
                    details=f"Wrong tool: 'wrong_search' | Result type: {type(result).__name__}",
                    expected=False,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_path_equality_json_formatting(self) -> TestResult:
        """Test async functionality with JSON string formatting in path arguments."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("filter", FilterModel)]
            ]
            objective = PathEqualityObjective(goal=valid_paths, output_key="json_path")
            
            # Path with JSON string arguments
            output_path = [
                ("search", '{"query": "async json test", "limit": 15}'),  # JSON string
                ("filter", {"field": "status", "value": "active"})        # Regular dict
            ]
            agent_output = {"json_path": output_path}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, True, "Should return True for valid async JSON parsing")
                
                return TestResult(
                    name="Async Path Equality - JSON Formatting",
                    status=TestStatus.PASS,
                    message="✓ Async JSON string parsing and validation successful",
                    details=f"Mixed JSON string and dict args | Result: {result.result}",
                    expected=True,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Path Equality - JSON Formatting",
                    status=TestStatus.FAIL,
                    message=f"✗ Async JSON parsing failed: {str(e)}",
                    details=f"JSON string parsing error | Result type: {type(result).__name__}",
                    expected=True,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_path_consistency(self) -> TestResult:
        """Test that async and sync path evaluations produce identical results."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)],
                [("filter", FilterModel), ("analyze", AnalyzeModel)]
            ]
            objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            test_cases = [
                # (output_path, description)
                ([("search", {"query": "test", "limit": 10}), ("analyze", {"data": "results"})], "valid first path"),
                ([("filter", {"field": "name", "value": "test"}), ("analyze", {"data": "results"})], "valid second path"),
                ([("wrong_tool", {"any": "args"}), ("analyze", {"data": "results"})], "wrong tool name"),
                ([("search", {"query": "test", "limit": "invalid"}), ("analyze", {"data": "results"})], "invalid args"),
            ]
            
            results = []
            
            try:
                for output_path, description in test_cases:
                    agent_output = {"test_path": output_path}
                    
                    # Run sync evaluation
                    sync_result = objective.eval(agent_output)
                    
                    # Run async evaluation
                    async_result = await objective.eval_async(agent_output)
                    
                    # Compare results
                    sync_type = type(sync_result).__name__
                    async_type = type(async_result).__name__
                    sync_value = getattr(sync_result, 'result', None)
                    async_value = getattr(async_result, 'result', None)
                    
                    # Check that both have same type and value
                    self.runner.assert_equal(sync_type, async_type, f"Type mismatch for {description}")
                    self.runner.assert_equal(sync_value, async_value, f"Value mismatch for {description}")
                    
                    results.append(f"{description}: {sync_type}({sync_value})")
                
                return TestResult(
                    name="Async vs Sync Path Consistency",
                    status=TestStatus.PASS,
                    message="✓ Async and sync path evaluations produce identical results",
                    details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                    expected="Identical async/sync path results",
                    actual="All results match"
                )
            except Exception as e:
                return TestResult(
                    name="Async vs Sync Path Consistency",
                    status=TestStatus.FAIL,
                    message=f"✗ Async/sync path consistency test failed: {str(e)}",
                    details=f"Completed tests: {results} | Error: {str(e)}",
                    expected="Identical async/sync path results",
                    actual=f"Error: {str(e)}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)


class PartialPathBenchmarkObjectiveTests:
    """Comprehensive test suite for PartialPathEqualityObjective class."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    def test_partial_path_equality_perfect_match(self) -> TestResult:
        """Test PartialPathEqualityObjective with perfect path match."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],
            [("filter", FilterModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Perfect match with first valid path
        output_path = [
            ("search", {"query": "test query", "limit": 10}),
            ("analyze", {"data": "search results"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 1.0, "Perfect match should return 1.0")
            
            return TestResult(
                name="Partial Path Equality - Perfect Match",
                status=TestStatus.PASS,
                message="✓ Perfect path match returned 1.0 similarity score",
                details=f"Matched valid path 0 perfectly | Score: {result.result}",
                expected=1.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Perfect Match",
                status=TestStatus.FAIL,
                message=f"✗ Perfect match test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected=1.0,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_partial_match(self) -> TestResult:
        """Test PartialPathEqualityObjective with partial path match."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Partial match - correct tools but invalid args for search
        output_path = [
            ("search", {"query": "test", "limit": "invalid_limit"}),  # Invalid limit type
            ("analyze", {"data": "results"})  # Valid
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # Should be between 0.0 and 1.0, but less than 1.0 due to validation error
            assert 0.0 < result.result < 1.0, f"Partial match should be between 0.0 and 1.0, got {result.result}"
            
            return TestResult(
                name="Partial Path Equality - Partial Match",
                status=TestStatus.PASS,
                message="✓ Partial path match returned appropriate similarity score",
                details=f"Tool names match but args invalid | Score: {result.result:.2f}",
                expected="0.0 < score < 1.0",
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Partial Match",
                status=TestStatus.FAIL,
                message=f"✗ Partial match test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected="0.0 < score < 1.0",
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_wrong_tools(self) -> TestResult:
        """Test PartialPathEqualityObjective with completely wrong tools."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Completely wrong tools
        output_path = [
            ("wrong_tool1", {"any": "args"}),
            ("wrong_tool2", {"other": "args"})
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 0.0, "Wrong tools should return 0.0 similarity")
            
            return TestResult(
                name="Partial Path Equality - Wrong Tools",
                status=TestStatus.PASS,
                message="✓ Wrong tools correctly returned 0.0 similarity score",
                details=f"No tool names matched | Score: {result.result}",
                expected=0.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Wrong Tools",
                status=TestStatus.FAIL,
                message=f"✗ Wrong tools test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected=0.0,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_length_mismatch(self) -> TestResult:
        """Test PartialPathEqualityObjective with length mismatch but some correct tools."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]  # Length 2
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output length 3, but first tool matches
        output_path = [
            ("search", {"query": "test"}),  # Matches
            ("extra_tool", {"extra": "data"}),  # Extra step
            ("analyze", {"data": "results"})  # Would match if at position 1
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # Should be low due to length mismatch and position mismatch
            assert 0.0 <= result.result < 0.5, f"Length mismatch should give low score, got {result.result}"
            
            return TestResult(
                name="Partial Path Equality - Length Mismatch",
                status=TestStatus.PASS,
                message="✓ Length mismatch correctly penalized similarity score",
                details=f"Output length 3, valid length 2 | Score: {result.result:.2f}",
                expected="Low score < 0.5",
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Length Mismatch",
                status=TestStatus.FAIL,
                message=f"✗ Length mismatch test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected="Low score < 0.5",
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_multiple_valid_paths_best_match(self) -> TestResult:
        """Test PartialPathEqualityObjective choosing best match among multiple valid paths."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)],  # Length 2
            [("filter", FilterModel), ("search", SearchModel), ("analyze", AnalyzeModel)],  # Length 3
            [("analyze", AnalyzeModel)]  # Length 1
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Output that partially matches the second valid path better than others
        output_path = [
            ("filter", {"field": "name", "value": "test"}),  # Perfect match
            ("search", {"query": "test", "limit": "invalid"}),  # Tool matches, args invalid
            ("analyze", {"data": "results"})  # Perfect match
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # Should be high since 2/3 steps are perfect and 1/3 has tool name match
            assert 0.5 < result.result < 1.0, f"Should get good score for best match, got {result.result}"
            
            return TestResult(
                name="Partial Path Equality - Multiple Paths Best Match",
                status=TestStatus.PASS,
                message="✓ Correctly chose best match among multiple valid paths",
                details=f"Best match with path 1 (3 steps) | Score: {result.result:.2f}",
                expected="Good score > 0.5",
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Multiple Paths Best Match",
                status=TestStatus.FAIL,
                message=f"✗ Multiple paths best match test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected="Good score > 0.5",
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_empty_paths(self) -> TestResult:
        """Test PartialPathEqualityObjective with empty paths."""
        valid_paths = [
            []  # Empty valid path
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Empty output path
        output_path = []
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 1.0, "Empty paths should match perfectly")
            
            return TestResult(
                name="Partial Path Equality - Empty Paths",
                status=TestStatus.PASS,
                message="✓ Empty paths correctly matched with 1.0 similarity",
                details=f"Both paths empty | Score: {result.result}",
                expected=1.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Empty Paths",
                status=TestStatus.FAIL,
                message=f"✗ Empty paths test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected=1.0,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_none_schema(self) -> TestResult:
        """Test PartialPathEqualityObjective with None schema (no validation)."""
        valid_paths = [
            [("tool1", None), ("tool2", SearchModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # First tool has no schema, second has valid args
        output_path = [
            ("tool1", {"any": "args", "should": "work"}),  # No validation required
            ("tool2", {"query": "test"})  # Valid args
        ]
        agent_output = {"test_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 1.0, "None schema should allow any args")
            
            return TestResult(
                name="Partial Path Equality - None Schema",
                status=TestStatus.PASS,
                message="✓ None schema correctly allowed any arguments",
                details=f"tool1 no validation, tool2 valid | Score: {result.result}",
                expected=1.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - None Schema",
                status=TestStatus.FAIL,
                message=f"✗ None schema test failed: {str(e)}",
                details=f"Score: {getattr(result, 'result', 'N/A')}",
                expected=1.0,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_invalid_output_format(self) -> TestResult:
        """Test PartialPathEqualityObjective with invalid output format."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Invalid format - not a list
        agent_output = {"test_path": "not_a_list"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, InvalidEvalResult, "Should return InvalidEvalResult")
            
            return TestResult(
                name="Partial Path Equality - Invalid Output Format",
                status=TestStatus.PASS,
                message="✓ Invalid output format correctly detected",
                details=f"Non-list output detected | Error: {result.message}",
                expected="InvalidEvalResult",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Invalid Output Format",
                status=TestStatus.FAIL,
                message=f"✗ Invalid format detection failed: {str(e)}",
                details=f"Result type: {type(result).__name__}",
                expected="InvalidEvalResult",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_valid_result_type(self) -> TestResult:
        """Test PartialPathEqualityObjective returns correct result type."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        try:
            expected_type = objective.valid_eval_result_type
            self.runner.assert_equal(expected_type, FloatEvalResult, "Should specify FloatEvalResult as valid type")
            
            return TestResult(
                name="Partial Path Equality - Valid Result Type",
                status=TestStatus.PASS,
                message="✓ Correctly specifies FloatEvalResult as valid result type",
                details=f"valid_eval_result_type: {expected_type.__name__}",
                expected="FloatEvalResult",
                actual=expected_type.__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Valid Result Type",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type test failed: {str(e)}",
                details=f"Type: {getattr(objective, 'valid_eval_result_type', 'N/A')}",
                expected="FloatEvalResult",
                actual=getattr(objective, 'valid_eval_result_type', None),
                traceback=traceback.format_exc()
            )
    


    def test_path_equality_complex_nested_models(self) -> TestResult:
        """Test PathEqualityObjective with complex nested Pydantic models."""
        from pydantic import field_validator
        
        class ComplexSearchModel(BaseModel):
            query: str
            filters: dict
            pagination: dict = {"page": 1, "size": 10}
            
            @field_validator('query')
            @classmethod
            def validate_query(cls, v):
                if len(v.strip()) < 3:
                    raise ValueError('Query must be at least 3 characters')
                return v.strip()
        
        class AdvancedAnalysisModel(BaseModel):
            algorithm: str
            parameters: dict
            output_format: str = "json"
            
            @field_validator('algorithm')
            @classmethod
            def validate_algorithm(cls, v):
                valid_algorithms = ['neural_network', 'decision_tree', 'svm', 'random_forest']
                if v not in valid_algorithms:
                    raise ValueError(f'Algorithm must be one of: {valid_algorithms}')
                return v
        
        valid_paths = [
            [("complex_search", ComplexSearchModel), ("advanced_analysis", AdvancedAnalysisModel)],
            [("advanced_analysis", AdvancedAnalysisModel)]  # Single step path
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="complex_path")
        
        # Valid complex path
        output_path = [
            ("complex_search", {
                "query": "machine learning algorithms",
                "filters": {"category": "research", "year": 2023},
                "pagination": {"page": 1, "size": 20}
            }),
            ("advanced_analysis", {
                "algorithm": "neural_network",
                "parameters": {"layers": [128, 64, 32], "activation": "relu"},
                "output_format": "detailed_json"
            })
        ]
        agent_output = {"complex_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Complex nested models should validate successfully")
            
            return TestResult(
                name="Path Equality - Complex Nested Models",
                status=TestStatus.PASS,
                message="✓ Complex nested models with validators passed successfully",
                details=f"Complex search + advanced analysis | Custom validators applied | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Complex Nested Models",
                status=TestStatus.FAIL,
                message=f"✗ Complex nested models test failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_invalid_tuple_structure(self) -> TestResult:
        """Test PathEqualityObjective with invalid tuple structure in output."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="test_path")
        
        # Invalid structures
        test_cases = [
            ("string_instead_of_tuple", "String instead of tuple"),
            (["list", "instead", "of", "tuple"], "List instead of tuple"),
            ({"dict": "instead_of_tuple"}, "Dict instead of tuple"),
            (("only_one_element",), "Tuple with only one element"),
            (("tool", "args", "extra"), "Tuple with three elements"),
            (None, "None instead of tuple")
        ]
        
        results = []
        
        try:
            for invalid_structure, description in test_cases:
                agent_output = {"test_path": [invalid_structure]}
                result = objective.eval(agent_output)
                
                # Should handle invalid structures gracefully
                if hasattr(result, '__class__') and ('Error' in str(type(result)) or 'Invalid' in str(type(result))):
                    results.append(f"{description}: ✓ {type(result).__name__}")
                elif isinstance(result, BoolEvalResult) and not result.result:
                    results.append(f"{description}: ✓ BoolEvalResult(False)")
                else:
                    return TestResult(
                        name="Path Equality - Invalid Tuple Structure",
                        status=TestStatus.FAIL,
                        message=f"✗ {description} was not handled properly",
                        details=f"Input: {invalid_structure} | Result: {type(result).__name__}",
                        expected="Error or False result",
                        actual=type(result).__name__
                    )
            
            return TestResult(
                name="Path Equality - Invalid Tuple Structure",
                status=TestStatus.PASS,
                message="✓ All invalid tuple structures handled correctly: " + " | ".join(results[:3]) + ("..." if len(results) > 3 else ""),
                details=f"Tested {len(test_cases)} invalid structures | All handled appropriately",
                expected="Error handling for invalid structures",
                actual="All structures handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Invalid Tuple Structure",
                status=TestStatus.FAIL,
                message=f"✗ Invalid tuple structure test failed: {str(e)}",
                details=f"Completed tests: {len(results)} | Error: {str(e)}",
                expected="Error handling for invalid structures",
                actual=f"Exception: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_json_string_conversion(self) -> TestResult:
        """Test PathEqualityObjective with JSON string arguments that need parsing."""
        valid_paths = [
            [("search", SearchModel), ("filter", FilterModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="json_path")
        
        # Path with JSON strings as arguments
        output_path = [
            ("search", '{"query": "json test", "limit": 15}'),  # JSON string
            ("filter", {"field": "status", "value": "active"})  # Regular dict
        ]
        agent_output = {"json_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "JSON string arguments should be parsed and validated")
            
            return TestResult(
                name="Path Equality - JSON String Conversion",
                status=TestStatus.PASS,
                message="✓ JSON string arguments correctly parsed and validated",
                details=f"Mixed JSON string and dict args | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - JSON String Conversion",
                status=TestStatus.FAIL,
                message=f"✗ JSON string conversion test failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_malformed_json_strings(self) -> TestResult:
        """Test PathEqualityObjective with malformed JSON strings."""
        valid_paths = [
            [("search", SearchModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="json_path")
        
        # Malformed JSON strings
        malformed_cases = [
            '{"query": "test", "limit":}',  # Missing value
            '{"query": "test", "limit": 10,}',  # Trailing comma
            '{"query": "test" "limit": 10}',  # Missing comma
            '{query: "test", limit: 10}',  # Unquoted keys
            'not json at all',  # Not JSON
            '{"query": "test", "limit": "not_a_number"}'  # Invalid type
        ]
        
        results = []
        
        try:
            for malformed_json in malformed_cases[:3]:  # Test first 3 to avoid too much detail
                output_path = [("search", malformed_json)]
                agent_output = {"json_path": output_path}
                result = objective.eval(agent_output)
                
                # Should handle malformed JSON gracefully
                if hasattr(result, '__class__') and ('Error' in str(type(result)) or isinstance(result, BoolEvalResult) and not result.result):
                    results.append(f"Malformed JSON handled: ✓")
                else:
                    return TestResult(
                        name="Path Equality - Malformed JSON Strings",
                        status=TestStatus.FAIL,
                        message=f"✗ Malformed JSON was not handled properly: {malformed_json[:30]}...",
                        details=f"Result: {type(result).__name__}",
                        expected="Error or False result",
                        actual=type(result).__name__
                    )
            
            return TestResult(
                name="Path Equality - Malformed JSON Strings",
                status=TestStatus.PASS,
                message="✓ All malformed JSON strings handled correctly",
                details=f"Tested {len(malformed_cases[:3])} malformed cases | All handled appropriately",
                expected="Error handling for malformed JSON",
                actual="All cases handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Malformed JSON Strings",
                status=TestStatus.FAIL,
                message=f"✗ Malformed JSON test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Error handling for malformed JSON",
                actual=f"Exception: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_very_long_paths(self) -> TestResult:
        """Test PathEqualityObjective with very long path sequences."""
        # Create a long valid path (10 steps)
        long_valid_path = []
        for i in range(10):
            if i % 2 == 0:
                long_valid_path.append((f"search_{i}", SearchModel))
            else:
                long_valid_path.append((f"filter_{i}", FilterModel))
        
        valid_paths = [long_valid_path]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="long_path")
        
        # Create matching long output path
        long_output_path = []
        for i in range(10):
            if i % 2 == 0:
                long_output_path.append((f"search_{i}", {"query": f"query_{i}", "limit": i + 1}))
            else:
                long_output_path.append((f"filter_{i}", {"field": f"field_{i}", "value": f"value_{i}"}))
        
        agent_output = {"long_path": long_output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Long path should validate successfully")
            
            return TestResult(
                name="Path Equality - Very Long Paths",
                status=TestStatus.PASS,
                message="✓ Very long path (10 steps) validated successfully",
                details=f"Path length: 10 steps | All steps matched | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Very Long Paths",
                status=TestStatus.FAIL,
                message=f"✗ Long path test failed: {str(e)}",
                details=f"Path length: 10 | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_path_equality_unicode_and_special_characters(self) -> TestResult:
        """Test PathEqualityObjective with Unicode and special characters."""
        valid_paths = [
            [("search", SearchModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PathEqualityObjective(goal=valid_paths, output_key="unicode_path")
        
        # Path with Unicode and special characters
        output_path = [
            ("search", {"query": "Müller & Co. 中文测试 🔍", "limit": 5}),
            ("analyze", {"data": "résultats spéciaux", "method": "méthode_avancée"})
        ]
        agent_output = {"unicode_path": output_path}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Unicode and special characters should be handled correctly")
            
            return TestResult(
                name="Path Equality - Unicode and Special Characters",
                status=TestStatus.PASS,
                message="✓ Unicode and special characters handled correctly",
                details=f"Contains: German umlauts, Chinese characters, emojis, accents | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Path Equality - Unicode and Special Characters",
                status=TestStatus.FAIL,
                message=f"✗ Unicode handling test failed: {str(e)}",
                details=f"Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_advanced_similarity_scenarios(self) -> TestResult:
        """Test PartialPathEqualityObjective with advanced similarity calculation scenarios."""
        valid_paths = [
            [("search", SearchModel), ("filter", FilterModel), ("analyze", AnalyzeModel)]
        ]
        
        objective = PartialPathEqualityObjective(goal=valid_paths, output_key="advanced_similarity")
        
        # Test multiple scenarios with different similarity expectations
        test_scenarios = [
            {
                "name": "Perfect match",
                "path": [
                    ("search", {"query": "test", "limit": 10}),
                    ("filter", {"field": "name", "value": "test"}),
                    ("analyze", {"data": "results", "method": "default"})
                ],
                "expected_range": (0.95, 1.0)
            },
            {
                "name": "Tool names match, some invalid args",
                "path": [
                    ("search", {"query": "test", "limit": "invalid"}),  # Invalid limit type
                    ("filter", {"field": "name", "value": "test"}),     # Valid
                    ("analyze", {"data": "results"})                    # Missing method (has default)
                ],
                "expected_range": (0.5, 0.9)
            },
            {
                "name": "Mixed tools correct and wrong",
                "path": [
                    ("search", {"query": "test", "limit": 10}),         # Perfect
                    ("wrong_filter", {"field": "name", "value": "test"}),  # Wrong tool
                    ("analyze", {"data": "results"})                    # Valid
                ],
                "expected_range": (0.3, 0.7)
            }
        ]
        
        results = []
        
        try:
            for scenario in test_scenarios:
                agent_output = {"advanced_similarity": scenario["path"]}
                result = objective.eval(agent_output)
                
                self.runner.assert_isinstance(result, FloatEvalResult, f"Should return FloatEvalResult for {scenario['name']}")
                
                min_expected, max_expected = scenario["expected_range"]
                actual_score = result.result
                
                if min_expected <= actual_score <= max_expected:
                    results.append(f"{scenario['name']}: ✓ ({actual_score:.2f})")
                else:
                    return TestResult(
                        name="Partial Path Equality - Advanced Similarity Scenarios",
                        status=TestStatus.FAIL,
                        message=f"✗ {scenario['name']} score {actual_score:.2f} not in expected range [{min_expected}, {max_expected}]",
                        details=f"Scenario: {scenario['name']} | Expected: {min_expected}-{max_expected} | Actual: {actual_score:.2f}",
                        expected=f"{min_expected}-{max_expected}",
                        actual=f"{actual_score:.2f}"
                    )
            
            return TestResult(
                name="Partial Path Equality - Advanced Similarity Scenarios",
                status=TestStatus.PASS,
                message="✓ All similarity scenarios scored within expected ranges",
                details=f"Tested scenarios: {', '.join(results)}",
                expected="Similarity scores within expected ranges",
                actual="All scenarios scored correctly"
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Advanced Similarity Scenarios",
                status=TestStatus.FAIL,
                message=f"✗ Advanced similarity test failed: {str(e)}",
                details=f"Completed scenarios: {results} | Error: {str(e)}",
                expected="Similarity scores within expected ranges",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_performance_optimization(self) -> TestResult:
        """Test PartialPathEqualityObjective performance with optimization scenarios."""
        import time
        
        # Create a scenario with many valid paths (worst case for performance)
        many_valid_paths = []
        for path_idx in range(10):  # 10 different valid paths
            path = []
            for step in range(8):  # 8 steps each
                if step % 2 == 0:
                    path.append((f"search_{path_idx}_{step}", SearchModel))
                else:
                    path.append((f"filter_{path_idx}_{step}", FilterModel))
            many_valid_paths.append(path)
        
        objective = PartialPathEqualityObjective(goal=many_valid_paths, output_key="perf_path")
        
        # Create an output that partially matches multiple paths (complex similarity calculation)
        mixed_output_path = []
        for step in range(8):
            if step % 2 == 0:
                # Some steps match path 0, some match path 5
                path_idx = 0 if step < 4 else 5
                mixed_output_path.append((f"search_{path_idx}_{step}", {"query": f"query_{step}", "limit": step + 1}))
            else:
                # Mix of valid and invalid tools
                if step < 4:
                    mixed_output_path.append((f"filter_0_{step}", {"field": f"field_{step}", "value": f"value_{step}"}))
                else:
                    mixed_output_path.append((f"wrong_filter_{step}", {"field": "wrong", "value": "wrong"}))
        
        agent_output = {"perf_path": mixed_output_path}
        
        start_time = time.time()
        result = objective.eval(agent_output)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # Should get some reasonable similarity score
            assert 0.0 <= result.result <= 1.0, f"Similarity score should be between 0.0 and 1.0, got {result.result}"
            
            # Performance check (should handle 10 paths × 8 steps efficiently)
            if execution_time > 1.5:  # More than 1.5 seconds is concerning
                return TestResult(
                    name="Partial Path Equality - Performance Optimization",
                    status=TestStatus.FAIL,
                    message=f"✗ Performance test took too long: {execution_time:.2f}s",
                    details=f"Valid paths: 10 | Path length: 8 steps | Execution time: {execution_time:.2f}s",
                    expected="Fast execution < 1.5s",
                    actual=f"Slow execution: {execution_time:.2f}s"
                )
            
            return TestResult(
                name="Partial Path Equality - Performance Optimization",
                status=TestStatus.PASS,
                message=f"✓ Performance test completed efficiently in {execution_time:.3f}s",
                details=f"Valid paths: 10 | Path length: 8 steps | Score: {result.result:.3f} | Time: {execution_time:.3f}s",
                expected="Efficient similarity calculation",
                actual=f"Efficient execution in {execution_time:.3f}s"
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Performance Optimization",
                status=TestStatus.FAIL,
                message=f"✗ Performance optimization test failed: {str(e)}",
                details=f"Error: {str(e)} | Execution time: {execution_time:.3f}s",
                expected="Efficient similarity calculation",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_partial_path_equality_edge_case_robustness(self) -> TestResult:
        """Test PartialPathEqualityObjective robustness with edge cases."""
        test_results = []
        
        try:
            # Test case 1: Empty valid path with non-empty output
            objective1 = PartialPathEqualityObjective(goal=[[]], output_key="test_key")
            result1 = objective1.eval({"test_key": [("search", {"query": "test"})]})
            self.runner.assert_isinstance(result1, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result1.result, 0.0, "Non-empty output vs empty valid should be 0.0")
            test_results.append("Non-empty vs empty valid → 0.0")
            
            # Test case 2: Very short path vs very long valid path
            short_vs_long_objective = PartialPathEqualityObjective(
                goal=[[(f"tool_{i}", None) for i in range(15)]], 
                output_key="test_key"
            )
            short_output = [("tool_0", {})]  # Only 1 step vs 15
            result2 = short_vs_long_objective.eval({"test_key": short_output})
            self.runner.assert_isinstance(result2, FloatEvalResult, "Should return FloatEvalResult")
            # Should get some credit for first tool match, but heavily penalized for length
            assert 0.0 <= result2.result < 0.2, f"Short vs long should have low score, got {result2.result}"
            test_results.append(f"Short vs long path → {result2.result:.3f}")
            
            # Test case 3: All None schemas (no validation required)
            none_schema_objective = PartialPathEqualityObjective(
                goal=[[("tool1", None), ("tool2", None), ("tool3", None)]], 
                output_key="test_key"
            )
            none_output = [("tool1", {"any": "args"}), ("tool2", {"more": "args"}), ("tool3", {"final": "args"})]
            result3 = none_schema_objective.eval({"test_key": none_output})
            self.runner.assert_isinstance(result3, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result3.result, 1.0, "All None schemas with matching tools should be 1.0")
            test_results.append("All None schemas → 1.0")
            
            # Test case 4: Mixed valid and None schemas
            mixed_schema_objective = PartialPathEqualityObjective(
                goal=[[("search", SearchModel), ("tool2", None), ("filter", FilterModel)]], 
                output_key="test_key"
            )
            mixed_output = [
                ("search", {"query": "test", "limit": 10}),    # Valid
                ("tool2", {"any": "args", "work": True}),      # None schema - always valid
                ("filter", {"field": "name", "value": "test"}) # Valid
            ]
            result4 = mixed_schema_objective.eval({"test_key": mixed_output})
            self.runner.assert_isinstance(result4, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result4.result, 1.0, "Mixed schemas with all valid should be 1.0")
            test_results.append("Mixed schemas all valid → 1.0")
            
            return TestResult(
                name="Partial Path Equality - Edge Case Robustness",
                status=TestStatus.PASS,
                message="✓ All edge cases handled robustly: " + " | ".join(test_results),
                details=f"Tested {len(test_results)} edge cases: {', '.join(test_results)}",
                expected="Robust edge case handling",
                actual="All edge cases handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Partial Path Equality - Edge Case Robustness",
                status=TestStatus.FAIL,
                message=f"✗ Edge case robustness test failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Robust edge case handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_async_partial_path_equality_basic(self) -> TestResult:
        """Test basic async functionality of PartialPathEqualityObjective."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)]
            ]
            objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            # Perfect match with valid path
            output_path = [
                ("search", {"query": "async test", "limit": 10}),
                ("analyze", {"data": "async results"})
            ]
            agent_output = {"test_path": output_path}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
                self.runner.assert_equal(result.result, 1.0, "Perfect match should return 1.0")
                
                return TestResult(
                    name="Async Partial Path Equality - Basic",
                    status=TestStatus.PASS,
                    message="✓ Async partial path evaluation successful",
                    details=f"Perfect match | Score: {result.result}",
                    expected=1.0,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Partial Path Equality - Basic",
                    status=TestStatus.FAIL,
                    message=f"✗ Async partial path evaluation failed: {str(e)}",
                    details=f"Perfect match test | Result type: {type(result).__name__}",
                    expected=1.0,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_partial_path_equality_partial_match(self) -> TestResult:
        """Test async functionality with partial path similarity scoring."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)]
            ]
            objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            # Partial match - correct tools but some invalid args
            output_path = [
                ("search", {"query": "async test", "limit": "invalid_limit"}),  # Invalid limit type
                ("analyze", {"data": "async results"})  # Valid
            ]
            agent_output = {"test_path": output_path}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
                # Should be between 0.0 and 1.0, but less than 1.0 due to validation error
                assert 0.0 < result.result < 1.0, f"Partial match should be between 0.0 and 1.0, got {result.result}"
                
                return TestResult(
                    name="Async Partial Path Equality - Partial Match",
                    status=TestStatus.PASS,
                    message="✓ Async partial match calculated correct similarity score",
                    details=f"Tool names match, some args invalid | Score: {result.result:.2f}",
                    expected="0.0 < score < 1.0",
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Partial Path Equality - Partial Match",
                    status=TestStatus.FAIL,
                    message=f"✗ Async partial match test failed: {str(e)}",
                    details=f"Partial match test | Result type: {type(result).__name__}",
                    expected="0.0 < score < 1.0",
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_partial_path_consistency(self) -> TestResult:
        """Test that async and sync partial path evaluations produce identical results."""
        async def async_test():
            valid_paths = [
                [("search", SearchModel), ("analyze", AnalyzeModel)],
                [("filter", FilterModel), ("search", SearchModel), ("analyze", AnalyzeModel)]
            ]
            objective = PartialPathEqualityObjective(goal=valid_paths, output_key="test_path")
            
            test_cases = [
                # (output_path, description)
                ([("search", {"query": "test", "limit": 10}), ("analyze", {"data": "results"})], "perfect match"),
                ([("search", {"query": "test", "limit": "invalid"}), ("analyze", {"data": "results"})], "partial match"),
                ([("wrong_tool", {"any": "args"}), ("analyze", {"data": "results"})], "wrong tool name"),
                ([("filter", {"field": "name", "value": "test"}), ("search", {"query": "test"}), ("analyze", {"data": "results"})], "longer path match"),
            ]
            
            results = []
            
            try:
                for output_path, description in test_cases:
                    agent_output = {"test_path": output_path}
                    
                    # Run sync evaluation
                    sync_result = objective.eval(agent_output)
                    
                    # Run async evaluation
                    async_result = await objective.eval_async(agent_output)
                    
                    # Compare results
                    sync_type = type(sync_result).__name__
                    async_type = type(async_result).__name__
                    sync_value = getattr(sync_result, 'result', None)
                    async_value = getattr(async_result, 'result', None)
                    
                    # Check that both have same type and value
                    if sync_type != async_type:
                        raise AssertionError(f"Type mismatch for {description}: sync={sync_type}, async={async_type}")
                    
                    if sync_value is not None and async_value is not None:
                        # For float results, check with small tolerance
                        if isinstance(sync_value, float) and isinstance(async_value, float):
                            if abs(sync_value - async_value) >= 0.001:
                                raise AssertionError(f"Value mismatch for {description}: sync={sync_value}, async={async_value}, diff={abs(sync_value - async_value)}")
                        else:
                            if sync_value != async_value:
                                raise AssertionError(f"Value mismatch for {description}: sync={sync_value}, async={async_value}")
                    
                    formatted_value = f"{sync_value:.3f}" if isinstance(sync_value, float) else str(sync_value)
                    results.append(f"{description}: {sync_type}({formatted_value})")
                
                return TestResult(
                    name="Async vs Sync Partial Path Consistency",
                    status=TestStatus.PASS,
                    message="✓ Async and sync partial path evaluations produce identical results",
                    details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                    expected="Identical async/sync partial path results",
                    actual="All partial results match"
                )
            except Exception as e:
                return TestResult(
                    name="Async vs Sync Partial Path Consistency",
                    status=TestStatus.FAIL,
                    message=f"✗ Async/sync partial path consistency test failed: {str(e)}",
                    details=f"Completed tests: {results} | Error: {str(e)}",
                    expected="Identical async/sync partial path results",
                    actual=f"Error: {str(e)}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)


def main():
    """Main test execution function."""
    runner = TestRunner()
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]PathBenchmarkObjective Test Suite", style="cyan")
        runner.console.print("\n[bold]Testing PathEqualityObjective and PartialPathEqualityObjective with Multiple Valid Paths[/bold]\n")
    else:
        print("="*60)
        print("PathBenchmarkObjective Test Suite")
        print("="*60)
        print("Testing PathEqualityObjective and PartialPathEqualityObjective with Multiple Valid Paths\n")
    
    # Initialize test suites
    path_tests = PathBenchmarkObjectiveTests(runner)
    partial_path_tests = PartialPathBenchmarkObjectiveTests(runner)
    
    # Define test methods to run
    test_methods = [
        # PathEqualityObjective tests
        ("Path Equality - Single Valid Path Match", path_tests.test_path_equality_single_valid_path_match),
        ("Path Equality - Multiple Paths Match First", path_tests.test_path_equality_multiple_valid_paths_match_first),
        ("Path Equality - Multiple Paths Match Second", path_tests.test_path_equality_multiple_valid_paths_match_second),
        ("Path Equality - No Valid Path Matches", path_tests.test_path_equality_no_valid_path_matches),
        ("Path Equality - Wrong Tool Name", path_tests.test_path_equality_wrong_tool_name),
        ("Path Equality - Invalid Args", path_tests.test_path_equality_invalid_args),
        ("Path Equality - Length Mismatch", path_tests.test_path_equality_length_mismatch),
        ("Path Equality - None Schema", path_tests.test_path_equality_none_schema),

        ("Path Equality - Missing Output Key", path_tests.test_path_equality_missing_output_key),
        ("Path Equality - Empty Agent Output", path_tests.test_path_equality_empty_agent_output),
        ("Path Equality - None Agent Output", path_tests.test_path_equality_none_agent_output),
        
        # PathEqualityObjective async tests
        ("Async Path Equality - Basic", path_tests.test_async_path_equality_basic),
        ("Async Path Equality - Validation Failure", path_tests.test_async_path_equality_validation_failure),
        ("Async Path Equality - JSON Formatting", path_tests.test_async_path_equality_json_formatting),
        ("Async vs Sync Path Consistency", path_tests.test_async_vs_sync_path_consistency),
        
        # PartialPathEqualityObjective tests  
        ("Partial Path Equality - Perfect Match", partial_path_tests.test_partial_path_equality_perfect_match),
        ("Partial Path Equality - Partial Match", partial_path_tests.test_partial_path_equality_partial_match),
        ("Partial Path Equality - Wrong Tools", partial_path_tests.test_partial_path_equality_wrong_tools),
        ("Partial Path Equality - Length Mismatch", partial_path_tests.test_partial_path_equality_length_mismatch),
        ("Partial Path Equality - Multiple Paths Best Match", partial_path_tests.test_partial_path_equality_multiple_valid_paths_best_match),
        ("Partial Path Equality - Empty Paths", partial_path_tests.test_partial_path_equality_empty_paths),
        ("Partial Path Equality - None Schema", partial_path_tests.test_partial_path_equality_none_schema),
        ("Partial Path Equality - Invalid Output Format", partial_path_tests.test_partial_path_equality_invalid_output_format),
        ("Partial Path Equality - Valid Result Type", partial_path_tests.test_partial_path_equality_valid_result_type),
        ("Partial Path Equality - Advanced Similarity Scenarios", partial_path_tests.test_partial_path_equality_advanced_similarity_scenarios),
        ("Partial Path Equality - Performance Optimization", partial_path_tests.test_partial_path_equality_performance_optimization),
        ("Partial Path Equality - Edge Case Robustness", partial_path_tests.test_partial_path_equality_edge_case_robustness),
        
        # PartialPathEqualityObjective async tests
        ("Async Partial Path Equality - Basic", partial_path_tests.test_async_partial_path_equality_basic),
        ("Async Partial Path Equality - Partial Match", partial_path_tests.test_async_partial_path_equality_partial_match),
        ("Async vs Sync Partial Path Consistency", partial_path_tests.test_async_vs_sync_partial_path_consistency),
    ]
    
    # Run tests with progress indication
    if runner.console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=runner.console,
        ) as progress:
            task = progress.add_task("Running tests...", total=len(test_methods))
            
            for test_name, test_method in test_methods:
                progress.update(task, description=f"Running: {test_name}")
                result = runner.run_test(test_name, test_method)
                progress.advance(task)
                
                # Show immediate feedback
                status_style = "green" if result.status == TestStatus.PASS else "red"
                runner.console.print(f"  {result.status.value} {test_name}", style=status_style)
    else:
        print("Running tests...\n")
        for test_name, test_method in test_methods:
            print(f"Running: {test_name}")
            result = runner.run_test(test_name, test_method)
            print(f"  {result.status.value} {test_name}")
    
    # Display final results
    runner.display_results()
    
    # Exit with appropriate code
    exit_code = 0 if runner.passed_tests == runner.total_tests else 1
    if runner.console:
        runner.console.print(f"\n[bold]Exiting with code: {exit_code}[/bold]")
    else:
        print(f"\nExiting with code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
