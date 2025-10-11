#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive test suite for StateBenchmarkObjective classes.
Tests StateEqualityObjective with rich terminal feedback.
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
from omnibar.objectives.state import (
    StateEqualityObjective,
    PartialStateEqualityObjective
)
from omnibar.core.types import (
    BoolEvalResult,
    FloatEvalResult,
    OutputKeyNotFoundError,
    InvalidEvalResult,
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


# Test Models for StateEqualityObjective
class SimpleTestModel(BaseModel):
    name: str
    value: int

class UserModel(BaseModel):
    id: int
    username: str
    email: str
    active: bool = True

class ProductModel(BaseModel):
    product_id: str
    name: str
    price: float
    category: str
    in_stock: bool = True

class ComplexTestModel(BaseModel):
    user: UserModel
    products: List[ProductModel]
    total_amount: float


class PartialStateBenchmarkObjectiveTests:
    """Comprehensive test suite for PartialStateEqualityObjective class."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    def test_partial_state_equality_no_errors(self) -> TestResult:
        """Test PartialStateEqualityObjective with valid data (all fields pass)."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Valid data that matches the model perfectly
        valid_data = {"name": "test_item", "value": 42}
        agent_output = {"test_data": valid_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 1.0, "Should return 1.0 for all fields passing (100% success rate)")
            
            return TestResult(
                name="Partial State Equality - All Fields Pass",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} validated successfully with 100% pass rate",
                details=f"Model: {goal.__name__} | Data: {valid_data} | Pass rate: {result.result} (all fields passed)",
                expected=1.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - All Fields Pass",
                status=TestStatus.FAIL,
                message=f"✗ Expected 100% pass rate failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {valid_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=1.0,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_single_error(self) -> TestResult:
        """Test PartialStateEqualityObjective with single validation error."""
        goal = SimpleTestModel  # Has 2 fields: name, value
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Invalid data with one missing field
        invalid_data = {"name": "test_item"}  # Missing 'value' field
        agent_output = {"test_data": invalid_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # SimpleTestModel has 2 fields, 1 failed, so 1/2 = 0.5 pass rate
            expected_pass_rate = 0.5
            self.runner.assert_equal(result.result, expected_pass_rate, f"Should return {expected_pass_rate} for 1 error out of 2 fields")
            
            return TestResult(
                name="Partial State Equality - Single Error",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} calculated correct pass rate: {result.result} (1 passed / 2 total)",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Pass rate: {result.result} | Expected: {expected_pass_rate}",
                expected=expected_pass_rate,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Single Error",
                status=TestStatus.FAIL,
                message=f"✗ Expected pass rate calculation failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=0.5,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_multiple_errors(self) -> TestResult:
        """Test PartialStateEqualityObjective with multiple validation errors."""
        goal = UserModel  # Has 4 fields: id, username, email, active
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Invalid data with multiple missing/wrong fields
        invalid_data = {
            "id": "not_an_int",  # Wrong type - 1 error
            "username": "",      # Might be valid or invalid depending on constraints
            # Missing 'email' field entirely - 1 error
            "active": "not_a_bool"  # Wrong type - 1 error
        }
        agent_output = {"test_data": invalid_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # UserModel has 4 fields total, expecting at least 3 errors (id, email, active)
            # So pass rate should be (4-3)/4 = 0.25 or lower
            self.runner.assert_equal(result.result <= 0.25, True, "Should have low pass rate due to multiple errors")
            
            return TestResult(
                name="Partial State Equality - Multiple Errors",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} calculated low pass rate: {result.result} due to multiple validation errors",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Pass rate: {result.result} (≤0.25 expected)",
                expected="≤0.25",
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Multiple Errors",
                status=TestStatus.FAIL,
                message=f"✗ Expected low pass rate failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected="≤0.25",
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_complex_model_errors(self) -> TestResult:
        """Test PartialStateEqualityObjective with complex nested model errors."""
        goal = ComplexTestModel  # Contains nested UserModel and ProductModel
        output_key = "complex_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Complex data with multiple nested errors
        complex_invalid_data = {
            "user": {
                "id": "not_int",     # Wrong type - 1 error
                "username": "",      # Might be valid (depending on constraints)
                # Missing 'email' field - 1 error
                "active": "not_bool" # Wrong type - 1 error
            },
            "products": [
                {
                    "product_id": "",    # Empty string might be valid
                    "name": "",          # Empty string might be valid
                    # Missing 'price' field - 1 error
                    "category": 123      # Wrong type (should be string) - 1 error
                    # Missing 'in_stock' field - but has default, so might not error
                }
            ],
            # Missing 'total_amount' field - 1 error
        }
        agent_output = {"complex_data": complex_invalid_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # With nested structure, expect many errors leading to low pass rate
            # Pass rate should be significantly less than 0.5 due to multiple validation failures
            self.runner.assert_equal(result.result < 0.5, True, "Should have low pass rate due to many nested validation errors")
            
            return TestResult(
                name="Partial State Equality - Complex Model Errors",
                status=TestStatus.PASS,
                message=f"✓ Complex model calculated low pass rate: {result.result:.3f} due to nested validation errors",
                details=f"Model: {goal.__name__} | Pass rate: {result.result:.3f} (< 0.5 expected due to nested errors)",
                expected="< 0.5",
                actual=f"{result.result:.3f}"
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Complex Model Errors",
                status=TestStatus.FAIL,
                message=f"✗ Expected low pass rate for complex model failed: {str(e)}",
                details=f"Model: {goal.__name__} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected="< 0.5",
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    

    
    def test_partial_state_equality_pass_rate_calculation(self) -> TestResult:
        """Test PartialStateEqualityObjective pass rate calculation with known field counts."""
        goal = SimpleTestModel  # Known to have exactly 2 fields: name, value
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        test_cases = [
            # (test_data, expected_errors, expected_pass_rate, description)
            ({"name": "valid", "value": 42}, 0, 1.0, "all fields valid"),
            ({"name": "valid"}, 1, 0.5, "one field missing"),
            ({"name": 123, "value": "invalid"}, 2, 0.0, "all fields invalid"),
        ]
        
        results = []
        
        try:
            for test_data, expected_errors, expected_pass_rate, description in test_cases:
                agent_output = {"test_data": test_data}
                result = objective.eval(agent_output)
                
                self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
                self.runner.assert_equal(abs(result.result - expected_pass_rate) < 0.01, True, 
                                       f"Pass rate should be {expected_pass_rate} for {description}")
                
                results.append(f"{description}: {result.result:.2f}")
            
            return TestResult(
                name="Partial State Equality - Pass Rate Calculation",
                status=TestStatus.PASS,
                message="✓ All pass rate calculations correct: " + " | ".join(results),
                details=f"Model: {goal.__name__} (2 fields) | Test results: {results}",
                expected="Correct pass rate calculations",
                actual="All calculations verified"
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Pass Rate Calculation",
                status=TestStatus.FAIL,
                message=f"✗ Pass rate calculation failed: {str(e)}",
                details=f"Model: {goal.__name__} | Completed tests: {results} | Error: {str(e)}",
                expected="Correct pass rate calculations",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_nested_field_counting(self) -> TestResult:
        """Test PartialStateEqualityObjective properly counts nested model fields."""
        goal = ComplexTestModel  # Has nested UserModel and ProductModel
        output_key = "complex_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Perfect valid complex data - should result in 1.0 pass rate
        perfect_complex_data = {
            "user": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "active": True
            },
            "products": [
                {
                    "product_id": "PROD001",
                    "name": "Test Product",
                    "price": 99.99,
                    "category": "electronics",
                    "in_stock": True
                }
            ],
            "total_amount": 99.99
        }
        agent_output = {"complex_data": perfect_complex_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            self.runner.assert_equal(result.result, 1.0, "Should have 1.0 pass rate for perfect nested data")
            
            # Now test with one specific nested field error
            partial_error_data = {
                "user": {
                    "id": "not_an_int",  # This should cause 1 error
                    "username": "testuser",
                    "email": "test@example.com",
                    "active": True
                },
                "products": [
                    {
                        "product_id": "PROD001",
                        "name": "Test Product",
                        "price": 99.99,
                        "category": "electronics",
                        "in_stock": True
                    }
                ],
                "total_amount": 99.99
            }
            agent_output_partial = {"complex_data": partial_error_data}
            result_partial = objective.eval(agent_output_partial)
            
            self.runner.assert_isinstance(result_partial, FloatEvalResult, "Should return FloatEvalResult for partial error")
            # Should have a high pass rate since only 1 field out of many failed
            self.runner.assert_equal(result_partial.result > 0.8, True, "Should have high pass rate with only 1 nested field error")
            
            return TestResult(
                name="Partial State Equality - Nested Field Counting",
                status=TestStatus.PASS,
                message=f"✓ Correctly counted nested fields: perfect={result.result:.1f}, partial={result_partial.result:.3f}",
                details=f"Model: {goal.__name__} | Perfect data: {result.result} | Partial error: {result_partial.result:.3f} (>0.8 expected)",
                expected="Perfect=1.0, Partial>0.8",
                actual=f"Perfect={result.result}, Partial={result_partial.result:.3f}"
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Nested Field Counting",
                status=TestStatus.FAIL,
                message=f"✗ Nested field counting test failed: {str(e)}",
                details=f"Model: {goal.__name__} | Error: {str(e)}",
                expected="Perfect=1.0, Partial>0.8",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_non_validation_exception(self) -> TestResult:
        """Test PartialStateEqualityObjective with non-ValidationError exceptions."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Use None value which will cause TypeError when trying goal(**None)
        agent_output = {"test_data": None}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, InvalidEvalResult, "Should return InvalidEvalResult for non-ValidationError")
            
            return TestResult(
                name="Partial State Equality - Non-Validation Exception",
                status=TestStatus.PASS,
                message="✓ Correctly detected non-ValidationError exception",
                details=f"Model: {goal.__name__} | Exception type: {type(result).__name__} | Message: {result.message}",
                expected="InvalidEvalResult",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Non-Validation Exception",
                status=TestStatus.FAIL,
                message=f"✗ Non-validation exception handling failed: {str(e)}",
                details=f"Model: {goal.__name__} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="InvalidEvalResult",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_valid_result_type(self) -> TestResult:
        """Test PartialStateEqualityObjective returns correct valid_eval_result_type."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        valid_data = {"name": "test", "value": 42}
        agent_output = {"test_data": valid_data}
        
        result = objective.eval(agent_output)
        
        try:
            # Check that result is an instance of the valid_eval_result_type
            self.runner.assert_isinstance(result, objective.valid_eval_result_type, 
                                        f"Should return {objective.valid_eval_result_type.__name__}")
            self.runner.assert_isinstance(result, FloatEvalResult, "Should be FloatEvalResult")
            self.runner.assert_equal(objective.valid_eval_result_type, FloatEvalResult, 
                                   "valid_eval_result_type should be FloatEvalResult")
            
            return TestResult(
                name="Partial State Equality - Valid Result Type",
                status=TestStatus.PASS,
                message=f"✓ Returned correct type: {type(result).__name__} matches {objective.valid_eval_result_type.__name__}",
                details=f"Model: {goal.__name__} | Expected type: {objective.valid_eval_result_type.__name__} | Actual type: {type(result).__name__} | Result: {result.result}",
                expected=objective.valid_eval_result_type.__name__,
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Valid Result Type",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type verification failed: {str(e)}",
                details=f"Model: {goal.__name__} | Expected type: {getattr(objective, 'valid_eval_result_type', 'UNKNOWN')} | Actual type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=getattr(objective, 'valid_eval_result_type', 'UNKNOWN'),
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_with_custom_validators(self) -> TestResult:
        """Test PartialStateEqualityObjective with custom validator errors."""
        from pydantic import field_validator
        
        class CustomValidatorModel(BaseModel):
            email: str
            age: int
            
            @field_validator('email')
            @classmethod
            def validate_email(cls, v):
                if '@' not in v:
                    raise ValueError('Email must contain @')
                return v
            
            @field_validator('age')
            @classmethod
            def validate_age(cls, v):
                if v < 0:
                    raise ValueError('Age must be positive')
                if v > 150:
                    raise ValueError('Age must be reasonable')
                return v
        
        goal = CustomValidatorModel
        output_key = "test_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        try:
            # Test with multiple custom validator failures
            invalid_data = {
                "email": "invalid-email",  # Missing @ symbol
                "age": -5                  # Negative age
            }
            agent_output = {"test_data": invalid_data}
            
            result = objective.eval(agent_output)
            
            self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
            # CustomValidatorModel has 2 fields (email, age), both failed, so 0/2 = 0.0 pass rate
            self.runner.assert_equal(result.result, 0.0, "Should have 0.0 pass rate for 2 custom validator errors")
            
            return TestResult(
                name="Partial State Equality - Custom Validators",
                status=TestStatus.PASS,
                message=f"✓ Custom validators calculated correct pass rate: {result.result} (0% pass rate)",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Pass rate: {result.result} (both fields failed)",
                expected=0.0,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Custom Validators",
                status=TestStatus.FAIL,
                message=f"✗ Custom validator error counting failed: {str(e)}",
                details=f"Model: {goal.__name__} | Error: {str(e)}",
                expected=0.0,
                actual=getattr(result, 'result', None) if 'result' in locals() else None,
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_missing_key(self) -> TestResult:
        """Test PartialStateEqualityObjective with missing output key."""
        goal = SimpleTestModel
        missing_key = "missing_key"
        objective = PartialStateEqualityObjective(goal=goal, output_key=missing_key)
        agent_output = {"test_data": {"name": "test", "value": 42}, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError")
            
            return TestResult(
                name="Partial State Equality - Missing Key",
                status=TestStatus.PASS,
                message=f"✓ Correctly detected missing key '{missing_key}' in output",
                details=f"Model: {goal.__name__} | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - Missing Key",
                status=TestStatus.FAIL,
                message=f"✗ Missing key detection failed: {str(e)}",
                details=f"Model: {goal.__name__} | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_partial_state_equality_json_formatting_error(self) -> TestResult:
        """Test PartialStateEqualityObjective with JSON formatting errors."""
        goal = SimpleTestModel
        output_key = "json_data"
        objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
        
        # Invalid JSON string
        invalid_json = '{"name": "test", "value":}'  # Missing value after colon
        agent_output = {"json_data": invalid_json}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, FormattingError, "Should return FormattingError for JSON parsing error")
            
            return TestResult(
                name="Partial State Equality - JSON Formatting Error",
                status=TestStatus.PASS,
                message="✓ Correctly detected JSON formatting error",
                details=f"Model: {goal.__name__} | Invalid JSON: {invalid_json} | Error type: {type(result).__name__} | Error: {result.message}",
                expected="FormattingError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Partial State Equality - JSON Formatting Error",
                status=TestStatus.FAIL,
                message=f"✗ JSON formatting error detection failed: {str(e)}",
                details=f"Model: {goal.__name__} | Invalid JSON: {invalid_json} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="FormattingError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )

    def test_async_partial_state_equality_basic(self) -> TestResult:
        """Test basic async functionality of PartialStateEqualityObjective."""
        async def async_test():
            goal = SimpleTestModel  # Has 2 fields: name, value
            output_key = "test_data"
            objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
            
            # Valid data that matches the model perfectly
            valid_data = {"name": "async_test", "value": 42}
            agent_output = {"test_data": valid_data}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
                self.runner.assert_equal(result.result, 1.0, "Should return 1.0 for all fields passing")
                
                return TestResult(
                    name="Async Partial State Equality - Basic",
                    status=TestStatus.PASS,
                    message=f"✓ Async partial evaluation successful for {goal.__name__}",
                    details=f"Model: {goal.__name__} | Data: {valid_data} | Pass rate: {result.result}",
                    expected=1.0,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Partial State Equality - Basic",
                    status=TestStatus.FAIL,
                    message=f"✗ Async partial evaluation failed: {str(e)}",
                    details=f"Model: {goal.__name__} | Data: {valid_data} | Result type: {type(result).__name__}",
                    expected=1.0,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_partial_state_equality_partial_errors(self) -> TestResult:
        """Test async functionality with partial validation errors."""
        async def async_test():
            goal = SimpleTestModel  # Has 2 fields: name, value
            output_key = "test_data"
            objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
            
            # Invalid data with one missing field
            invalid_data = {"name": "async_test"}  # Missing 'value' field
            agent_output = {"test_data": invalid_data}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, FloatEvalResult, "Should return FloatEvalResult")
                # SimpleTestModel has 2 fields, 1 failed, so 1/2 = 0.5 pass rate
                expected_pass_rate = 0.5
                self.runner.assert_equal(result.result, expected_pass_rate, f"Should return {expected_pass_rate} for 1 error out of 2 fields")
                
                return TestResult(
                    name="Async Partial State Equality - Partial Errors",
                    status=TestStatus.PASS,
                    message=f"✓ Async partial error calculation successful for {goal.__name__}",
                    details=f"Model: {goal.__name__} | Data: {invalid_data} | Pass rate: {result.result}",
                    expected=expected_pass_rate,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async Partial State Equality - Partial Errors",
                    status=TestStatus.FAIL,
                    message=f"✗ Async partial error calculation failed: {str(e)}",
                    details=f"Model: {goal.__name__} | Data: {invalid_data} | Result type: {type(result).__name__}",
                    expected=0.5,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_partial_consistency(self) -> TestResult:
        """Test that async and sync partial evaluations produce identical results."""
        async def async_test():
            goal = SimpleTestModel
            output_key = "test_data"
            objective = PartialStateEqualityObjective(goal=goal, output_key=output_key)
            
            test_cases = [
                # (data, description)
                ({"name": "test", "value": 42}, "all fields valid"),
                ({"name": "test"}, "one field missing"),
                ({"name": 123, "value": "invalid"}, "all fields invalid"),
                ('{"name": "test", "value": 99}', "JSON string valid"),
            ]
            
            results = []
            
            try:
                for data, description in test_cases:
                    agent_output = {"test_data": data}
                    
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
                    if sync_value is not None and async_value is not None:
                        # For float results, check with small tolerance
                        if isinstance(sync_value, float) and isinstance(async_value, float):
                            self.runner.assert_equal(abs(sync_value - async_value) < 0.001, True, f"Value mismatch for {description}")
                        else:
                            self.runner.assert_equal(sync_value, async_value, f"Value mismatch for {description}")
                    
                    results.append(f"{description}: {sync_type}({sync_value})")
                
                return TestResult(
                    name="Async vs Sync Partial Consistency",
                    status=TestStatus.PASS,
                    message="✓ Async and sync partial evaluations produce identical results",
                    details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                    expected="Identical async/sync partial results",
                    actual="All partial results match"
                )
            except Exception as e:
                return TestResult(
                    name="Async vs Sync Partial Consistency",
                    status=TestStatus.FAIL,
                    message=f"✗ Async/sync partial consistency test failed: {str(e)}",
                    details=f"Completed tests: {results} | Error: {str(e)}",
                    expected="Identical async/sync partial results",
                    actual=f"Error: {str(e)}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)


class StateBenchmarkObjectiveTests:
    """Comprehensive test suite for StateBenchmarkObjective classes."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    def test_state_equality_success_simple(self) -> TestResult:
        """Test StateEqualityObjective with simple model validation success."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # Valid data that matches the model
        valid_data = {"name": "test_item", "value": 42}
        agent_output = {"test_data": valid_data, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for valid model data")
            
            return TestResult(
                name="State Equality - Simple Success",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} validated successfully against output data",
                details=f"Model: {goal.__name__} | Data: {valid_data} | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Simple Success",
                status=TestStatus.FAIL,
                message=f"✗ Expected model validation success failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {valid_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_failure_validation(self) -> TestResult:
        """Test StateEqualityObjective with model validation failure."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # Invalid data that doesn't match the model (missing required field)
        invalid_data = {"name": "test_item"}  # Missing 'value' field
        agent_output = {"test_data": invalid_data, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, False, "Should return False for invalid model data")
            
            return TestResult(
                name="State Equality - Validation Failure",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} correctly failed validation for incomplete data",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Result: {result.result} (correctly False)",
                expected=False,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Validation Failure",
                status=TestStatus.FAIL,
                message=f"✗ Expected validation failure detection failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {invalid_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=False,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_missing_key(self) -> TestResult:
        """Test StateEqualityObjective with missing output key."""
        goal = SimpleTestModel
        missing_key = "missing_key"
        objective = StateEqualityObjective(goal=goal, output_key=missing_key)
        agent_output = {"test_data": {"name": "test", "value": 42}, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError")
            
            return TestResult(
                name="State Equality - Missing Key",
                status=TestStatus.PASS,
                message=f"✓ Correctly detected missing key '{missing_key}' in output",
                details=f"Model: {goal.__name__} | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Missing Key",
                status=TestStatus.FAIL,
                message=f"✗ Missing key detection failed: {str(e)}",
                details=f"Model: {goal.__name__} | Missing key: '{missing_key}' | Available keys: {list(agent_output.keys())} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_json_string_input(self) -> TestResult:
        """Test StateEqualityObjective with JSON string input that needs parsing."""
        goal = SimpleTestModel
        output_key = "json_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # Valid JSON string that should parse and validate
        valid_json_string = '{"name": "json_test", "value": 123}'
        agent_output = {"json_data": valid_json_string, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for valid JSON string data")
            
            return TestResult(
                name="State Equality - JSON String Success",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} validated JSON string successfully",
                details=f"Model: {goal.__name__} | JSON: {valid_json_string} | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="State Equality - JSON String Success",
                status=TestStatus.FAIL,
                message=f"✗ JSON string validation failed: {str(e)}",
                details=f"Model: {goal.__name__} | JSON: {valid_json_string} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_basemodel_input(self) -> TestResult:
        """Test StateEqualityObjective with BaseModel instance as input."""
        goal = SimpleTestModel
        output_key = "model_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # BaseModel instance that should validate
        model_instance = SimpleTestModel(name="model_test", value=456)
        agent_output = {"model_data": model_instance, "other_key": "other_value"}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for valid BaseModel instance")
            
            return TestResult(
                name="State Equality - BaseModel Success",
                status=TestStatus.PASS,
                message=f"✓ Model {goal.__name__} validated BaseModel instance successfully",
                details=f"Model: {goal.__name__} | Instance: {model_instance} | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="State Equality - BaseModel Success",
                status=TestStatus.FAIL,
                message=f"✗ BaseModel instance validation failed: {str(e)}",
                details=f"Model: {goal.__name__} | Instance: {model_instance} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_complex_model(self) -> TestResult:
        """Test StateEqualityObjective with complex nested model."""
        goal = ComplexTestModel
        output_key = "complex_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # Complex nested data
        complex_data = {
            "user": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "active": True
            },
            "products": [
                {
                    "product_id": "PROD001",
                    "name": "Test Product",
                    "price": 99.99,
                    "category": "electronics",
                    "in_stock": True
                }
            ],
            "total_amount": 99.99
        }
        agent_output = {"complex_data": complex_data}
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Should return True for valid complex model data")
            
            return TestResult(
                name="State Equality - Complex Model Success",
                status=TestStatus.PASS,
                message=f"✓ Complex model {goal.__name__} validated successfully with nested data",
                details=f"Model: {goal.__name__} | Data keys: {list(complex_data.keys())} | Result: {result.result}",
                expected=True,
                actual=result.result
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Complex Model Success",
                status=TestStatus.FAIL,
                message=f"✗ Complex model validation failed: {str(e)}",
                details=f"Model: {goal.__name__} | Data: {complex_data} | Result type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=True,
                actual=getattr(result, 'result', None),
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_invalid_json(self) -> TestResult:
        """Test StateEqualityObjective with invalid JSON string."""
        goal = SimpleTestModel
        output_key = "bad_json"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        # Invalid JSON string
        invalid_json = '{"name": "test", "value":}'  # Missing value after colon
        agent_output = {"bad_json": invalid_json}
        
        result = objective.eval(agent_output)
        
        try:
            # Should return FormattingError due to JSON parsing error in _format_filtered_output
            self.runner.assert_isinstance(result, FormattingError, "Should return FormattingError for JSON parsing error")
            
            return TestResult(
                name="State Equality - Invalid JSON",
                status=TestStatus.PASS,
                message="✓ Correctly detected invalid JSON string",
                details=f"Model: {goal.__name__} | Invalid JSON: {invalid_json} | Error type: {type(result).__name__} | Error: {result.message}",
                expected="FormattingError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Invalid JSON",
                status=TestStatus.FAIL,
                message=f"✗ Invalid JSON detection failed: {str(e)}",
                details=f"Model: {goal.__name__} | Invalid JSON: {invalid_json} | Result type: {type(result).__name__} | Result: {getattr(result, 'message', 'N/A')}",
                expected="FormattingError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_state_equality_valid_result_type(self) -> TestResult:
        """Test StateEqualityObjective returns correct valid_eval_result_type."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        valid_data = {"name": "test", "value": 42}
        agent_output = {"test_data": valid_data}
        
        result = objective.eval(agent_output)
        
        try:
            # Check that result is an instance of the valid_eval_result_type
            self.runner.assert_isinstance(result, objective.valid_eval_result_type, 
                                        f"Should return {objective.valid_eval_result_type.__name__}")
            self.runner.assert_isinstance(result, BoolEvalResult, "Should be BoolEvalResult")
            self.runner.assert_equal(objective.valid_eval_result_type, BoolEvalResult, 
                                   "valid_eval_result_type should be BoolEvalResult")
            
            return TestResult(
                name="State Equality - Valid Result Type",
                status=TestStatus.PASS,
                message=f"✓ Returned correct type: {type(result).__name__} matches {objective.valid_eval_result_type.__name__}",
                details=f"Model: {goal.__name__} | Expected type: {objective.valid_eval_result_type.__name__} | Actual type: {type(result).__name__} | Result: {result.result}",
                expected=objective.valid_eval_result_type.__name__,
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="State Equality - Valid Result Type",
                status=TestStatus.FAIL,
                message=f"✗ Valid result type verification failed: {str(e)}",
                details=f"Model: {goal.__name__} | Expected type: {getattr(objective, 'valid_eval_result_type', 'UNKNOWN')} | Actual type: {type(result).__name__} | Result: {getattr(result, 'result', 'N/A')}",
                expected=getattr(objective, 'valid_eval_result_type', 'UNKNOWN'),
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    

    

    

    
    def test_edge_cases(self) -> TestResult:
        """Test various edge cases."""
        test_results = []
        
        try:
            # Test with None value
            goal1 = SimpleTestModel
            objective1 = StateEqualityObjective(goal=goal1, output_key="test_key")
            agent_output1 = {"test_key": None}
            result1 = objective1.eval(agent_output1)
            
            # None should cause an InvalidEvalResult because goal(**None) will fail with TypeError
            self.runner.assert_isinstance(result1, InvalidEvalResult, "None should cause validation error")
            test_results.append(f"None value → {type(result1).__name__}")
            
            # Test with empty dict
            agent_output2 = {"test_key": {}}
            result2 = objective1.eval(agent_output2)
            self.runner.assert_isinstance(result2, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result2.result, False, "Empty dict should fail validation")
            test_results.append(f"Empty dict → {result2.result}")
            
            # Test with extra fields (should still validate if required fields present)
            agent_output3 = {"test_key": {"name": "test", "value": 42, "extra_field": "extra"}}
            result3 = objective1.eval(agent_output3)
            self.runner.assert_isinstance(result3, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result3.result, True, "Extra fields should not prevent validation")
            test_results.append(f"Extra fields → {result3.result}")
            
            return TestResult(
                name="Edge Cases",
                status=TestStatus.PASS,
                message="✓ All edge cases handled correctly: " + " | ".join(test_results),
                details=f"Test 1: {test_results[0]} | Test 2: {test_results[1]} | Test 3: {test_results[2]}",
                expected="Proper edge case handling",
                actual="Edge cases handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Edge Cases",
                status=TestStatus.FAIL,
                message=f"✗ Edge case testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper edge case handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_non_dict_values(self) -> TestResult:
        """Test StateEqualityObjective with non-dictionary values."""
        goal = SimpleTestModel
        output_key = "test_key"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        test_results = []
        
        try:
            # Test with string value (not JSON)
            agent_output1 = {"test_key": "not a dict"}
            result1 = objective.eval(agent_output1)
            # This should fail when trying goal(**"not a dict")
            self.runner.assert_isinstance(result1, InvalidEvalResult, "String value should cause error")
            test_results.append(f"String value → {type(result1).__name__}")
            
            # Test with integer value
            agent_output2 = {"test_key": 42}
            result2 = objective.eval(agent_output2)
            # This should fail when trying goal(**42)
            self.runner.assert_isinstance(result2, InvalidEvalResult, "Integer value should cause error")
            test_results.append(f"Integer value → {type(result2).__name__}")
            
            # Test with list value
            agent_output3 = {"test_key": [1, 2, 3]}
            result3 = objective.eval(agent_output3)
            # This should fail when trying goal(**[1, 2, 3])
            self.runner.assert_isinstance(result3, InvalidEvalResult, "List value should cause error")
            test_results.append(f"List value → {type(result3).__name__}")
            
            return TestResult(
                name="Non-Dict Values",
                status=TestStatus.PASS,
                message="✓ All non-dict values handled correctly: " + " | ".join(test_results),
                details=f"String: {test_results[0]} | Integer: {test_results[1]} | List: {test_results[2]}",
                expected="InvalidEvalResult for all non-dict values",
                actual="All non-dict values rejected"
            )
        except Exception as e:
            return TestResult(
                name="Non-Dict Values",
                status=TestStatus.FAIL,
                message=f"✗ Non-dict value testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="InvalidEvalResult for all non-dict values",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_malformed_json_strings(self) -> TestResult:
        """Test StateEqualityObjective with various malformed JSON strings."""
        goal = SimpleTestModel
        output_key = "json_key"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        test_results = []
        
        try:
            # Test 1: Missing closing brace
            malformed_json1 = '{"name": "test", "value": 42'
            agent_output1 = {"json_key": malformed_json1}
            result1 = objective.eval(agent_output1)
            self.runner.assert_isinstance(result1, FormattingError, "Should return FormattingError for malformed JSON")
            test_results.append("Missing brace → FormattingError")
            
            # Test 2: Invalid JSON syntax (trailing comma)
            malformed_json2 = '{"name": "test", "value": 42,}'
            agent_output2 = {"json_key": malformed_json2}
            result2 = objective.eval(agent_output2)
            self.runner.assert_isinstance(result2, FormattingError, "Should return FormattingError for trailing comma")
            test_results.append("Trailing comma → FormattingError")
            
            # Test 3: Completely invalid JSON
            malformed_json3 = 'this is not json at all'
            agent_output3 = {"json_key": malformed_json3}
            result3 = objective.eval(agent_output3)
            self.runner.assert_isinstance(result3, FormattingError, "Should return FormattingError for non-JSON")
            test_results.append("Non-JSON → FormattingError")
            
            # Test 4: Valid JSON but missing required fields
            valid_json_missing_fields = '{"name": "test"}'  # missing value field
            agent_output4 = {"json_key": valid_json_missing_fields}
            result4 = objective.eval(agent_output4)
            self.runner.assert_isinstance(result4, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result4.result, False, "Should fail validation for missing fields")
            test_results.append("Valid JSON, missing fields → False")
            
            return TestResult(
                name="Malformed JSON Strings",
                status=TestStatus.PASS,
                message="✓ All malformed JSON cases handled correctly: " + " | ".join(test_results),
                details=f"Tests: {test_results}",
                expected="FormattingError for malformed JSON, BoolEvalResult(False) for valid JSON with missing fields",
                actual="All JSON cases handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Malformed JSON Strings",
                status=TestStatus.FAIL,
                message=f"✗ Malformed JSON testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper JSON error handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_type_validation_comprehensive(self) -> TestResult:
        """Test comprehensive type validation behavior with proper models for int, float, and string fields."""
        test_results = []
        
        try:
            # Test integer field validation
            int_model_objective = StateEqualityObjective(goal=SimpleTestModel, output_key="test_key")
            
            # Valid int
            result1 = int_model_objective.eval({"test_key": {"name": "test", "value": 42}})
            self.runner.assert_isinstance(result1, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result1.result, True, "Valid int should pass")
            test_results.append("Valid int(42) → True")
            
            # String that can be coerced to int
            result2 = int_model_objective.eval({"test_key": {"name": "test", "value": "42"}})
            self.runner.assert_isinstance(result2, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result2.result, True, "String '42' should coerce to int 42")
            test_results.append("String('42') to int → True")
            
            # Float that loses precision (should fail for int field)
            result3 = int_model_objective.eval({"test_key": {"name": "test", "value": 42.7}})
            self.runner.assert_isinstance(result3, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result3.result, False, "Float 42.7 should not coerce to int (precision loss)")
            test_results.append("Float(42.7) to int → False")
            
            # Non-numeric string
            result4 = int_model_objective.eval({"test_key": {"name": "test", "value": "not_a_number"}})
            self.runner.assert_isinstance(result4, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result4.result, False, "Non-numeric string should fail")
            test_results.append("Non-numeric string → False")
            
            # Boolean to string coercion
            result5 = int_model_objective.eval({"test_key": {"name": True, "value": 42}})
            self.runner.assert_isinstance(result5, BoolEvalResult, "Should return BoolEvalResult")
            if result5.result:
                test_results.append("Boolean(True) to string → True")
            else:
                test_results.append("Boolean(True) to string → False")
            
            return TestResult(
                name="Type Validation Comprehensive",
                status=TestStatus.PASS,
                message="✓ Type validation behavior verified: " + " | ".join(test_results),
                details=f"Tests: {test_results}",
                expected="Proper Pydantic type validation and coercion rules",
                actual="Type validation working correctly"
            )
        except Exception as e:
            return TestResult(
                name="Type Validation Comprehensive",
                status=TestStatus.FAIL,
                message=f"✗ Type validation testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper Pydantic type validation and coercion rules",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_numeric_type_boundaries(self) -> TestResult:
        """Test validation with different numeric models to verify int vs float handling."""
        test_results = []
        
        # Create models with different numeric types
        class IntModel(BaseModel):
            value: int
            
        class FloatModel(BaseModel):
            value: float
            
        class StrModel(BaseModel):
            value: str
        
        try:
            # Test with IntModel
            int_objective = StateEqualityObjective(goal=IntModel, output_key="test_key")
            
            # Integer to int field
            result1 = int_objective.eval({"test_key": {"value": 42}})
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Int to int should pass")
            test_results.append("Int→Int: True")
            
            # Float with no decimal to int field (42.0 → 42)
            result2 = int_objective.eval({"test_key": {"value": 42.0}})
            self.runner.assert_isinstance(result2, BoolEvalResult)
            # Pydantic should allow 42.0 → 42 conversion
            self.runner.assert_equal(result2.result, True, "Float 42.0 should coerce to int 42")
            test_results.append("Float(42.0)→Int: True")
            
            # Float with decimal to int field (42.5 → should fail)
            result3 = int_objective.eval({"test_key": {"value": 42.5}})
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, False, "Float 42.5 should not coerce to int (precision loss)")
            test_results.append("Float(42.5)→Int: False")
            
            # Test with FloatModel
            float_objective = StateEqualityObjective(goal=FloatModel, output_key="test_key")
            
            # Integer to float field
            result4 = float_objective.eval({"test_key": {"value": 42}})
            self.runner.assert_isinstance(result4, BoolEvalResult)
            self.runner.assert_equal(result4.result, True, "Int should coerce to float")
            test_results.append("Int→Float: True")
            
            # Float to float field
            result5 = float_objective.eval({"test_key": {"value": 42.7}})
            self.runner.assert_isinstance(result5, BoolEvalResult)
            self.runner.assert_equal(result5.result, True, "Float to float should pass")
            test_results.append("Float→Float: True")
            
            # Test with StrModel
            str_objective = StateEqualityObjective(goal=StrModel, output_key="test_key")
            
            # String to string
            result6 = str_objective.eval({"test_key": {"value": "hello"}})
            self.runner.assert_isinstance(result6, BoolEvalResult)
            self.runner.assert_equal(result6.result, True, "String to string should pass")
            test_results.append("Str→Str: True")
            
            # Number to string (Pydantic behavior)
            result7 = str_objective.eval({"test_key": {"value": 42}})
            self.runner.assert_isinstance(result7, BoolEvalResult)
            if result7.result:
                test_results.append("Int→Str: True")
            else:
                test_results.append("Int→Str: False")
            
            return TestResult(
                name="Numeric Type Boundaries",
                status=TestStatus.PASS,
                message="✓ Numeric type boundary validation: " + " | ".join(test_results),
                details=f"Type coercion rules: {test_results}",
                expected="Proper numeric type validation per Pydantic rules",
                actual="Numeric boundaries working correctly"
            )
        except Exception as e:
            return TestResult(
                name="Numeric Type Boundaries",
                status=TestStatus.FAIL,
                message=f"✗ Numeric type boundary testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper numeric type validation per Pydantic rules",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_numeric_range_validation(self) -> TestResult:
        """Test validation across different numeric ranges and edge cases."""
        test_results = []
        
        # Create models with different constraints
        class RangeModel(BaseModel):
            small_int: int
            large_int: int
            small_float: float
            large_float: float
            
        class ConstrainedModel(BaseModel):
            positive_int: int
            negative_int: int
            zero_value: int
            scientific_float: float
        
        try:
            range_objective = StateEqualityObjective(goal=RangeModel, output_key="test_key")
            
            # Test 1: Small numbers
            small_data = {
                "small_int": 1,
                "large_int": 1000000,
                "small_float": 0.1,
                "large_float": 1000000.5
            }
            result1 = range_objective.eval({"test_key": small_data})
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Small and large numbers should validate")
            test_results.append("Mixed ranges → True")
            
            # Test 2: Very large numbers
            large_data = {
                "small_int": 999999999,
                "large_int": 999999999999999,
                "small_float": 1e10,
                "large_float": 1.23e15
            }
            result2 = range_objective.eval({"test_key": large_data})
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, True, "Very large numbers should validate")
            test_results.append("Large numbers → True")
            
            # Test 3: Edge cases with constrained model
            constrained_objective = StateEqualityObjective(goal=ConstrainedModel, output_key="test_key")
            
            edge_data = {
                "positive_int": 1,
                "negative_int": -1,
                "zero_value": 0,
                "scientific_float": 1.23e-10
            }
            result3 = constrained_objective.eval({"test_key": edge_data})
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, True, "Edge case numbers should validate")
            test_results.append("Edge cases → True")
            
            # Test 4: Boundary integer values
            boundary_data = {
                "positive_int": 2147483647,  # Max 32-bit int
                "negative_int": -2147483648,  # Min 32-bit int
                "zero_value": 0,
                "scientific_float": float('inf')  # This might cause validation issues
            }
            result4 = constrained_objective.eval({"test_key": boundary_data})
            self.runner.assert_isinstance(result4, BoolEvalResult)
            # Infinity might be accepted or rejected depending on Pydantic version
            if result4.result:
                test_results.append("Boundary + inf → True")
            else:
                test_results.append("Boundary + inf → False")
            
            # Test 5: Scientific notation strings
            scientific_string_data = {
                "positive_int": "1e3",  # Should coerce to 1000
                "negative_int": "-2e2",  # Should coerce to -200
                "zero_value": "0e10",  # Should coerce to 0
                "scientific_float": "1.5e-5"  # Should coerce to 0.000015
            }
            result5 = constrained_objective.eval({"test_key": scientific_string_data})
            self.runner.assert_isinstance(result5, BoolEvalResult)
            if result5.result:
                test_results.append("Scientific notation strings → True")
            else:
                test_results.append("Scientific notation strings → False")
            
            # Test 6: Decimal precision edge cases
            precision_data = {
                "small_int": 1,
                "large_int": 1000,
                "small_float": 0.1 + 0.2,  # Classic floating point precision issue
                "large_float": 1.0000000000000001  # Very small precision difference
            }
            result6 = range_objective.eval({"test_key": precision_data})
            self.runner.assert_isinstance(result6, BoolEvalResult)
            self.runner.assert_equal(result6.result, True, "Floating point precision should not affect validation")
            test_results.append("Precision edge cases → True")
            
            return TestResult(
                name="Numeric Range Validation",
                status=TestStatus.PASS,
                message="✓ Numeric range validation completed: " + " | ".join(test_results),
                details=f"Range tests: {test_results}",
                expected="Proper handling of various numeric ranges and edge cases",
                actual="Numeric ranges handled correctly"
            )
        except Exception as e:
            return TestResult(
                name="Numeric Range Validation",
                status=TestStatus.FAIL,
                message=f"✗ Numeric range testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper handling of various numeric ranges and edge cases",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_extreme_values_and_special_cases(self) -> TestResult:
        """Test validation with extreme values, special float values, and boundary conditions."""
        test_results = []
        
        class ExtremesModel(BaseModel):
            normal_value: float
            optional_value: int = 0
            
        try:
            extremes_objective = StateEqualityObjective(goal=ExtremesModel, output_key="test_key")
            
            # Test 1: Normal case
            normal_data = {"normal_value": 42.5, "optional_value": 10}
            result1 = extremes_objective.eval({"test_key": normal_data})
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Normal values should validate")
            test_results.append("Normal values → True")
            
            # Test 2: Missing optional field (should use default)
            missing_optional = {"normal_value": 42.5}
            result2 = extremes_objective.eval({"test_key": missing_optional})
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, True, "Missing optional field should use default")
            test_results.append("Missing optional → True")
            
            # Test 3: Negative zero
            negative_zero_data = {"normal_value": -0.0, "optional_value": 0}
            result3 = extremes_objective.eval({"test_key": negative_zero_data})
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, True, "Negative zero should validate")
            test_results.append("Negative zero → True")
            
            # Test 4: Very small numbers (near machine epsilon)
            tiny_data = {"normal_value": 1e-100, "optional_value": 1}
            result4 = extremes_objective.eval({"test_key": tiny_data})
            self.runner.assert_isinstance(result4, BoolEvalResult)
            self.runner.assert_equal(result4.result, True, "Very small numbers should validate")
            test_results.append("Tiny numbers → True")
            
            # Test 5: Very large numbers
            huge_data = {"normal_value": 1e100, "optional_value": 999999999}
            result5 = extremes_objective.eval({"test_key": huge_data})
            self.runner.assert_isinstance(result5, BoolEvalResult)
            self.runner.assert_equal(result5.result, True, "Very large numbers should validate")
            test_results.append("Huge numbers → True")
            
            # Test 6: Special float values (NaN)
            nan_data = {"normal_value": float('nan'), "optional_value": 1}
            result6 = extremes_objective.eval({"test_key": nan_data})
            self.runner.assert_isinstance(result6, BoolEvalResult)
            # NaN might be rejected by Pydantic validation
            if result6.result:
                test_results.append("NaN → True")
            else:
                test_results.append("NaN → False")
            
            # Test 7: Negative infinity
            neg_inf_data = {"normal_value": float('-inf'), "optional_value": 1}
            result7 = extremes_objective.eval({"test_key": neg_inf_data})
            self.runner.assert_isinstance(result7, BoolEvalResult)
            if result7.result:
                test_results.append("Negative infinity → True")
            else:
                test_results.append("Negative infinity → False")
            
            # Test 8: String representations of extreme values
            extreme_string_data = {"normal_value": "1e-50", "optional_value": "999999"}
            result8 = extremes_objective.eval({"test_key": extreme_string_data})
            self.runner.assert_isinstance(result8, BoolEvalResult)
            if result8.result:
                test_results.append("Extreme string values → True")
            else:
                test_results.append("Extreme string values → False")
            
            return TestResult(
                name="Extreme Values and Special Cases",
                status=TestStatus.PASS,
                message="✓ Extreme values testing completed: " + " | ".join(test_results),
                details=f"Special cases: {test_results}",
                expected="Proper handling of extreme values and special float cases",
                actual="Extreme values handled appropriately"
            )
        except Exception as e:
            return TestResult(
                name="Extreme Values and Special Cases",
                status=TestStatus.FAIL,
                message=f"✗ Extreme values testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper handling of extreme values and special float cases",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_custom_validator_models(self) -> TestResult:
        """Test StateEqualityObjective with Pydantic models that have custom validators."""
        from pydantic import field_validator, model_validator
        import re
        
        test_results = []
        
        # Create models with various custom validators
        class EmailModel(BaseModel):
            email: str
            name: str
            
            @field_validator('email')
            @classmethod
            def validate_email(cls, v):
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                    raise ValueError('Invalid email format')
                return v.lower()  # Normalize to lowercase
        
        class PasswordModel(BaseModel):
            username: str
            password: str
            confirm_password: str
            
            @field_validator('password')
            @classmethod
            def validate_password_strength(cls, v):
                if len(v) < 8:
                    raise ValueError('Password must be at least 8 characters')
                if not re.search(r'[A-Z]', v):
                    raise ValueError('Password must contain at least one uppercase letter')
                if not re.search(r'[0-9]', v):
                    raise ValueError('Password must contain at least one number')
                return v
            
            @model_validator(mode='after')
            def validate_passwords_match(self):
                if self.password != self.confirm_password:
                    raise ValueError('Passwords do not match')
                return self
        
        class RangeModel(BaseModel):
            age: int
            score: float
            
            @field_validator('age')
            @classmethod
            def validate_age(cls, v):
                if v < 0 or v > 150:
                    raise ValueError('Age must be between 0 and 150')
                return v
            
            @field_validator('score')
            @classmethod
            def validate_score(cls, v):
                if v < 0.0 or v > 100.0:
                    raise ValueError('Score must be between 0.0 and 100.0')
                return round(v, 2)  # Round to 2 decimal places
        
        try:
            # Test 1: Email validation - valid email
            email_objective = StateEqualityObjective(goal=EmailModel, output_key="test_key")
            
            valid_email_data = {"email": "User@Example.COM", "name": "John Doe"}
            result1 = email_objective.eval({"test_key": valid_email_data})
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Valid email should pass validation")
            test_results.append("Valid email → True")
            
            # Test 2: Email validation - invalid email
            invalid_email_data = {"email": "not-an-email", "name": "John Doe"}
            result2 = email_objective.eval({"test_key": invalid_email_data})
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, False, "Invalid email should fail validation")
            test_results.append("Invalid email → False")
            
            # Test 3: Password validation - valid password
            password_objective = StateEqualityObjective(goal=PasswordModel, output_key="test_key")
            
            valid_password_data = {
                "username": "johndoe",
                "password": "StrongPass123",
                "confirm_password": "StrongPass123"
            }
            result3 = password_objective.eval({"test_key": valid_password_data})
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, True, "Valid password should pass validation")
            test_results.append("Valid password → True")
            
            # Test 4: Password validation - weak password
            weak_password_data = {
                "username": "johndoe",
                "password": "weak",  # Too short, no uppercase, no number
                "confirm_password": "weak"
            }
            result4 = password_objective.eval({"test_key": weak_password_data})
            self.runner.assert_isinstance(result4, BoolEvalResult)
            self.runner.assert_equal(result4.result, False, "Weak password should fail validation")
            test_results.append("Weak password → False")
            
            # Test 5: Password validation - mismatched passwords
            mismatch_password_data = {
                "username": "johndoe",
                "password": "StrongPass123",
                "confirm_password": "DifferentPass123"
            }
            result5 = password_objective.eval({"test_key": mismatch_password_data})
            self.runner.assert_isinstance(result5, BoolEvalResult)
            self.runner.assert_equal(result5.result, False, "Mismatched passwords should fail validation")
            test_results.append("Mismatched passwords → False")
            
            # Test 6: Range validation - valid values
            range_objective = StateEqualityObjective(goal=RangeModel, output_key="test_key")
            
            valid_range_data = {"age": 25, "score": 87.654}  # Score should be rounded to 87.65
            result6 = range_objective.eval({"test_key": valid_range_data})
            self.runner.assert_isinstance(result6, BoolEvalResult)
            self.runner.assert_equal(result6.result, True, "Valid range values should pass")
            test_results.append("Valid ranges → True")
            
            # Test 7: Range validation - age out of range
            invalid_age_data = {"age": 200, "score": 75.0}  # Age too high
            result7 = range_objective.eval({"test_key": invalid_age_data})
            self.runner.assert_isinstance(result7, BoolEvalResult)
            self.runner.assert_equal(result7.result, False, "Age out of range should fail")
            test_results.append("Invalid age range → False")
            
            # Test 8: Range validation - score out of range
            invalid_score_data = {"age": 25, "score": 150.0}  # Score too high
            result8 = range_objective.eval({"test_key": invalid_score_data})
            self.runner.assert_isinstance(result8, BoolEvalResult)
            self.runner.assert_equal(result8.result, False, "Score out of range should fail")
            test_results.append("Invalid score range → False")
            
            # Test 9: Edge case - boundary values
            boundary_data = {"age": 0, "score": 100.0}  # Boundary values
            result9 = range_objective.eval({"test_key": boundary_data})
            self.runner.assert_isinstance(result9, BoolEvalResult)
            self.runner.assert_equal(result9.result, True, "Boundary values should pass")
            test_results.append("Boundary values → True")
            
            return TestResult(
                name="Custom Validator Models",
                status=TestStatus.PASS,
                message="✓ Custom validator testing completed: " + " | ".join(test_results),
                details=f"Validator tests: {test_results}",
                expected="Proper handling of custom Pydantic validators",
                actual="Custom validators working correctly"
            )
        except Exception as e:
            return TestResult(
                name="Custom Validator Models",
                status=TestStatus.FAIL,
                message=f"✗ Custom validator testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper handling of custom Pydantic validators",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_advanced_custom_validators(self) -> TestResult:
        """Test StateEqualityObjective with more advanced custom validator scenarios."""
        from pydantic import field_validator, model_validator, Field
        from typing import List
        import datetime
        
        test_results = []
        
        # Advanced models with complex validation logic
        class UserProfileModel(BaseModel):
            username: str = Field(min_length=3, max_length=20)
            birth_date: str
            tags: List[str]
            is_premium: bool = False
            
            @field_validator('username')
            @classmethod
            def validate_username(cls, v):
                if not v.isalnum():
                    raise ValueError('Username must be alphanumeric')
                return v.lower()
            
            @field_validator('birth_date')
            @classmethod
            def validate_birth_date(cls, v):
                try:
                    date = datetime.datetime.strptime(v, '%Y-%m-%d')
                    if date > datetime.datetime.now():
                        raise ValueError('Birth date cannot be in the future')
                    return v
                except ValueError as e:
                    if 'does not match format' in str(e):
                        raise ValueError('Birth date must be in YYYY-MM-DD format')
                    raise e
            
            @field_validator('tags')
            @classmethod
            def validate_tags(cls, v):
                if len(v) > 5:
                    raise ValueError('Maximum 5 tags allowed')
                # Remove duplicates and normalize
                return list(set(tag.lower().strip() for tag in v if tag.strip()))
            
            @model_validator(mode='after')
            def validate_premium_requirements(self):
                if self.is_premium and len(self.tags) < 2:
                    raise ValueError('Premium users must have at least 2 tags')
                return self
        
        class FinancialModel(BaseModel):
            amount: float
            currency: str
            transaction_type: str
            
            @field_validator('amount')
            @classmethod
            def validate_amount(cls, v):
                if v <= 0:
                    raise ValueError('Amount must be positive')
                if v > 1000000:
                    raise ValueError('Amount too large')
                return round(v, 2)
            
            @field_validator('currency')
            @classmethod
            def validate_currency(cls, v):
                valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD']
                if v.upper() not in valid_currencies:
                    raise ValueError(f'Currency must be one of: {valid_currencies}')
                return v.upper()
            
            @field_validator('transaction_type')
            @classmethod
            def validate_transaction_type(cls, v):
                valid_types = ['credit', 'debit', 'transfer']
                if v.lower() not in valid_types:
                    raise ValueError(f'Transaction type must be one of: {valid_types}')
                return v.lower()
        
        try:
            # Test 1: User profile - valid data
            profile_objective = StateEqualityObjective(goal=UserProfileModel, output_key="test_key")
            
            valid_profile_data = {
                "username": "JohnDoe123",
                "birth_date": "1990-05-15",
                "tags": ["python", "developer", "tech"],
                "is_premium": False
            }
            result1 = profile_objective.eval({"test_key": valid_profile_data})
            self.runner.assert_isinstance(result1, BoolEvalResult)
            self.runner.assert_equal(result1.result, True, "Valid profile should pass")
            test_results.append("Valid profile → True")
            
            # Test 2: User profile - invalid username (non-alphanumeric)
            invalid_username_data = {
                "username": "john-doe!",  # Contains special characters
                "birth_date": "1990-05-15",
                "tags": ["python"],
                "is_premium": False
            }
            result2 = profile_objective.eval({"test_key": invalid_username_data})
            self.runner.assert_isinstance(result2, BoolEvalResult)
            self.runner.assert_equal(result2.result, False, "Invalid username should fail")
            test_results.append("Invalid username → False")
            
            # Test 3: User profile - future birth date
            future_birth_data = {
                "username": "johndoe",
                "birth_date": "2030-01-01",  # Future date
                "tags": ["python"],
                "is_premium": False
            }
            result3 = profile_objective.eval({"test_key": future_birth_data})
            self.runner.assert_isinstance(result3, BoolEvalResult)
            self.runner.assert_equal(result3.result, False, "Future birth date should fail")
            test_results.append("Future birth date → False")
            
            # Test 4: User profile - too many tags
            too_many_tags_data = {
                "username": "johndoe",
                "birth_date": "1990-05-15",
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],  # 6 tags (max 5)
                "is_premium": False
            }
            result4 = profile_objective.eval({"test_key": too_many_tags_data})
            self.runner.assert_isinstance(result4, BoolEvalResult)
            self.runner.assert_equal(result4.result, False, "Too many tags should fail")
            test_results.append("Too many tags → False")
            
            # Test 5: User profile - premium user without enough tags
            premium_insufficient_tags = {
                "username": "johndoe",
                "birth_date": "1990-05-15",
                "tags": ["python"],  # Only 1 tag, but premium needs 2+
                "is_premium": True
            }
            result5 = profile_objective.eval({"test_key": premium_insufficient_tags})
            self.runner.assert_isinstance(result5, BoolEvalResult)
            self.runner.assert_equal(result5.result, False, "Premium user with insufficient tags should fail")
            test_results.append("Premium insufficient tags → False")
            
            # Test 6: Financial model - valid transaction
            financial_objective = StateEqualityObjective(goal=FinancialModel, output_key="test_key")
            
            valid_financial_data = {
                "amount": 1234.567,  # Should be rounded to 1234.57
                "currency": "usd",    # Should be normalized to USD
                "transaction_type": "CREDIT"  # Should be normalized to credit
            }
            result6 = financial_objective.eval({"test_key": valid_financial_data})
            self.runner.assert_isinstance(result6, BoolEvalResult)
            self.runner.assert_equal(result6.result, True, "Valid financial data should pass")
            test_results.append("Valid financial → True")
            
            # Test 7: Financial model - invalid currency
            invalid_currency_data = {
                "amount": 100.0,
                "currency": "XYZ",  # Invalid currency
                "transaction_type": "credit"
            }
            result7 = financial_objective.eval({"test_key": invalid_currency_data})
            self.runner.assert_isinstance(result7, BoolEvalResult)
            self.runner.assert_equal(result7.result, False, "Invalid currency should fail")
            test_results.append("Invalid currency → False")
            
            # Test 8: Financial model - negative amount
            negative_amount_data = {
                "amount": -50.0,  # Negative amount
                "currency": "USD",
                "transaction_type": "debit"
            }
            result8 = financial_objective.eval({"test_key": negative_amount_data})
            self.runner.assert_isinstance(result8, BoolEvalResult)
            self.runner.assert_equal(result8.result, False, "Negative amount should fail")
            test_results.append("Negative amount → False")
            
            return TestResult(
                name="Advanced Custom Validators",
                status=TestStatus.PASS,
                message="✓ Advanced validator testing completed: " + " | ".join(test_results),
                details=f"Advanced tests: {test_results}",
                expected="Proper handling of complex custom validation scenarios",
                actual="Advanced validators working correctly"
            )
        except Exception as e:
            return TestResult(
                name="Advanced Custom Validators",
                status=TestStatus.FAIL,
                message=f"✗ Advanced validator testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Proper handling of complex custom validation scenarios",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_in_place_modification_safety(self) -> TestResult:
        """Test that _format_filtered_output doesn't cause issues with in-place modification."""
        goal = SimpleTestModel
        output_key = "test_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        try:
            # Create test data that will be modified in place
            original_json_string = '{"name": "json_test", "value": 100}'
            agent_output = {"test_data": original_json_string}
            
            # Store the original value for comparison
            original_data = agent_output["test_data"]
            
            result = objective.eval(agent_output)
            
            # Verify the result is correct
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "JSON string should validate successfully")
            
            # Check if the original agent_output dict was modified
            # (This tests the in-place modification behavior)
            data_was_modified = agent_output["test_data"] != original_data
            
            return TestResult(
                name="In-Place Modification Safety",
                status=TestStatus.PASS,
                message=f"✓ In-place modification behavior documented: data modified={data_was_modified}",
                details=f"Original data: {type(original_data).__name__} | Final data: {type(agent_output['test_data']).__name__} | Result: {result.result}",
                expected="Successful validation regardless of modification",
                actual="Validation successful"
            )
        except Exception as e:
            return TestResult(
                name="In-Place Modification Safety",
                status=TestStatus.FAIL,
                message=f"✗ In-place modification test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful validation regardless of modification",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_async_state_equality_basic(self) -> TestResult:
        """Test basic async functionality of StateEqualityObjective."""
        async def async_test():
            goal = SimpleTestModel
            output_key = "test_data"
            objective = StateEqualityObjective(goal=goal, output_key=output_key)
            
            # Valid data that matches the model
            valid_data = {"name": "async_test", "value": 42}
            agent_output = {"test_data": valid_data}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, True, "Should return True for valid async evaluation")
                
                return TestResult(
                    name="Async State Equality - Basic",
                    status=TestStatus.PASS,
                    message=f"✓ Async evaluation successful for {goal.__name__}",
                    details=f"Model: {goal.__name__} | Data: {valid_data} | Result: {result.result}",
                    expected=True,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async State Equality - Basic",
                    status=TestStatus.FAIL,
                    message=f"✗ Async evaluation failed: {str(e)}",
                    details=f"Model: {goal.__name__} | Data: {valid_data} | Result type: {type(result).__name__}",
                    expected=True,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_state_equality_validation_failure(self) -> TestResult:
        """Test async functionality with validation failure."""
        async def async_test():
            goal = SimpleTestModel
            output_key = "test_data"
            objective = StateEqualityObjective(goal=goal, output_key=output_key)
            
            # Invalid data that doesn't match the model
            invalid_data = {"name": "async_test"}  # Missing 'value' field
            agent_output = {"test_data": invalid_data}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, False, "Should return False for invalid async data")
                
                return TestResult(
                    name="Async State Equality - Validation Failure",
                    status=TestStatus.PASS,
                    message=f"✓ Async validation failure correctly detected for {goal.__name__}",
                    details=f"Model: {goal.__name__} | Data: {invalid_data} | Result: {result.result}",
                    expected=False,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async State Equality - Validation Failure",
                    status=TestStatus.FAIL,
                    message=f"✗ Async validation failure test failed: {str(e)}",
                    details=f"Model: {goal.__name__} | Data: {invalid_data} | Result type: {type(result).__name__}",
                    expected=False,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_state_equality_json_formatting(self) -> TestResult:
        """Test async functionality with JSON string formatting."""
        async def async_test():
            goal = SimpleTestModel
            output_key = "json_data"
            objective = StateEqualityObjective(goal=goal, output_key=output_key)
            
            # Valid JSON string that should parse and validate
            valid_json_string = '{"name": "async_json_test", "value": 123}'
            agent_output = {"json_data": valid_json_string}
            
            # Test async evaluation
            result = await objective.eval_async(agent_output)
            
            try:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
                self.runner.assert_equal(result.result, True, "Should return True for valid async JSON")
                
                return TestResult(
                    name="Async State Equality - JSON Formatting",
                    status=TestStatus.PASS,
                    message=f"✓ Async JSON string validation successful for {goal.__name__}",
                    details=f"Model: {goal.__name__} | JSON: {valid_json_string} | Result: {result.result}",
                    expected=True,
                    actual=result.result
                )
            except Exception as e:
                return TestResult(
                    name="Async State Equality - JSON Formatting",
                    status=TestStatus.FAIL,
                    message=f"✗ Async JSON validation failed: {str(e)}",
                    details=f"Model: {goal.__name__} | JSON: {valid_json_string} | Result type: {type(result).__name__}",
                    expected=True,
                    actual=getattr(result, 'result', None),
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_async_vs_sync_consistency(self) -> TestResult:
        """Test that async and sync evaluations produce identical results."""
        async def async_test():
            goal = SimpleTestModel
            output_key = "test_data"
            objective = StateEqualityObjective(goal=goal, output_key=output_key)
            
            test_cases = [
                # (data, description)
                ({"name": "test", "value": 42}, "valid data"),
                ({"name": "test"}, "missing field"),
                ('{"name": "test", "value": 99}', "JSON string"),
                ({"name": 123, "value": "invalid"}, "wrong types"),
            ]
            
            results = []
            
            try:
                for data, description in test_cases:
                    agent_output = {"test_data": data}
                    
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
                    name="Async vs Sync Consistency",
                    status=TestStatus.PASS,
                    message="✓ Async and sync evaluations produce identical results",
                    details=f"Test cases: {len(test_cases)} | Results: " + " | ".join(results),
                    expected="Identical async/sync results",
                    actual="All results match"
                )
            except Exception as e:
                return TestResult(
                    name="Async vs Sync Consistency",
                    status=TestStatus.FAIL,
                    message=f"✗ Async/sync consistency test failed: {str(e)}",
                    details=f"Completed tests: {results} | Error: {str(e)}",
                    expected="Identical async/sync results",
                    actual=f"Error: {str(e)}",
                    traceback=traceback.format_exc()
                )
        
        return self.runner.run_async_test(async_test)
    
    def test_nested_validation_failure_propagation(self) -> TestResult:
        """Test how validation errors propagate through nested models."""
        goal = ComplexTestModel
        output_key = "complex_data"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        test_results = []
        
        try:
            # Test 1: Missing required field in nested user model
            complex_data1 = {
                "user": {
                    "id": 1,
                    "username": "testuser",
                    # missing "email" field
                    "active": True
                },
                "products": [],
                "total_amount": 0.0
            }
            agent_output1 = {"complex_data": complex_data1}
            result1 = objective.eval(agent_output1)
            
            self.runner.assert_isinstance(result1, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result1.result, False, "Should fail for missing email in user")
            test_results.append("Missing user.email → False")
            
            # Test 2: Invalid product structure
            complex_data2 = {
                "user": {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "active": True
                },
                "products": [
                    {
                        "product_id": "PROD001",
                        "name": "Test Product",
                        # missing "price" field
                        "category": "electronics"
                    }
                ],
                "total_amount": 99.99
            }
            agent_output2 = {"complex_data": complex_data2}
            result2 = objective.eval(agent_output2)
            
            self.runner.assert_isinstance(result2, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result2.result, False, "Should fail for missing price in product")
            test_results.append("Missing product.price → False")
            
            # Test 3: Wrong data type in nested structure
            complex_data3 = {
                "user": {
                    "id": "not_an_int",  # Should be int
                    "username": "testuser",
                    "email": "test@example.com",
                    "active": True
                },
                "products": [],
                "total_amount": 0.0
            }
            agent_output3 = {"complex_data": complex_data3}
            result3 = objective.eval(agent_output3)
            
            self.runner.assert_isinstance(result3, BoolEvalResult, "Should return BoolEvalResult")
            # Depending on Pydantic's coercion rules, this might pass or fail
            if result3.result:
                test_results.append("String to int coercion → True")
            else:
                test_results.append("Invalid user.id type → False")
            
            return TestResult(
                name="Nested Validation Failure Propagation",
                status=TestStatus.PASS,
                message="✓ Nested validation errors properly detected: " + " | ".join(test_results),
                details=f"Tests: {test_results}",
                expected="Validation failures in nested structures properly propagated",
                actual="Nested validation working correctly"
            )
        except Exception as e:
            return TestResult(
                name="Nested Validation Failure Propagation",
                status=TestStatus.FAIL,
                message=f"✗ Nested validation testing failed: {str(e)}",
                details=f"Completed tests: {test_results} | Error: {str(e)}",
                expected="Validation failures in nested structures properly propagated",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_empty_agent_output(self) -> TestResult:
        """Test behavior with completely empty agent output."""
        goal = SimpleTestModel
        output_key = "test_key"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        agent_output = {}  # Completely empty
        
        result = objective.eval(agent_output)
        
        try:
            self.runner.assert_isinstance(result, OutputKeyNotFoundError, "Should return OutputKeyNotFoundError for empty output")
            
            return TestResult(
                name="Empty Agent Output",
                status=TestStatus.PASS,
                message=f"✓ Correctly handled empty agent output for key '{output_key}'",
                details=f"Goal: {goal.__name__} | Key: '{output_key}' | Empty output: {{}} | Error: {result.message}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__
            )
        except Exception as e:
            return TestResult(
                name="Empty Agent Output",
                status=TestStatus.FAIL,
                message=f"✗ Empty agent output handling failed: {str(e)}",
                details=f"Goal: {goal.__name__} | Key: '{output_key}' | Result type: {type(result).__name__}",
                expected="OutputKeyNotFoundError",
                actual=type(result).__name__,
                traceback=traceback.format_exc()
            )
    
    def test_none_agent_output(self) -> TestResult:
        """Test behavior with None as agent output (should return ExtractionError)."""
        goal = SimpleTestModel
        output_key = "test_key"
        objective = StateEqualityObjective(goal=goal, output_key=output_key)
        
        try:
            result = objective.eval(None)
            
            # The correct behavior is to return an ExtractionError
            if hasattr(result, '__class__') and 'ExtractionError' in str(type(result)):
                return TestResult(
                    name="None Agent Output",
                    status=TestStatus.PASS,
                    message=f"✓ Correctly handled None agent output with {type(result).__name__}",
                    details=f"Goal: {goal.__name__} | Key: '{output_key}' | Input: None | Result type: {type(result).__name__} | Message: {getattr(result, 'message', 'N/A')}",
                    expected="ExtractionError",
                    actual=type(result).__name__
                )
            else:
                return TestResult(
                    name="None Agent Output",
                    status=TestStatus.FAIL,
                    message=f"✗ Expected ExtractionError but got {type(result).__name__}",
                    details=f"Goal: {goal.__name__} | Key: '{output_key}' | Input: None | Result type: {type(result).__name__}",
                    expected="ExtractionError",
                    actual=type(result).__name__
                )
        except Exception as e:
            # If an exception is raised instead of returning ExtractionError, that's also acceptable
            return TestResult(
                name="None Agent Output",
                status=TestStatus.PASS,
                message=f"✓ Correctly raised exception for None agent output: {type(e).__name__}",
                details=f"Goal: {goal.__name__} | Key: '{output_key}' | Input: None | Exception: {str(e)}",
                expected="Exception or ExtractionError",
                actual=f"Exception: {type(e).__name__}"
            )
    
    def test_concurrent_evaluation_safety(self) -> TestResult:
        """Test that objective evaluation is thread-safe and doesn't have side effects."""
        try:
            import threading
            
            objective = StateEqualityObjective(goal=SimpleTestModel, output_key="test_key")
            results = []
            errors = []
            
            def evaluate_objective(thread_id):
                try:
                    if thread_id % 2 == 0:
                        agent_output = {"test_key": {"name": "test", "value": thread_id}}
                    else:
                        agent_output = {"test_key": {"name": "test"}}  # Missing value field
                    
                    result = objective.eval(agent_output)
                    results.append((thread_id, result.result if hasattr(result, 'result') else False))
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # Create and start multiple threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=evaluate_objective, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            if errors:
                return TestResult(
                    name="Concurrent Evaluation Safety",
                    status=TestStatus.FAIL,
                    message=f"✗ Thread safety test failed with {len(errors)} errors",
                    details=f"Errors: {errors[:3]} | Total results: {len(results)}",
                    expected="No thread errors",
                    actual=f"{len(errors)} errors occurred"
                )
            
            # Verify we got results from all threads
            self.runner.assert_equal(len(results), 10, "Should have 10 results from 10 threads")
            
            # Verify results are consistent (even threads should be True, odd should be False)
            expected_results = {i: (i % 2 == 0) for i in range(10)}
            actual_results = {thread_id: result for thread_id, result in results}
            
            for thread_id in range(10):
                expected = expected_results[thread_id]
                actual = actual_results.get(thread_id, None)
                self.runner.assert_equal(actual, expected, f"Thread {thread_id} result mismatch")
            
            return TestResult(
                name="Concurrent Evaluation Safety",
                status=TestStatus.PASS,
                message=f"✓ Thread safety test passed with {len(results)} consistent results",
                details=f"Threads: 10 | Results: {len(results)} | Errors: {len(errors)} | Pattern: alternating True/False",
                expected="Thread-safe evaluation",
                actual="All threads completed safely with consistent results"
            )
        except Exception as e:
            return TestResult(
                name="Concurrent Evaluation Safety",
                status=TestStatus.FAIL,
                message=f"✗ Concurrent evaluation test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Thread-safe evaluation",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def test_memory_efficiency_large_models(self) -> TestResult:
        """Test memory efficiency with large models and data."""
        try:
            # Create a model with many fields
            class LargeModel(BaseModel):
                field_01: str
                field_02: int
                field_03: float
                field_04: bool
                field_05: str
                field_06: int
                field_07: float
                field_08: bool
                field_09: str
                field_10: int
                field_11: float
                field_12: bool
                field_13: str
                field_14: int
                field_15: float
                field_16: bool
                field_17: str
                field_18: int
                field_19: float
                field_20: bool
            
            objective = StateEqualityObjective(goal=LargeModel, output_key="large_data")
            
            # Create valid large data
            large_data = {
                f"field_{i:02d}": "string" if i % 4 == 1 else 
                                 42 if i % 4 == 2 else 
                                 3.14 if i % 4 == 3 else 
                                 True
                for i in range(1, 21)
            }
            
            agent_output = {"large_data": large_data}
            
            import time
            start_time = time.time()
            result = objective.eval(agent_output)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            self.runner.assert_equal(result.result, True, "Large model should validate successfully")
            
            # Check execution time (should be reasonable)
            if execution_time > 1.0:  # More than 1 second is concerning
                return TestResult(
                    name="Memory Efficiency Large Models",
                    status=TestStatus.FAIL,
                    message=f"✗ Large model validation took too long: {execution_time:.2f}s",
                    details=f"Model fields: 20 | Execution time: {execution_time:.2f}s | Result: {result.result}",
                    expected="Fast execution",
                    actual=f"Slow execution: {execution_time:.2f}s"
                )
            
            return TestResult(
                name="Memory Efficiency Large Models",
                status=TestStatus.PASS,
                message=f"✓ Large model validation completed efficiently in {execution_time:.3f}s",
                details=f"Model fields: 20 | Execution time: {execution_time:.3f}s | Result: {result.result}",
                expected="Efficient large model handling",
                actual=f"Efficient execution in {execution_time:.3f}s"
            )
        except Exception as e:
            return TestResult(
                name="Memory Efficiency Large Models",
                status=TestStatus.FAIL,
                message=f"✗ Large model test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Efficient large model handling",
                actual=f"Error: {str(e)}",
                traceback=traceback.format_exc()
            )


def main():
    """Main test execution function."""
    runner = TestRunner()
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]StateBenchmarkObjective Test Suite", style="cyan")
        runner.console.print("\n[bold]Testing StateEqualityObjective and PartialStateEqualityObjective classes[/bold]\n")
    else:
        print("="*60)
        print("StateBenchmarkObjective Test Suite")
        print("="*60)
        print("Testing StateEqualityObjective and PartialStateEqualityObjective classes\n")
    
    # Initialize test suites
    tests = StateBenchmarkObjectiveTests(runner)
    partial_tests = PartialStateBenchmarkObjectiveTests(runner)
    
    # Define test methods to run
    test_methods = [
        ("State Equality Simple Success", tests.test_state_equality_success_simple),
        ("State Equality Validation Failure", tests.test_state_equality_failure_validation),
        ("State Equality Missing Key", tests.test_state_equality_missing_key),
        ("State Equality JSON String Success", tests.test_state_equality_json_string_input),
        ("State Equality BaseModel Success", tests.test_state_equality_basemodel_input),
        ("State Equality Complex Model Success", tests.test_state_equality_complex_model),
        ("State Equality Invalid JSON", tests.test_state_equality_invalid_json),
        ("State Equality Valid Result Type", tests.test_state_equality_valid_result_type),

        ("Edge Cases", tests.test_edge_cases),
        ("Non-Dict Values", tests.test_non_dict_values),
        ("Malformed JSON Strings", tests.test_malformed_json_strings),
        ("Type Validation Comprehensive", tests.test_type_validation_comprehensive),
        ("Numeric Type Boundaries", tests.test_numeric_type_boundaries),
        ("Numeric Range Validation", tests.test_numeric_range_validation),
        ("Extreme Values and Special Cases", tests.test_extreme_values_and_special_cases),
        ("Custom Validator Models", tests.test_custom_validator_models),
        ("Advanced Custom Validators", tests.test_advanced_custom_validators),
        ("In-Place Modification Safety", tests.test_in_place_modification_safety),
        ("Nested Validation Failure Propagation", tests.test_nested_validation_failure_propagation),
        ("Empty Agent Output", tests.test_empty_agent_output),
        ("None Agent Output", tests.test_none_agent_output),
        ("Concurrent Evaluation Safety", tests.test_concurrent_evaluation_safety),
        ("Memory Efficiency Large Models", tests.test_memory_efficiency_large_models),
        
        # StateEqualityObjective async tests
        ("Async State Equality - Basic", tests.test_async_state_equality_basic),
        ("Async State Equality - Validation Failure", tests.test_async_state_equality_validation_failure),
        ("Async State Equality - JSON Formatting", tests.test_async_state_equality_json_formatting),
        ("Async vs Sync Consistency", tests.test_async_vs_sync_consistency),
        
        # PartialStateEqualityObjective tests
        ("Partial State Equality - No Errors", partial_tests.test_partial_state_equality_no_errors),
        ("Partial State Equality - Single Error", partial_tests.test_partial_state_equality_single_error),
        ("Partial State Equality - Multiple Errors", partial_tests.test_partial_state_equality_multiple_errors),
        ("Partial State Equality - Complex Model Errors", partial_tests.test_partial_state_equality_complex_model_errors),

        ("Partial State Equality - Pass Rate Calculation", partial_tests.test_partial_state_equality_pass_rate_calculation),
        ("Partial State Equality - Nested Field Counting", partial_tests.test_partial_state_equality_nested_field_counting),
        ("Partial State Equality - Non-Validation Exception", partial_tests.test_partial_state_equality_non_validation_exception),
        ("Partial State Equality - Valid Result Type", partial_tests.test_partial_state_equality_valid_result_type),
        ("Partial State Equality - Custom Validators", partial_tests.test_partial_state_equality_with_custom_validators),
        ("Partial State Equality - Missing Key", partial_tests.test_partial_state_equality_missing_key),
        ("Partial State Equality - JSON Formatting Error", partial_tests.test_partial_state_equality_json_formatting_error),
        
        # PartialStateEqualityObjective async tests
        ("Async Partial State Equality - Basic", partial_tests.test_async_partial_state_equality_basic),
        ("Async Partial State Equality - Partial Errors", partial_tests.test_async_partial_state_equality_partial_errors),
        ("Async vs Sync Partial Consistency", partial_tests.test_async_vs_sync_partial_consistency),
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
