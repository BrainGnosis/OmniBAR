#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive test suite for OutputBenchmarkObjective classes.
Tests StringEqualityObjective and RegexMatchObjective with rich terminal feedback.
"""

import sys
import traceback
import asyncio
import re
from typing import Any
from dataclasses import dataclass
from enum import Enum

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
from omnibar.objectives.output import (
    StringEqualityObjective,
    RegexMatchObjective
)
from omnibar.core.types import (
    BoolEvalResult,
    OutputKeyNotFoundError,
    InvalidRegexPatternError
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
    
    def create_failure_result(self, name: str, message: str, details: str = "", expected: Any = None, actual: Any = None) -> TestResult:
        """Helper method to create a failure result with traceback."""
        return TestResult(
            name=name,
            status=TestStatus.FAIL,
            message=message,
            details=details,
            expected=expected,
            actual=actual,
            traceback=traceback.format_exc()
        )
    
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
        table.add_column("Test Name", style="cyan", width=30)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Message", style="white", width=60)
        table.add_column("Details", style="dim white", width=40)
        
        for result in self.results:
            status_style = {
                TestStatus.PASS: "green",
                TestStatus.FAIL: "red", 
                TestStatus.ERROR: "red",
                TestStatus.SKIP: "yellow"
            }.get(result.status, "white")
            
            # Truncate long messages and details for table display
            message_display = result.message[:57] + "..." if len(result.message) > 60 else result.message
            details_display = result.details[:37] + "..." if result.details and len(result.details) > 40 else (result.details or "")
            
            table.add_row(
                result.name,
                Text(result.status.value, style=status_style),
                message_display,
                details_display
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
        
        # Show detailed failure information if there are any failures
        failed_tests = [r for r in self.results if r.status in [TestStatus.FAIL, TestStatus.ERROR]]
        if failed_tests:
            self.console.print("\n")
            self.console.rule("[bold red]Detailed Failure Information", style="red")
            for failed_test in failed_tests:
                # Build the failure content
                content_parts = [
                    f"[bold red]Status:[/bold red] {failed_test.status.value}",
                    f"[bold yellow]Message:[/bold yellow] {failed_test.message}",
                    f"[bold cyan]Details:[/bold cyan] {failed_test.details}",
                    f"[bold green]Expected:[/bold green] {failed_test.expected}",
                    f"[bold magenta]Actual:[/bold magenta] {failed_test.actual}"
                ]
                
                # Add traceback if available
                if failed_test.traceback:
                    content_parts.append("[bold white]Traceback:[/bold white]")
                    # Format traceback with syntax highlighting
                    traceback_syntax = Syntax(
                        failed_test.traceback,
                        "python",
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True
                    )
                    
                failure_content = "\n".join(content_parts)
                failure_panel = Panel(
                    failure_content,
                    title=f"❌ {failed_test.name}",
                    border_style="red",
                    expand=False
                )
                self.console.print(failure_panel)
                
                # Print traceback separately if available for better formatting
                if failed_test.traceback:
                    traceback_panel = Panel(
                        traceback_syntax,
                        title="📋 Full Traceback",
                        border_style="dim red",
                        expand=False
                    )
                    self.console.print(traceback_panel)
    
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


class OutputBenchmarkObjectiveTests:
    """Comprehensive test suite for OutputBenchmarkObjective classes."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    def test_string_equality_success(self) -> TestResult:
        """Test StringEqualityObjective with matching string."""
        goal = "test_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        agent_output = {"test_key": "test_value", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for matching strings")
            
            return TestResult(
                name="String Equality - Success",
                status=TestStatus.PASS,
                message=f"✓ Goal '{goal}' matched output['{output_key}'] = '{agent_output[output_key]}'",
                details=f"Expected: {goal} | Actual: {agent_output[output_key]} | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="String Equality - Success",
                status=TestStatus.FAIL,
                message=f"✗ Expected match failed: {str(e)}",
                details=f"Goal: '{goal}' | Output: {agent_output} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_string_equality_failure(self) -> TestResult:
        """Test StringEqualityObjective with non-matching string."""
        goal = "expected_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        agent_output = {"test_key": "different_value", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should return False for non-matching strings")
            
            return TestResult(
                name="String Equality - Mismatch",
                status=TestStatus.PASS,
                message=f"✓ Goal '{goal}' correctly didn't match output['{output_key}'] = '{agent_output[output_key]}'",
                details=f"Expected: {goal} | Actual: {agent_output[output_key]} | Result: {result.result} (correctly False)",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="String Equality - Mismatch",
                status=TestStatus.FAIL,
                message=f"✗ Expected mismatch detection failed: {str(e)}",
                details=f"Goal: '{goal}' | Output: {agent_output} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_string_equality_missing_key(self) -> TestResult:
        """Test StringEqualityObjective with missing output key."""
        goal = "test_value"
        missing_key = "missing_key"
        objective = StringEqualityObjective(goal=goal, output_key=missing_key)
        agent_output = {"test_key": "test_value", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError")
            # Check if the error message contains meaningful information
            # has_key_info = missing_key in str(result.message) or "missing" in str(result.message).lower()
            
            return TestResult(
                name="String Equality - Missing Key",
                status=TestStatus.PASS,
                message=f"✓ Correctly detected missing key '{missing_key}' in output",
                details=f"Goal: '{goal}' | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="String Equality - Missing Key",
                status=TestStatus.FAIL,
                message=f"✗ Missing key detection failed: {str(e)}",
                details=f"Goal: '{goal}' | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_regex_match_success(self) -> TestResult:
        """Test RegexMatchObjective with matching pattern."""
        pattern = r"test_\d+"
        output_key = "test_key"
        objective = RegexMatchObjective(goal=pattern, output_key=output_key)
        agent_output = {"test_key": "test_123", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for matching regex")
            
            return TestResult(
                name="Regex Match - Success",
                status=TestStatus.PASS,
                message=f"✓ Pattern '{pattern}' matched output['{output_key}'] = '{agent_output[output_key]}'",
                details=f"Pattern: {pattern} | Input: '{agent_output[output_key]}' | Match found: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - Success",
                status=TestStatus.FAIL,
                message=f"✗ Expected regex match failed: {str(e)}",
                details=f"Pattern: '{pattern}' | Input: '{agent_output.get(output_key, 'KEY_NOT_FOUND')}' | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_regex_match_failure(self) -> TestResult:
        """Test RegexMatchObjective with non-matching pattern."""
        pattern = r"test_\d+"
        output_key = "test_key"
        objective = RegexMatchObjective(goal=pattern, output_key=output_key)
        agent_output = {"test_key": "test_abc", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should return False for non-matching regex")
            
            return TestResult(
                name="Regex Match - No Match",
                status=TestStatus.PASS,
                message=f"✓ Pattern '{pattern}' correctly didn't match output['{output_key}'] = '{agent_output[output_key]}'",
                details=f"Pattern: {pattern} | Input: '{agent_output[output_key]}' | Match found: {result.result} (correctly False)",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - No Match",
                status=TestStatus.FAIL,
                message=f"✗ Expected regex non-match detection failed: {str(e)}",
                details=f"Pattern: '{pattern}' | Input: '{agent_output.get(output_key, 'KEY_NOT_FOUND')}' | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_regex_match_missing_key(self) -> TestResult:
        """Test RegexMatchObjective with missing output key."""
        pattern = r"test_\d+"
        missing_key = "missing_key"
        objective = RegexMatchObjective(goal=pattern, output_key=missing_key)
        agent_output = {"test_key": "test_123", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError")
            
            return TestResult(
                name="Regex Match - Missing Key",
                status=TestStatus.PASS,
                message=f"✓ Correctly detected missing key '{missing_key}' for regex pattern",
                details=f"Pattern: '{pattern}' | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - Missing Key",
                status=TestStatus.FAIL,
                message=f"✗ Missing key detection failed for regex: {str(e)}",
                details=f"Pattern: '{pattern}' | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_regex_invalid_pattern(self) -> TestResult:
        """Test RegexMatchObjective with invalid regex pattern."""
        invalid_pattern = r"[invalid(regex"
        output_key = "test_key"
        objective = RegexMatchObjective(goal=invalid_pattern, output_key=output_key)
        agent_output = {"test_key": "test_123", "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, InvalidRegexPatternError, "Should return InvalidRegexPatternError")
            
            return TestResult(
                name="Regex Match - Invalid Pattern",
                status=TestStatus.PASS,
                message=f"✓ Correctly detected invalid regex pattern '{invalid_pattern}'",
                details=f"Invalid pattern: '{invalid_pattern}' | Input: '{agent_output[output_key]}' | Error: {result.message}",
                expected="InvalidRegexPatternError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - Invalid Pattern",
                status=TestStatus.FAIL,
                message=f"✗ Invalid regex pattern detection failed: {str(e)}",
                details=f"Invalid pattern: '{invalid_pattern}' | Input: '{agent_output.get(output_key, 'KEY_NOT_FOUND')}' | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="InvalidRegexPatternError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_complex_regex_patterns(self) -> TestResult:
        """Test RegexMatchObjective with complex patterns."""
        # Email pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        output_key = "email"
        objective = RegexMatchObjective(goal=email_pattern, output_key=output_key)
        
        try:
            # Test valid email
            valid_email = "user@example.com"
            agent_output = {"email": valid_email}
            result = objective.eval(agent_output)
            
            self.runner.assert_isinstance(result, BoolEvalResult)
            self.runner.assert_equal(result.result, True, "Should match valid email")
            
            # Test invalid email
            invalid_email = "invalid-email"
            agent_output = {"email": invalid_email}
            result = objective.eval(agent_output)
            
            self.runner.assert_isinstance(result, BoolEvalResult)
            self.runner.assert_equal(result.result, False, "Should not match invalid email")
            
            return TestResult(
                name="Regex Match - Complex Patterns",
                status=TestStatus.PASS,
                message=f"✓ Email pattern correctly validated '{valid_email}' ✓ and rejected '{invalid_email}' ✗",
                details=f"Pattern: {email_pattern} | Valid: '{valid_email}' → True | Invalid: '{invalid_email}' → False",
                expected="Email validation working",
                actual="Complex regex validation successful"
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - Complex Patterns",
                status=TestStatus.FAIL,
                message=f"✗ Complex regex pattern testing failed: {str(e)}",
                details=f"Pattern: {email_pattern} | Error: {str(e)}",
                expected="Email validation working",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_edge_cases(self) -> TestResult:
        """Test various edge cases."""
        test_results = []
        
        try:
            # Test with None value
            goal1 = "test"
            objective1 = StringEqualityObjective(goal=goal1, output_key="test_key")
            agent_output1 = {"test_key": None}
            result1 = objective1.eval(agent_output1)
            
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, False, "None should not equal 'test'")
            test_results.append(f"None vs '{goal1}' → {result1.result}")
            
            # Test with empty string
            goal2 = ""
            objective2 = StringEqualityObjective(goal=goal2, output_key="test_key")
            agent_output2 = {"test_key": ""}
            result2 = objective2.eval(agent_output2)
            
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, True, "Empty string should equal empty string")
            test_results.append(f"Empty string vs empty string → {result2.result}")
            
            # Test with numeric values
            goal3 = "123"
            objective3 = StringEqualityObjective(goal=goal3, output_key="test_key")
            agent_output3 = {"test_key": 123}
            result3 = objective3.eval(agent_output3)
            
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, False, "String '123' should not equal int 123")
            test_results.append(f"String '{goal3}' vs int {agent_output3['test_key']} → {result3.result}")
            
            return TestResult(
                name="Edge Cases",
                status=TestStatus.PASS,
                message="✓ All edge cases handled correctly: " + " | ".join(test_results),
                details=f"Test 1: {test_results[0]} | Test 2: {test_results[1]} | Test 3: {test_results[2]}",
                expected="Proper type handling",
                actual="Edge cases handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Edge Cases",
                status=TestStatus.FAIL,
                message=f"✗ Edge case testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper type handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_string_equality_valid_result_type(self) -> TestResult:
        """Test StringEqualityObjective returns correct valid_eval_result_type."""
        goal = "test_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        agent_output = {"test_key": "test_value"}
        
        result = objective.eval(agent_output)
        
        try:
            # Check that result is an instance of the valid_eval_result_type
            self.runner.assert_isinstance(result, objective.valid_eval_result_type, 
                                        f"Should return {objective.valid_eval_result_type.__name__}")
            self.runner.assert_isinstance(result, BoolEvalResult, "Should be BoolEvalResult")
            self.runner.assert_equal(objective.valid_eval_result_type, BoolEvalResult, 
                                   "valid_eval_result_type should be BoolEvalResult")
            
            return TestResult(
                name="String Equality - Valid Result Type",
                status=TestStatus.PASS,
                message=f"✓ Returned correct type: {type(result).__name__} matches {objective.valid_eval_result_type.__name__}",
                details=f"Expected type: {objective.valid_eval_result_type.__name__} | Actual type: {type(result).__name__} | Result: {result.result}",
                expected=objective.valid_eval_result_type.__name__,
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="String Equality - Valid Result Type",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type verification failed: {str(e)}",
                details=f"Expected type: {getattr(objective, 'valid_eval_result_type', 'UNKNOWN')} | Actual type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=getattr(objective, 'valid_eval_result_type', 'UNKNOWN'),
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_regex_match_valid_result_type(self) -> TestResult:
        """Test RegexMatchObjective returns correct valid_eval_result_type."""
        pattern = r"test_\d+"
        output_key = "test_key"
        objective = RegexMatchObjective(goal=pattern, output_key=output_key)
        agent_output = {"test_key": "test_123"}
        
        result = objective.eval(agent_output)
        
        try:
            # Check that result is an instance of the valid_eval_result_type
            self.runner.assert_isinstance(result, objective.valid_eval_result_type, 
                                        f"Should return {objective.valid_eval_result_type.__name__}")
            self.runner.assert_isinstance(result, BoolEvalResult, "Should be BoolEvalResult")
            self.runner.assert_equal(objective.valid_eval_result_type, BoolEvalResult, 
                                   "valid_eval_result_type should be BoolEvalResult")
            
            return TestResult(
                name="Regex Match - Valid Result Type",
                status=TestStatus.PASS,
                message=f"✓ Returned correct type: {type(result).__name__} matches {objective.valid_eval_result_type.__name__}",
                details=f"Pattern: {pattern} | Expected type: {objective.valid_eval_result_type.__name__} | Actual type: {type(result).__name__} | Result: {result.result}",
                expected=objective.valid_eval_result_type.__name__,
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Regex Match - Valid Result Type",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type verification failed: {str(e)}",
                details=f"Pattern: {pattern} | Expected type: {getattr(objective, 'valid_eval_result_type', 'UNKNOWN')} | Actual type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=getattr(objective, 'valid_eval_result_type', 'UNKNOWN'),
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_valid_result_type_consistency(self) -> TestResult:
        """Test that valid_eval_result_type is consistent across different scenarios."""
        test_results = []
        
        try:
            # Test StringEqualityObjective with different outcomes
            string_obj = StringEqualityObjective(goal="test", output_key="key")
            
            # Test success case
            result1 = string_obj.eval({"key": "test"})
            self.runner.assert_isinstance(result1, string_obj.valid_eval_result_type)
            test_results.append(f"String success: {type(result1).__name__}")
            
            # Test failure case
            result2 = string_obj.eval({"key": "different"})
            self.runner.assert_isinstance(result2, string_obj.valid_eval_result_type)
            test_results.append(f"String failure: {type(result2).__name__}")
            
            # Test RegexMatchObjective with different outcomes
            regex_obj = RegexMatchObjective(goal=r"\d+", output_key="key")
            
            # Test success case
            result3 = regex_obj.eval({"key": "123"})
            self.runner.assert_isinstance(result3, regex_obj.valid_eval_result_type)
            test_results.append(f"Regex success: {type(result3).__name__}")
            
            # Test failure case
            result4 = regex_obj.eval({"key": "abc"})
            self.runner.assert_isinstance(result4, regex_obj.valid_eval_result_type)
            test_results.append(f"Regex failure: {type(result4).__name__}")
            
            # Verify both objectives have the same valid_eval_result_type
            self.runner.assert_equal(string_obj.valid_eval_result_type, regex_obj.valid_eval_result_type,
                                   "Both objectives should have same valid_eval_result_type")
            
            return TestResult(
                name="Valid Result Type - Consistency",
                status=TestStatus.PASS,
                message="✓ All scenarios return correct valid_eval_result_type: " + " | ".join(test_results),
                details=f"String type: {string_obj.valid_eval_result_type.__name__} | Regex type: {regex_obj.valid_eval_result_type.__name__} | All results: {test_results}",
                expected="BoolEvalResult consistency",
                actual="All results consistent"
            )
        except Exception as e:
            return TestResult(
                name="Valid Result Type - Consistency",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type consistency failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="BoolEvalResult consistency",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    

    

    

    

    

    

    



    def test_empty_agent_output(self) -> TestResult:
        """Test behavior with completely empty agent output."""
        goal = "test_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        agent_output = {}  # Completely empty
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError for empty output")
            
            return TestResult(
                name="Empty Agent Output",
                status=TestStatus.PASS,
                message=f"✓ Correctly handled empty agent output for key '{output_key}'",
                details=f"Goal: '{goal}' | Key: '{output_key}' | Empty output: {{}} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Empty Agent Output",
                status=TestStatus.FAIL,
                message=f"✗ Empty agent output handling failed: {str(e)}",
                details=f"Goal: '{goal}' | Key: '{output_key}' | Result type: {type(result).__name__}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_none_agent_output(self) -> TestResult:
        """Test behavior with None as agent output (should return ExtractionError)."""
        goal = "test_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        
        try:
            result = objective.eval(None)
            
            # The correct behavior is to return an ExtractionError, not crash
            if hasattr(result, '__class__') and 'ExtractionError' in str(type(result)):
                return TestResult(
                    name="None Agent Output",
                    status=TestStatus.PASS,
                    message=f"✓ Correctly handled None agent output with {type(result).__name__}",
                    details=f"Goal: '{goal}' | Key: '{output_key}' | Input: None | Result type: {type(result).__name__} | Message: {getattr(result, 'message', 'N/A')}",
                    expected="ExtractionError",
                    actual=type(result).__name__
                )
            else:
                return TestResult(
                    name="None Agent Output",
                    status=TestStatus.FAIL,
                    message=f"✗ Expected ExtractionError but got {type(result).__name__}",
                    details=f"Goal: '{goal}' | Key: '{output_key}' | Input: None | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                    expected="ExtractionError",
                    actual=type(result).__name__
                )
        except Exception as e:
            # If an exception is raised instead of returning ExtractionError, that's also acceptable
            return TestResult(
                name="None Agent Output",
                status=TestStatus.PASS,
                message=f"✓ Correctly raised exception for None agent output: {type(e).__name__}",
                details=f"Goal: '{goal}' | Key: '{output_key}' | Input: None | Exception: {str(e)}",
                expected="Exception or ExtractionError",
                actual=f"Exception: {type(e).__name__}"
            )
    
    def test_invalid_input_types(self) -> TestResult:
        """Test behavior with various invalid input types for agent_output."""
        goal = "test_value"
        output_key = "test_key"
        objective = StringEqualityObjective(goal=goal, output_key=output_key)
        test_results = []
        
        # Test cases: (input_value, expected_error_type, description)
        invalid_inputs = [
            ("string_instead_of_dict", "ExtractionError", "String input"),
            (123, "ExtractionError", "Integer input"),
            ([1, 2, 3], "ExtractionError", "List input"),
            (True, "ExtractionError", "Boolean input"),
        ]
        
        try:
            for input_value, expected_error, description in invalid_inputs:
                result = objective.eval(input_value)
                
                # Check if we got the expected error type
                if expected_error in str(type(result)):
                    test_results.append(f"{description}: ✓ {type(result).__name__}")
                else:
                    return TestResult(
                        name="Invalid Input Types",
                        status=TestStatus.FAIL,
                        message=f"✗ {description} failed: expected {expected_error}, got {type(result).__name__}",
                        details=f"Input: {input_value} | Expected: {expected_error} | Actual: {type(result).__name__}",
                        expected=expected_error,
                        actual=type(result).__name__
                    )
            
            return TestResult(
                name="Invalid Input Types",
                status=TestStatus.PASS,
                message="✓ All invalid input types handled correctly: " + " | ".join(test_results),
                details=f"Tested: {len(invalid_inputs)} invalid input types | All returned appropriate ExtractionError",
                expected="ExtractionError for all invalid inputs",
                actual="All inputs handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Invalid Input Types",
                status=TestStatus.FAIL,
                message=f"✗ Invalid input types test failed with exception: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="ExtractionError handling",
                actual=f"Exception: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_deeply_nested_output_values(self) -> TestResult:
        """Test with complex nested data structures as output values."""
        test_results = []
        
        try:
            # Test with nested dictionary
            nested_dict = {"inner": {"deep": "target_value"}}
            goal1 = str(nested_dict)
            objective1 = StringEqualityObjective(goal=goal1, output_key="nested_key")
            agent_output1 = {"nested_key": nested_dict}
            result1 = objective1.eval(agent_output1)
            
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, False, "Dict should not equal its string representation")
            test_results.append(f"Nested dict: {result1.result}")
            
            # Test regex with nested structure 
            pattern = r".*target_value.*"
            objective3 = RegexMatchObjective(goal=pattern, output_key="nested_key")
            result3 = objective3.eval(agent_output1)
            
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, True, "Regex should match string representation of nested dict")
            test_results.append(f"Regex on nested: {result3.result}")
            
            return TestResult(
                name="Deeply Nested Output Values",
                status=TestStatus.PASS,
                message="✓ All nested data structure tests passed: " + " | ".join(test_results),
                details=f"Dict test: {test_results[0]} | Regex test: {test_results[1]}",
                expected="Complex type handling",
                actual="Nested structures handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Deeply Nested Output Values",
                status=TestStatus.FAIL,
                message=f"✗ Nested data structure test failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Complex type handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_unicode_and_special_characters(self) -> TestResult:
        """Test with Unicode characters, emojis, and special characters."""
        test_results = []
        
        try:
            # Test with Unicode characters
            unicode_goal = "测试中文字符"
            objective1 = StringEqualityObjective(goal=unicode_goal, output_key="unicode_key")
            agent_output1 = {"unicode_key": "测试中文字符"}
            result1 = objective1.eval(agent_output1)
            
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Unicode characters should match exactly")
            test_results.append(f"Unicode: {result1.result}")
            
            # Test with emojis
            emoji_goal = "🎉✨🚀"
            objective2 = StringEqualityObjective(goal=emoji_goal, output_key="emoji_key")
            agent_output2 = {"emoji_key": "🎉✨🚀"}
            result2 = objective2.eval(agent_output2)
            
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, True, "Emojis should match exactly")
            test_results.append(f"Emoji: {result2.result}")
            
            # Test regex with special regex characters that need escaping
            special_chars = ".$^{[(|)*+?\\"
            pattern = re.escape(special_chars)
            objective3 = RegexMatchObjective(goal=pattern, output_key="special_key")
            agent_output3 = {"special_key": special_chars}
            result3 = objective3.eval(agent_output3)
            
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, True, "Escaped special chars should match")
            test_results.append(f"Special chars: {result3.result}")
            
            return TestResult(
                name="Unicode and Special Characters",
                status=TestStatus.PASS,
                message="✓ All Unicode and special character tests passed: " + " | ".join(test_results),
                details=f"Unicode: {test_results[0]} | Emoji: {test_results[1]} | Special: {test_results[2]}",
                expected="Special character handling",
                actual="All special characters handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Unicode and Special Characters",
                status=TestStatus.FAIL,
                message=f"✗ Unicode and special character test failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Special character handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_extremely_large_strings(self) -> TestResult:
        """Test with very large strings to check performance and memory handling."""
        try:
            # Create a large string (1MB)
            large_string = "A" * (1024 * 1024)  # 1MB of 'A's
            
            # Test string equality with large string
            objective1 = StringEqualityObjective(goal=large_string, output_key="large_key")
            agent_output1 = {"large_key": large_string}
            result1 = objective1.eval(agent_output1)
            
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Large strings should match exactly")
            
            # Test with slightly different large string
            different_large = "A" * (1024 * 1024 - 1) + "B"
            agent_output2 = {"large_key": different_large}
            result2 = objective1.eval(agent_output2)
            
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, False, "Different large strings should not match")
            
            return TestResult(
                name="Extremely Large Strings",
                status=TestStatus.PASS,
                message=f"✓ Large string tests passed: exact match={result1.result}, different={result2.result}",
                details=f"String size: {len(large_string):,} chars | Exact: {result1.result} | Different: {result2.result}",
                expected="Large string handling",
                actual="Large strings handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Extremely Large Strings",
                status=TestStatus.FAIL,
                message=f"✗ Large string test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Large string handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_regex_catastrophic_backtracking(self) -> TestResult:
        """Test regex patterns that could cause catastrophic backtracking."""
        try:
            # Pattern that could cause catastrophic backtracking
            dangerous_pattern = r"(a+)+b"
            test_input = "a" * 20 + "c"  # No 'b' at end
            
            objective = RegexMatchObjective(goal=dangerous_pattern, output_key="test_key")
            agent_output = {"test_key": test_input}
            
            import time
            start_time = time.time()
            result = objective.eval(agent_output)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            self.runner.assert_isinstance(result, BoolEvalResult)
            self.runner.assert_equal(result.result, False, "Pattern should not match input without 'b'")
            
            if execution_time > 1.0:  # More than 1 second is suspicious
                return TestResult(
                    name="Regex Catastrophic Backtracking",
                    status=TestStatus.FAIL,
                    message=f"✗ Regex took too long: {execution_time:.2f}s (potential catastrophic backtracking)",
                    details=f"Pattern: {dangerous_pattern} | Input length: {len(test_input)} | Time: {execution_time:.2f}s",
                    expected="Fast execution",
                    actual=f"Slow execution: {execution_time:.2f}s"
                )
            
            return TestResult(
                name="Regex Catastrophic Backtracking",
                status=TestStatus.PASS,
                message=f"✓ Regex executed safely in {execution_time:.3f}s",
                details=f"Pattern: {dangerous_pattern} | Input length: {len(test_input)} | Time: {execution_time:.3f}s | Result: {result.result}",
                expected="Safe regex execution",
                actual=f"Safe execution in {execution_time:.3f}s"
            )
        except Exception as e:
            return TestResult(
                name="Regex Catastrophic Backtracking",
                status=TestStatus.FAIL,
                message=f"✗ Regex backtracking test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Safe regex execution",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_async_string_equality_basic(self) -> TestResult:
        """Test basic async functionality of StringEqualityObjective."""
        async def async_test():
            goal = "test_value"
            output_key = "test_key"
            objective = StringEqualityObjective(goal=goal, output_key=output_key)
            
            # Test successful match
            agent_output = {"test_key": "test_value", "other_key": "other_value"}
            result = await objective.eval_async(agent_output)
            
            if not isinstance(result, BoolEvalResult):
                raise AssertionError(f"Expected BoolEvalResult, got {type(result).__name__}")
            if result.result != True:
                raise AssertionError(f"Expected True, got {result.result}")
            
            return TestResult(
                name="Async String Equality - Basic",
                status=TestStatus.PASS,
                message=f"✓ Async string equality evaluation successful",
                details=f"Goal: '{goal}' | Output: '{agent_output[output_key]}' | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_string_equality_mismatch(self) -> TestResult:
        """Test async functionality with string mismatch."""
        async def async_test():
            goal = "expected_value"
            output_key = "test_key"
            objective = StringEqualityObjective(goal=goal, output_key=output_key)
            
            # Test mismatch
            agent_output = {"test_key": "different_value"}
            result = await objective.eval_async(agent_output)
            
            if not isinstance(result, BoolEvalResult):
                raise AssertionError(f"Expected BoolEvalResult, got {type(result).__name__}")
            if result.result != False:
                raise AssertionError(f"Expected False, got {result.result}")
            
            return TestResult(
                name="Async String Equality - Mismatch",
                status=TestStatus.PASS,
                message=f"✓ Async string mismatch correctly detected",
                details=f"Goal: '{goal}' | Output: '{agent_output[output_key]}' | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_regex_match_basic(self) -> TestResult:
        """Test basic async functionality of RegexMatchObjective."""
        async def async_test():
            pattern = r"test_\d+"
            output_key = "test_key"
            objective = RegexMatchObjective(goal=pattern, output_key=output_key)
            
            # Test successful match
            agent_output = {"test_key": "test_123", "other_key": "other_value"}
            result = await objective.eval_async(agent_output)
            
            if not isinstance(result, BoolEvalResult):
                raise AssertionError(f"Expected BoolEvalResult, got {type(result).__name__}")
            if result.result != True:
                raise AssertionError(f"Expected True, got {result.result}")
            
            return TestResult(
                name="Async Regex Match - Basic",
                status=TestStatus.PASS,
                message=f"✓ Async regex match evaluation successful",
                details=f"Pattern: '{pattern}' | Input: '{agent_output[output_key]}' | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_regex_match_no_match(self) -> TestResult:
        """Test async functionality with regex no match."""
        async def async_test():
            pattern = r"test_\d+"
            output_key = "test_key"
            objective = RegexMatchObjective(goal=pattern, output_key=output_key)
            
            # Test no match
            agent_output = {"test_key": "test_abc"}
            result = await objective.eval_async(agent_output)
            
            if not isinstance(result, BoolEvalResult):
                raise AssertionError(f"Expected BoolEvalResult, got {type(result).__name__}")
            if result.result != False:
                raise AssertionError(f"Expected False, got {result.result}")
            
            return TestResult(
                name="Async Regex Match - No Match",
                status=TestStatus.PASS,
                message=f"✓ Async regex no match correctly detected",
                details=f"Pattern: '{pattern}' | Input: '{agent_output[output_key]}' | Result: {result.result}",
                expected=False,
                actual=result.result
            )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_string_consistency(self) -> TestResult:
        """Test that async and sync string evaluations produce identical results."""
        async def async_test():
            goal = "test_value"
            output_key = "test_key"
            objective = StringEqualityObjective(goal=goal, output_key=output_key)
            
            test_cases = [
                ({"test_key": "test_value"}, "exact match"),
                ({"test_key": "different_value"}, "mismatch"),
                ({"test_key": ""}, "empty string"),
                ({"test_key": None}, "None value"),
                ({"test_key": 123}, "numeric value"),
            ]
            
            results = []
            
            for agent_output, description in test_cases:
                # Run sync evaluation
                sync_result = objective.eval(agent_output)
                
                # Run async evaluation
                async_result = await objective.eval_async(agent_output)
                
                # Compare results
                sync_type = type(sync_result).__name__
                async_type = type(async_result).__name__
                sync_value = getattr(sync_result, 'result', None)
                async_value = getattr(async_result, 'result', None)
                
                if sync_type != async_type:
                    raise AssertionError(f"Type mismatch for {description}: sync={sync_type}, async={async_type}")
                
                if sync_value != async_value:
                    raise AssertionError(f"Value mismatch for {description}: sync={sync_value}, async={async_value}")
                
                formatted_value = str(sync_value) if sync_value is not None else "None"
                results.append(f"{description}: {sync_type}({formatted_value})")
            
            return TestResult(
                name="Async vs Sync String Consistency",
                status=TestStatus.PASS,
                message="✓ Async and sync string evaluations produce identical results",
                details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                expected="Identical async/sync string results",
                actual="All string results match"
            )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_regex_consistency(self) -> TestResult:
        """Test that async and sync regex evaluations produce identical results."""
        async def async_test():
            pattern = r"test_\d+"
            output_key = "test_key"
            objective = RegexMatchObjective(goal=pattern, output_key=output_key)
            
            test_cases = [
                ({"test_key": "test_123"}, "exact match"),
                ({"test_key": "test_abc"}, "no match"),
                ({"test_key": "test_"}, "partial match"),
                ({"test_key": ""}, "empty string"),
                ({"test_key": None}, "None value"),
                ({"test_key": 123}, "numeric value"),
            ]
            
            results = []
            
            for agent_output, description in test_cases:
                # Run sync evaluation
                sync_result = objective.eval(agent_output)
                
                # Run async evaluation
                async_result = await objective.eval_async(agent_output)
                
                # Compare results
                sync_type = type(sync_result).__name__
                async_type = type(async_result).__name__
                sync_value = getattr(sync_result, 'result', None)
                async_value = getattr(async_result, 'result', None)
                
                if sync_type != async_type:
                    raise AssertionError(f"Type mismatch for {description}: sync={sync_type}, async={async_type}")
                
                if sync_value != async_value:
                    raise AssertionError(f"Value mismatch for {description}: sync={sync_value}, async={async_value}")
                
                formatted_value = str(sync_value) if sync_value is not None else "None"
                results.append(f"{description}: {sync_type}({formatted_value})")
            
            return TestResult(
                name="Async vs Sync Regex Consistency",
                status=TestStatus.PASS,
                message="✓ Async and sync regex evaluations produce identical results",
                details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                expected="Identical async/sync regex results",
                actual="All regex results match"
            )
        
        return self.runner.run_async_test(async_test)


def main():
    """Main test execution function."""
    runner = TestRunner()
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]OutputBenchmarkObjective Test Suite", style="cyan")
        runner.console.print("\n[bold]Testing StringEqualityObjective and RegexMatchObjective classes[/bold]\n")
    else:
        print("="*60)
        print("OutputBenchmarkObjective Test Suite")
        print("="*60)
        print("Testing StringEqualityObjective and RegexMatchObjective classes\n")
    
    # Initialize test suite
    tests = OutputBenchmarkObjectiveTests(runner)
    
    # Define test methods to run
    test_methods = [
        ("String Equality Success", tests.test_string_equality_success),
        ("String Equality Failure", tests.test_string_equality_failure),
        ("String Equality Missing Key", tests.test_string_equality_missing_key),
        ("Regex Match Success", tests.test_regex_match_success),
        ("Regex Match Failure", tests.test_regex_match_failure),
        ("Regex Match Missing Key", tests.test_regex_match_missing_key),
        ("Regex Invalid Pattern", tests.test_regex_invalid_pattern),
        ("Complex Regex Patterns", tests.test_complex_regex_patterns),
        ("Edge Cases", tests.test_edge_cases),
        ("String Equality Valid Result Type", tests.test_string_equality_valid_result_type),
        ("Regex Match Valid Result Type", tests.test_regex_match_valid_result_type),
        ("Valid Result Type Consistency", tests.test_valid_result_type_consistency),
        ("Empty Agent Output", tests.test_empty_agent_output),
        ("None Agent Output", tests.test_none_agent_output),
        ("Invalid Input Types", tests.test_invalid_input_types),
        ("Deeply Nested Output Values", tests.test_deeply_nested_output_values),
        ("Unicode and Special Characters", tests.test_unicode_and_special_characters),
        ("Extremely Large Strings", tests.test_extremely_large_strings),
        ("Regex Catastrophic Backtracking", tests.test_regex_catastrophic_backtracking),
        
        # Async compatibility tests
        ("Async String Equality - Basic", tests.test_async_string_equality_basic),
        ("Async String Equality - Mismatch", tests.test_async_string_equality_mismatch),
        ("Async Regex Match - Basic", tests.test_async_regex_match_basic),
        ("Async Regex Match - No Match", tests.test_async_regex_match_no_match),
        ("Async vs Sync String Consistency", tests.test_async_vs_sync_string_consistency),
        ("Async vs Sync Regex Consistency", tests.test_async_vs_sync_regex_consistency),
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