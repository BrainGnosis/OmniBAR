#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive Test Suite Runner for OmniBAR

This master test file orchestrates all individual test files to provide complete
package coverage testing. It organizes tests into logical categories and provides
detailed reporting on the entire package functionality.

Usage:
    python test_all.py                    # Run all tests
    python test_all.py --category core    # Run only core tests
    python test_all.py --category objectives  # Run only objectives tests
    python test_all.py --fast             # Run fast tests only (skip slow integration tests)
    python test_all.py --verbose          # Detailed output
    python test_all.py --list             # List all available tests
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Rich terminal output for beautiful reporting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.tree import Tree
    from rich.align import Align
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich library not available. Install with: pip install rich")


class TestCategory(Enum):
    """Test categories for organized execution."""
    IMPORTS = "imports"
    CORE = "core" 
    OBJECTIVES = "objectives"
    INTEGRATIONS = "integrations"
    LOGGING = "logging"
    EXAMPLES = "examples"
    ALL = "all"


class TestStatus(Enum):
    """Test execution status."""
    PASS = "✅"
    FAIL = "❌"
    ERROR = "💥" 
    SKIP = "⏭️"
    TIMEOUT = "⏰"
    NOT_RUN = "⭕"


@dataclass
class TestFile:
    """Individual test file specification."""
    name: str
    file_path: str
    category: TestCategory
    description: str
    estimated_time: int  # seconds
    requires_env: bool = False
    requires_internet: bool = False
    is_slow: bool = False


@dataclass
class TestResult:
    """Result of running a test file."""
    test_file: TestFile
    status: TestStatus
    duration: float
    output: str
    error_output: str
    exit_code: int
    details: str = ""


class OmniBarTestSuite:
    """Master test suite for OmniBAR package."""
    
    def __init__(self, verbose: bool = False):
        self.console = Console() if RICH_AVAILABLE else None
        self.verbose = verbose
        self.test_dir = Path(__file__).parent
        self.results: List[TestResult] = []
        
        # Define all test files with metadata
        self.test_files = [
            # Import Tests
            TestFile(
                name="Package Imports",
                file_path="test_imports.py",
                category=TestCategory.IMPORTS,
                description="Verify all package imports work correctly",
                estimated_time=10,
                requires_env=False
            ),
            
            # Core Functionality Tests  
            TestFile(
                name="OmniBarmarker Core",
                file_path="test_omnibarmarker.py",
                category=TestCategory.CORE,
                description="Core benchmarker functionality, async/sync execution",
                estimated_time=45,
                requires_env=True,
                requires_internet=True,
                is_slow=True
            ),
            
            # Objectives Tests
            TestFile(
                name="Output-Based Objectives",
                file_path="test_output_benchmark_objective.py",
                category=TestCategory.OBJECTIVES,
                description="StringEqualityObjective and RegexMatchObjective",
                estimated_time=25,
                requires_env=False
            ),
            TestFile(
                name="Combined Objectives",
                file_path="test_combined_benchmark_objective.py", 
                category=TestCategory.OBJECTIVES,
                description="Multi-objective combined evaluation",
                estimated_time=40,
                requires_env=True,
                requires_internet=True,
                is_slow=True
            ),
            TestFile(
                name="Path-Based Objectives",
                file_path="test_path_benchmark_objective.py",
                category=TestCategory.OBJECTIVES,
                description="PathEqualityObjective for action sequence evaluation",
                estimated_time=20,
                requires_env=False
            ),
            TestFile(
                name="State-Based Objectives",
                file_path="test_state_benchmark_objective.py",
                category=TestCategory.OBJECTIVES,
                description="StateEqualityObjective for system state evaluation",
                estimated_time=20,
                requires_env=False
            ),
            
            # Integration Tests
            TestFile(
                name="LLM Judge + LangChain",
                file_path="test_llm_judge_objective_real_langchain.py",
                category=TestCategory.INTEGRATIONS,
                description="LLM Judge with LangChain integration",
                estimated_time=60,
                requires_env=True,
                requires_internet=True,
                is_slow=True
            ),
            TestFile(
                name="LLM Judge + Pydantic AI",
                file_path="test_llm_judge_objective_real_pydantic_ai.py",
                category=TestCategory.INTEGRATIONS,
                description="LLM Judge with Pydantic AI integration", 
                estimated_time=50,
                requires_env=True,
                requires_internet=True,
                is_slow=True
            ),
            TestFile(
                name="Diet Schedule LLM Judge",
                file_path="test_diet_schedule_llm_judge.py",
                category=TestCategory.INTEGRATIONS,
                description="Specialized diet schedule evaluation with LLM",
                estimated_time=35,
                requires_env=True,
                requires_internet=True,
                is_slow=True
            ),
            
            # Logging Tests
            TestFile(
                name="OmniBarmarker Logging",
                file_path="test_omnibarmarker_logging.py",
                category=TestCategory.LOGGING,
                description="Comprehensive logging and analytics",
                estimated_time=25,
                requires_env=False
            ),
            TestFile(
                name="OmniBarmarker Logging Integration",
                file_path="test_omnibarmarker_logging_integration.py",
                category=TestCategory.LOGGING,
                description="Integration test for logging with real benchmarker",
                estimated_time=15,
                requires_env=False
            ),
            TestFile(
                name="Auto Evaluators",
                file_path="test_auto_evaluators.py",
                category=TestCategory.LOGGING,
                description="Automated evaluation and analysis systems",
                estimated_time=30,
                requires_env=True,
                requires_internet=True
            ),
            TestFile(
                name="Auto Evaluator Examples",
                file_path="test_auto_evaluator.py",
                category=TestCategory.LOGGING,
                description="Auto-evaluator assignment and usage examples",
                estimated_time=10,
                requires_env=False
            ),
            TestFile(
                name="Logger Core Components",
                file_path="test_logger.py",
                category=TestCategory.LOGGING,
                description="Comprehensive test suite for BenchmarkLogger and related classes",
                estimated_time=20,
                requires_env=False
            ),
        ]
    
    def print(self, *args, style=None, **kwargs):
        """Print with rich formatting if available."""
        if self.console:
            self.console.print(*args, style=style, **kwargs)
        else:
            print(*args, **kwargs)
    
    def get_tests_by_category(self, category: TestCategory) -> List[TestFile]:
        """Get test files filtered by category."""
        if category == TestCategory.ALL:
            return self.test_files
        return [t for t in self.test_files if t.category == category]
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if required dependencies and environment are available."""
        checks = {}
        
        # Check for .env file
        env_file = self.test_dir.parent / '.env'
        checks['env_file'] = env_file.exists()
        
        # Check for required environment variables
        required_env_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        for var in required_env_vars:
            checks[f'env_{var}'] = os.getenv(var) is not None
            
        # Check for optional dependencies
        optional_deps = ['rich', 'dotenv', 'langchain', 'pydantic_ai']
        for dep in optional_deps:
            try:
                __import__(dep)
                checks[f'dep_{dep}'] = True
            except ImportError:
                checks[f'dep_{dep}'] = False
        
        return checks
    
    def print_prerequisites_report(self, checks: Dict[str, bool]):
        """Print a detailed prerequisites report."""
        if RICH_AVAILABLE:
            table = Table(title="Prerequisites Check", show_header=True)
            table.add_column("Component", style="cyan", width=25)
            table.add_column("Status", justify="center", width=10) 
            table.add_column("Description", style="dim")
            
            # Environment checks
            table.add_row(
                ".env file",
                "✅" if checks.get('env_file') else "❌",
                "Configuration file with API keys"
            )
            
            table.add_row(
                "OPENAI_API_KEY", 
                "✅" if checks.get('env_OPENAI_API_KEY') else "❌",
                "Required for LLM Judge objectives"
            )
            
            table.add_row(
                "ANTHROPIC_API_KEY",
                "✅" if checks.get('env_ANTHROPIC_API_KEY') else "❌", 
                "Alternative LLM provider for testing"
            )
            
            # Dependencies
            deps_info = {
                'rich': 'Beautiful terminal output',
                'dotenv': 'Environment variable loading',
                'langchain': 'LangChain integration tests',
                'pydantic_ai': 'Pydantic AI integration tests'
            }
            
            for dep, desc in deps_info.items():
                table.add_row(
                    f"{dep} (optional)",
                    "✅" if checks.get(f'dep_{dep}') else "⚠️",
                    desc
                )
            
            self.console.print(table)
        else:
            print("\n📋 Prerequisites Check:")
            print("=" * 50)
            for key, status in checks.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {key}")
    
    async def run_test_file(self, test_file: TestFile, timeout: int = 300) -> TestResult:
        """Run a single test file and return results."""
        start_time = time.time()
        test_path = self.test_dir / test_file.file_path
        
        if not test_path.exists():
            return TestResult(
                test_file=test_file,
                status=TestStatus.ERROR,
                duration=0.0,
                output="",
                error_output=f"Test file not found: {test_path}",
                exit_code=-1,
                details="File missing"
            )
        
        try:
            # Run test file as subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(test_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.test_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                exit_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return TestResult(
                    test_file=test_file,
                    status=TestStatus.TIMEOUT,
                    duration=timeout,
                    output="",
                    error_output=f"Test timed out after {timeout}s",
                    exit_code=-1,
                    details=f"Timeout ({timeout}s)"
                )
            
            duration = time.time() - start_time
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Determine status based on exit code and output
            if exit_code == 0:
                status = TestStatus.PASS
                details = "Success"
            else:
                status = TestStatus.FAIL
                details = f"Exit code: {exit_code}"
                
                # Look for specific error indicators
                if "ImportError" in stderr_str:
                    details = "Import Error"
                elif "AssertionError" in stderr_str:
                    details = "Assertion Failed"
                elif "ConnectionError" in stderr_str or "requests.exceptions" in stderr_str:
                    details = "Network Error"
                elif "API" in stderr_str and "key" in stderr_str.lower():
                    details = "API Key Error"
            
            return TestResult(
                test_file=test_file,
                status=status,
                duration=duration,
                output=stdout_str,
                error_output=stderr_str,
                exit_code=exit_code,
                details=details
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_file=test_file,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error_output=str(e),
                exit_code=-1,
                details=f"Exception: {type(e).__name__}"
            )
    
    async def run_tests(self, 
                       category: TestCategory = TestCategory.ALL,
                       fast_only: bool = False,
                       max_concurrent: int = 3) -> List[TestResult]:
        """Run tests with specified filters."""
        
        # Filter tests
        tests_to_run = self.get_tests_by_category(category)
        
        if fast_only:
            tests_to_run = [t for t in tests_to_run if not t.is_slow]
        
        if not tests_to_run:
            self.print("❌ No tests match the specified criteria", style="red")
            return []
        
        # Print test plan
        self.print_test_plan(tests_to_run)
        
        # Run tests with concurrency control
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                
                task = progress.add_task("Running tests...", total=len(tests_to_run))
                
                # Control concurrency to avoid overwhelming the system
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def run_with_semaphore(test_file):
                    async with semaphore:
                        result = await self.run_test_file(test_file)
                        progress.advance(task)
                        
                        # Update progress description
                        progress.update(task, description=f"Running {result.test_file.name}...")
                        
                        return result
                
                # Run all tests concurrently (but limited by semaphore)
                results = await asyncio.gather(
                    *[run_with_semaphore(test) for test in tests_to_run],
                    return_exceptions=True
                )
                
                # Handle any exceptions that occurred
                final_results = []
                for result in results:
                    if isinstance(result, Exception):
                        # Create error result for the exception
                        final_results.append(TestResult(
                            test_file=TestFile("Unknown", "unknown", TestCategory.ALL, "Error", 0),
                            status=TestStatus.ERROR,
                            duration=0.0,
                            output="",
                            error_output=str(result),
                            exit_code=-1,
                            details="Exception during execution"
                        ))
                    else:
                        final_results.append(result)
                
                self.results = final_results
        else:
            # Fallback without rich progress
            self.print(f"🚀 Running {len(tests_to_run)} tests...")
            results = []
            for i, test in enumerate(tests_to_run, 1):
                self.print(f"[{i}/{len(tests_to_run)}] Running {test.name}...")
                result = await self.run_test_file(test)
                results.append(result)
                self.print(f"  {result.status.value} {test.name}")
            
            self.results = results
        
        return self.results
    
    def print_test_plan(self, tests: List[TestFile]):
        """Print the test execution plan."""
        if RICH_AVAILABLE:
            tree = Tree("🧪 Test Execution Plan")
            
            # Group by category
            by_category = defaultdict(list)
            for test in tests:
                by_category[test.category].append(test)
            
            total_time = sum(t.estimated_time for t in tests)
            
            for category, category_tests in by_category.items():
                category_node = tree.add(f"📁 {category.value.title()}")
                category_time = sum(t.estimated_time for t in category_tests)
                
                for test in category_tests:
                    test_info = f"{test.name}"
                    if test.requires_env:
                        test_info += " 🔑"
                    if test.requires_internet:
                        test_info += " 🌐"
                    if test.is_slow:
                        test_info += " 🐌"
                    
                    test_info += f" ({test.estimated_time}s)"
                    category_node.add(test_info)
                
                category_node.label += f" ({len(category_tests)} tests, ~{category_time}s)"
            
            tree.label += f" ({len(tests)} tests, ~{total_time}s)"
            self.console.print(Panel(tree, title="Test Plan", border_style="blue"))
        else:
            print(f"\n🧪 Test Plan: {len(tests)} tests")
            for test in tests:
                flags = ""
                if test.requires_env:
                    flags += " [ENV]"
                if test.requires_internet: 
                    flags += " [NET]"
                if test.is_slow:
                    flags += " [SLOW]"
                print(f"  - {test.name} (~{test.estimated_time}s){flags}")
    
    def print_detailed_results(self):
        """Print comprehensive test results."""
        if not self.results:
            self.print("❌ No test results to display", style="red")
            return
        
        # Calculate statistics
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == TestStatus.PASS])
        failed = len([r for r in self.results if r.status == TestStatus.FAIL])
        errors = len([r for r in self.results if r.status == TestStatus.ERROR])
        timeouts = len([r for r in self.results if r.status == TestStatus.TIMEOUT])
        total_time = sum(r.duration for r in self.results)
        
        if RICH_AVAILABLE:
            # Summary statistics
            summary_table = Table(title="📊 Test Results Summary", show_header=True)
            summary_table.add_column("Metric", style="cyan", width=20)
            summary_table.add_column("Value", justify="right", style="bold", width=10)
            summary_table.add_column("Percentage", justify="right", style="dim", width=12)
            
            summary_table.add_row("Total Tests", str(total_tests), "100.0%")
            summary_table.add_row("✅ Passed", str(passed), f"{passed/total_tests*100:.1f}%")
            summary_table.add_row("❌ Failed", str(failed), f"{failed/total_tests*100:.1f}%")
            summary_table.add_row("💥 Errors", str(errors), f"{errors/total_tests*100:.1f}%")
            summary_table.add_row("⏰ Timeouts", str(timeouts), f"{timeouts/total_tests*100:.1f}%")
            summary_table.add_row("Total Time", f"{total_time:.1f}s", "-")
            
            self.console.print(summary_table)
            
            # Detailed results table
            results_table = Table(title="🔍 Detailed Results", show_header=True)
            results_table.add_column("Status", width=6, justify="center")
            results_table.add_column("Test Name", style="cyan", width=30)
            results_table.add_column("Category", style="dim", width=12)
            results_table.add_column("Duration", justify="right", width=8)
            results_table.add_column("Details", style="dim", width=20)
            
            for result in self.results:
                duration_str = f"{result.duration:.1f}s"
                results_table.add_row(
                    result.status.value,
                    result.test_file.name,
                    result.test_file.category.value,
                    duration_str,
                    result.details
                )
            
            self.console.print(results_table)
            
            # Show failures and errors in detail
            failures = [r for r in self.results if r.status in [TestStatus.FAIL, TestStatus.ERROR]]
            if failures and self.verbose:
                self.console.print("\n🚨 Failure Details", style="red bold")
                for failure in failures:
                    panel_title = f"{failure.status.value} {failure.test_file.name}"
                    error_content = failure.error_output.strip() if failure.error_output else "No error output"
                    
                    # Truncate very long error messages
                    if len(error_content) > 1000:
                        error_content = error_content[:1000] + "\n... (truncated)"
                    
                    self.console.print(Panel(
                        error_content,
                        title=panel_title,
                        border_style="red"
                    ))
        else:
            # Fallback without rich
            print(f"\n📊 Test Results Summary:")
            print(f"Total Tests: {total_tests}")
            print(f"✅ Passed: {passed} ({passed/total_tests*100:.1f}%)")
            print(f"❌ Failed: {failed} ({failed/total_tests*100:.1f}%)")
            print(f"💥 Errors: {errors} ({errors/total_tests*100:.1f}%)")
            print(f"⏰ Timeouts: {timeouts} ({timeouts/total_tests*100:.1f}%)")
            print(f"Total Time: {total_time:.1f}s")
            
            print(f"\n🔍 Detailed Results:")
            for result in self.results:
                print(f"{result.status.value} {result.test_file.name} ({result.duration:.1f}s) - {result.details}")
    
    def get_exit_code(self) -> int:
        """Get appropriate exit code based on test results."""
        if not self.results:
            return 1  # No tests run
        
        failed_tests = [r for r in self.results if r.status != TestStatus.PASS]
        return 0 if not failed_tests else 1
    
    def list_available_tests(self):
        """List all available tests organized by category."""
        if RICH_AVAILABLE:
            tree = Tree("📋 Available Tests")
            
            by_category = defaultdict(list)
            for test in self.test_files:
                by_category[test.category].append(test)
            
            for category, tests in by_category.items():
                category_node = tree.add(f"📁 {category.value.title()} ({len(tests)} tests)")
                
                for test in tests:
                    test_info = f"{test.name} - {test.description}"
                    flags = []
                    if test.requires_env:
                        flags.append("🔑 ENV")
                    if test.requires_internet:
                        flags.append("🌐 NET") 
                    if test.is_slow:
                        flags.append("🐌 SLOW")
                    
                    if flags:
                        test_info += f" [{', '.join(flags)}]"
                    
                    test_info += f" (~{test.estimated_time}s)"
                    category_node.add(test_info)
            
            self.console.print(tree)
        else:
            print("📋 Available Tests:")
            by_category = defaultdict(list)
            for test in self.test_files:
                by_category[test.category].append(test)
            
            for category, tests in by_category.items():
                print(f"\n📁 {category.value.title()}:")
                for test in tests:
                    flags = []
                    if test.requires_env:
                        flags.append("ENV")
                    if test.requires_internet:
                        flags.append("NET")
                    if test.is_slow:
                        flags.append("SLOW")
                    
                    flag_str = f" [{', '.join(flags)}]" if flags else ""
                    print(f"  - {test.name}: {test.description}{flag_str} (~{test.estimated_time}s)")


async def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="OmniBAR Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_all.py                    # Run all tests
  python test_all.py --category core    # Run only core tests  
  python test_all.py --fast             # Skip slow integration tests
  python test_all.py --verbose          # Show detailed failure information
  python test_all.py --list             # List all available tests
        """
    )
    
    parser.add_argument(
        "--category", 
        choices=[c.value for c in TestCategory],
        default=TestCategory.ALL.value,
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true", 
        help="Run only fast tests (skip slow integration tests)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including failure details"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tests and exit"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum number of concurrent test processes (default: 3)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    # Create test suite
    suite = OmniBarTestSuite(verbose=args.verbose)
    
    # Print header
    if RICH_AVAILABLE:
        header = Panel.fit(
            "[bold cyan]🧪 OmniBAR Comprehensive Test Suite[/bold cyan]\n"
            "[dim]Testing the entire package functionality[/dim]",
            border_style="cyan"
        )
        suite.console.print(header)
    else:
        print("🧪 OmniBAR Comprehensive Test Suite")
        print("=" * 50)
    
    # Handle list command
    if args.list:
        suite.list_available_tests()
        return 0
    
    # Check prerequisites
    checks = suite.check_prerequisites()
    suite.print_prerequisites_report(checks)
    
    # Warn about missing prerequisites
    missing_env = not checks.get('env_file', False) or not checks.get('env_OPENAI_API_KEY', False)
    if missing_env:
        suite.print("⚠️ Some tests may fail due to missing API keys or .env file", style="yellow")
    
    # Convert category string back to enum
    category = TestCategory(args.category)
    
    # Run tests
    suite.print(f"\n🚀 Starting test execution...")
    start_time = time.time()
    
    try:
        results = await suite.run_tests(
            category=category,
            fast_only=args.fast,
            max_concurrent=args.max_concurrent
        )
        
        execution_time = time.time() - start_time
        
        # Print results
        suite.print(f"\n⏱️ Test execution completed in {execution_time:.1f}s")
        suite.print_detailed_results()
        
        # Print final summary
        if results:
            passed = len([r for r in results if r.status == TestStatus.PASS])
            total = len(results)
            
            if passed == total:
                suite.print(f"\n🎉 All tests passed! ({passed}/{total})", style="green bold")
            else:
                failed = total - passed
                suite.print(f"\n⚠️ {failed} test(s) failed out of {total}", style="red bold")
                
                if not args.verbose:
                    suite.print("💡 Run with --verbose to see detailed failure information", style="dim")
        
        return suite.get_exit_code()
        
    except KeyboardInterrupt:
        suite.print("\n⏹️ Test execution interrupted by user", style="yellow")
        return 130
    except Exception as e:
        suite.print(f"\n💥 Unexpected error during test execution: {e}", style="red bold")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Ensure we're running in the correct directory
    os.chdir(Path(__file__).parent)
    
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
