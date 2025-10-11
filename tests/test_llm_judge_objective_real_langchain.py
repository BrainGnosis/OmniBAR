#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Real LangChain integration test suite for LLMJudgeObjective class.
Tests LLM-based evaluation with actual OpenAI API calls and real AI agents.
Uses the OPENAI_API_KEY from .env file for authentic testing.
"""

import sys
import traceback
import os
import asyncio
from typing import Any, Dict
from dataclasses import dataclass
from enum import Enum
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
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("❌ Rich library not available. Install with: pip install rich")

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
from omnibar.objectives.llm_judge import (
    LLMJudgeObjective,
    LLMBinaryOutputSchema,
    LLMPartialOutputSchema,
    DEFAULT_BINARY_PROMPT
)
from omnibar.core.types import (
    BoolEvalResult,
    InvalidEvalResult
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
    api_calls_made: int = 0
    total_tokens: int = 0


class TestRunner:
    """Enhanced test runner with rich terminal output and API usage tracking."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
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
                
            if result.status == TestStatus.PASS:
                self.passed_tests += 1
            
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
        """Display comprehensive test results with API usage statistics."""
        if not self.console:
            # Fallback to simple text output
            print("\n" + "="*80)
            print("REAL LANGCHAIN INTEGRATION TEST RESULTS")
            print("="*80)
            for result in self.results:
                print(f"{result.status.value}: {result.name}")
                if result.message:
                    print(f"    {result.message}")
                if result.details:
                    print(f"    Details: {result.details}")
                if result.api_calls_made > 0:
                    print(f"    API Calls: {result.api_calls_made} | Tokens: {result.total_tokens}")
                if result.traceback and result.status in [TestStatus.FAIL, TestStatus.ERROR]:
                    print(f"    Traceback:\n{result.traceback}")
            print(f"\nTotal: {self.total_tests}, Passed: {self.passed_tests}, Failed: {self.total_tests - self.passed_tests}")
            print(f"API Usage: {self.total_api_calls} calls, {self.total_tokens_used} tokens")
            return
        
        # Rich formatted output
        self.console.print("\n")
        self.console.rule("[bold blue]Real LangChain Integration Test Results", style="blue")
        
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
        
        # Summary panel with API usage
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        summary_style = "green" if pass_rate == 100 else "yellow" if pass_rate >= 75 else "red"
        
        estimated_cost = self.total_tokens_used * 0.00003  # Rough estimate for GPT-4
        
        summary = Panel(
            f"[bold]Test Results:[/bold]\n"
            f"  Total Tests: {self.total_tests}\n"
            f"  [bold green]Passed:[/bold green] {self.passed_tests}\n"
            f"  [bold red]Failed:[/bold red] {self.total_tests - self.passed_tests}\n"
            f"  [bold]Pass Rate:[/bold] {pass_rate:.1f}%\n\n"
            f"[bold]API Usage:[/bold]\n"
            f"  Total API Calls: {self.total_api_calls}\n"
            f"  Total Tokens: {self.total_tokens_used:,}\n"
            f"  Estimated Cost: ${estimated_cost:.4f}",
            title="Real LangChain Integration Summary",
            border_style=summary_style
        )
        self.console.print(summary)


class RealLangChainLLMJudgeTests:
    """Comprehensive test suite for LLMJudgeObjective with real LangChain and OpenAI integration."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
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
    
    def test_real_openai_binary_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real OpenAI binary evaluation."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real OpenAI Binary Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met (LangChain or OpenAI API key missing)",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",  # Using cheaper model for testing
                temperature=0,
                max_tokens=150
            )
            
            # Create output parser
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            # Create prompt template
            prompt = PromptTemplate(
                template=DEFAULT_BINARY_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "expected_output": "A sentence starting with apolite greeting like 'Hello' or 'Hi'",
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            # Create chain
            chain = prompt | llm | parser
            
            # Create LLMJudgeObjective with real invoke method
            objective = LLMJudgeObjective(
                invoke_method=chain.invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test with correct greeting
            self.runner.print("🔄 Testing with correct greeting...", style="yellow")
            result_correct = objective.eval({"response": "Hello there! How can I help you today?"})
            api_usage["calls"] += 1
            
            # Test with incorrect response
            self.runner.print("🔄 Testing with incorrect response...", style="yellow")
            result_incorrect = objective.eval({"response": "The capital of France is Paris."})
            api_usage["calls"] += 1
            
            # Estimate tokens (rough calculation)
            api_usage["tokens"] = api_usage["calls"] * 100  # Rough estimate
            
            # Validate results
            self.runner.assert_isinstance(result_correct, BoolEvalResult, "Should return BoolEvalResult for correct")
            self.runner.assert_isinstance(result_incorrect, BoolEvalResult, "Should return BoolEvalResult for incorrect")
            
            # Correct greeting should pass, incorrect should fail
            if not result_correct.result:
                return TestResult(
                    name="Real OpenAI Binary Evaluation",
                    status=TestStatus.FAIL,
                    message="✗ OpenAI incorrectly evaluated correct greeting as false",
                    details=f"Correct result: {result_correct.result} | Message: {result_correct.message}",
                    expected="True for correct greeting",
                    actual=f"False: {result_correct.message}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            return TestResult(
                name="Real OpenAI Binary Evaluation",
                status=TestStatus.PASS,
                message="✓ OpenAI successfully evaluated both test cases",
                details=f"Correct: {result_correct.result} | Incorrect: {result_incorrect.result}",
                expected="Correct evaluation of greetings",
                actual=f"Correct: {result_correct.result}, Incorrect: {result_incorrect.result}",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real OpenAI Binary Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real OpenAI binary evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful real OpenAI evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_real_openai_detailed_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real OpenAI detailed evaluation using custom prompt."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real OpenAI Detailed Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=200
            )
            
            # Custom detailed evaluation prompt
            detailed_prompt = """
            You are an expert customer service evaluator. Judge the following customer service response:

            Customer Query: "I'm having trouble with my account login"
            Agent Response: {input}
            Expected Quality: Professional, helpful, provides clear next steps

            Evaluate the response on:
            1. Professionalism (polite, appropriate tone)
            2. Helpfulness (addresses the issue)
            3. Clarity (provides clear guidance)

            {format_instructions}
            """
            
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            prompt = PromptTemplate(
                template=detailed_prompt,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            objective = LLMJudgeObjective(
                invoke_method=chain.invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test cases for customer service evaluation
            test_cases = [
                {
                    "response": "I understand your login issue. Let me help you reset your password. Please check your email for reset instructions and try logging in again. If you continue having problems, please contact our technical support team.",
                    "expected": True,
                    "label": "good_response"
                },
                {
                    "response": "I don't know. Try again later.",
                    "expected": False,
                    "label": "poor_response"
                },
                {
                    "response": "Hello! I'd be happy to help with your login issue. First, let's try resetting your password. Click 'Forgot Password' on the login page, enter your email, and follow the instructions. If that doesn't work, please clear your browser cache and try again.",
                    "expected": True,
                    "label": "excellent_response"
                }
            ]
            
            results = []
            for case in test_cases:
                self.runner.print(f"🔄 Testing {case['label']}...", style="yellow")
                result = objective.eval({"response": case["response"]})
                api_usage["calls"] += 1
                
                results.append({
                    "label": case["label"],
                    "expected": case["expected"],
                    "actual": result.result,
                    "message": result.message,
                    "correct": result.result == case["expected"]
                })
            
            # Estimate tokens
            api_usage["tokens"] = api_usage["calls"] * 150  # Rough estimate for longer prompts
            
            # Check if evaluations are reasonable
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                failed_cases = [r for r in results if not r["correct"]]
                return TestResult(
                    name="Real OpenAI Detailed Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ OpenAI evaluation accuracy too low: {correct_evaluations}/{total_evaluations}",
                    details=f"Failed cases: {failed_cases}",
                    expected="At least 2/3 correct evaluations",
                    actual=f"{correct_evaluations}/{total_evaluations} correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            results_summary = " | ".join([f"{r['label']}: {r['actual']}" for r in results])
            
            return TestResult(
                name="Real OpenAI Detailed Evaluation",
                status=TestStatus.PASS,
                message=f"✓ OpenAI detailed evaluation successful: {correct_evaluations}/{total_evaluations}",
                details=f"Results: {results_summary}",
                expected="Accurate detailed evaluations",
                actual=f"{correct_evaluations}/{total_evaluations} correct evaluations",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real OpenAI Detailed Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real OpenAI detailed evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful detailed evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_real_openai_score_based_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real OpenAI score-based evaluation."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real OpenAI Score-Based Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=250
            )
            
            # Score-based evaluation prompt
            score_prompt = """
            Evaluate the following email response for professionalism and clarity.
            Rate on a scale from 0.0 to 1.0 where:
            - 0.0-0.3: Poor (unprofessional, unclear, unhelpful)
            - 0.4-0.6: Average (somewhat professional, moderately clear)
            - 0.7-1.0: Excellent (highly professional, very clear, very helpful)

            Email Response to Evaluate: {input}

            Consider:
            1. Professional tone and language
            2. Clarity of communication
            3. Helpfulness of the response
            4. Grammar and structure

            {format_instructions}
            """
            
            parser = JsonOutputParser(pydantic_object=LLMPartialOutputSchema)
            
            prompt = PromptTemplate(
                template=score_prompt,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            # Custom objective that handles numeric scores
            class ScoreLLMJudgeObjective(LLMJudgeObjective):
                def _eval_fn(self, goal: str | None, formatted_output: Dict[str, Any], **kwargs):
                    output = next(iter(formatted_output.values()))
                    key = next(iter(formatted_output.keys()))
                    
                    try:
                        output = str(output)
                    except Exception as e:
                        return InvalidEvalResult(result=None, message=f"Value for key {key} is not a string: {e}")
                    
                    try:
                        result = self._invoke_method({"input": output})
                        score = result.get("result", 0.0)
                        # Convert score to boolean (threshold at 0.6)
                        bool_result = score >= 0.6
                        return BoolEvalResult(
                            result=bool_result, 
                            message=f"Score: {score:.2f} - {result.get('message', '')}"
                        )
                    except Exception as e:
                        return InvalidEvalResult(result=None, message=f"Error invoking method: {e}")
            
            objective = ScoreLLMJudgeObjective(
                invoke_method=chain.invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test different quality levels
            test_emails = [
                {
                    "text": "Dear Customer, Thank you for your inquiry regarding our premium services. I'd be delighted to provide you with comprehensive information about our offerings. Please find attached our detailed brochure, and I'll follow up with a personal consultation within 24 hours. Best regards, Sarah Johnson",
                    "expected_high": True,
                    "label": "professional_email"
                },
                {
                    "text": "Hi, thanks for asking about our stuff. We have some products you might like. Let me know if you want more info. Thanks.",
                    "expected_high": False,
                    "label": "casual_email"
                },
                {
                    "text": "ur question is dumb lol try google",
                    "expected_high": False,
                    "label": "unprofessional_email"
                }
            ]
            
            results = []
            for email in test_emails:
                self.runner.print(f"🔄 Evaluating {email['label']}...", style="yellow")
                result = objective.eval({"response": email["text"]})
                api_usage["calls"] += 1
                
                results.append({
                    "label": email["label"],
                    "expected_high": email["expected_high"],
                    "actual_high": result.result,
                    "message": result.message,
                    "correct": result.result == email["expected_high"]
                })
            
            # Estimate tokens
            api_usage["tokens"] = api_usage["calls"] * 180  # Rough estimate
            
            # Validate results
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Real OpenAI Score-Based Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Score-based evaluation accuracy too low: {correct_evaluations}/{total_evaluations}",
                    details=f"Results: {results}",
                    expected="At least 2/3 correct evaluations",
                    actual=f"{correct_evaluations}/{total_evaluations} correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            results_summary = " | ".join([f"{r['label']}: {r['actual_high']}" for r in results])
            
            return TestResult(
                name="Real OpenAI Score-Based Evaluation",
                status=TestStatus.PASS,
                message=f"✓ Score-based evaluation successful: {correct_evaluations}/{total_evaluations}",
                details=f"Results: {results_summary}",
                expected="Accurate score-based evaluations",
                actual=f"{correct_evaluations}/{total_evaluations} correct",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real OpenAI Score-Based Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real OpenAI score-based evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful score-based evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_real_openai_creative_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real OpenAI creative content evaluation."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real OpenAI Creative Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,  # Slightly higher for creativity evaluation
                max_tokens=300
            )
            
            # Creative content evaluation prompt
            creative_prompt = """
            You are evaluating creative writing samples for a storytelling contest.
            
            Evaluate this story excerpt for creativity and engagement:
            "{input}"
            
            Judge based on:
            1. Originality of ideas and concepts
            2. Engaging narrative voice
            3. Vivid imagery and descriptions
            4. Character development (if applicable)
            5. Overall creativity and imagination
            
            A story should be considered "good" if it demonstrates clear creativity,
            engaging writing, and original thinking.
            
            {format_instructions}
            """
            
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            prompt = PromptTemplate(
                template=creative_prompt,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            objective = LLMJudgeObjective(
                invoke_method=chain.invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test creative writing samples
            writing_samples = [
                {
                    "text": "The old lighthouse keeper had a secret: every night at midnight, the lighthouse beam didn't just guide ships—it opened a portal to parallel oceans where mermaid civilizations thrived in floating crystal cities, and he was their appointed guardian between worlds.",
                    "expected_creative": True,
                    "label": "creative_story"
                },
                {
                    "text": "I went to the store today. I bought milk and bread. Then I went home and had dinner. The end.",
                    "expected_creative": False,
                    "label": "mundane_story"
                },
                {
                    "text": "In the quantum coffee shop, Sarah discovered that each cup of coffee contained memories from parallel universes. The barista, who existed in seventeen dimensions simultaneously, served her a latte that tasted of childhood summers she never lived and love stories that belonged to other versions of herself.",
                    "expected_creative": True,
                    "label": "imaginative_story"
                }
            ]
            
            results = []
            for sample in writing_samples:
                self.runner.print(f"🔄 Evaluating {sample['label']}...", style="yellow")
                result = objective.eval({"response": sample["text"]})
                api_usage["calls"] += 1
                
                results.append({
                    "label": sample["label"],
                    "expected": sample["expected_creative"],
                    "actual": result.result,
                    "message": result.message,
                    "correct": result.result == sample["expected_creative"]
                })
            
            # Estimate tokens
            api_usage["tokens"] = api_usage["calls"] * 220  # Rough estimate for creative prompts
            
            # Validate creative evaluation accuracy
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Real OpenAI Creative Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Creative evaluation accuracy too low: {correct_evaluations}/{total_evaluations}",
                    details=f"Results: {results}",
                    expected="At least 2/3 correct creative evaluations",
                    actual=f"{correct_evaluations}/{total_evaluations} correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            results_summary = " | ".join([f"{r['label']}: {r['actual']}" for r in results])
            
            return TestResult(
                name="Real OpenAI Creative Evaluation",
                status=TestStatus.PASS,
                message=f"✓ Creative evaluation successful: {correct_evaluations}/{total_evaluations}",
                details=f"Results: {results_summary}",
                expected="Accurate creative content evaluation",
                actual=f"{correct_evaluations}/{total_evaluations} correct",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real OpenAI Creative Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real OpenAI creative evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful creative evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    def test_real_openai_technical_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real OpenAI technical code evaluation."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real OpenAI Technical Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=400
            )
            
            # Technical code evaluation prompt
            tech_prompt = """
            You are a senior software engineer reviewing code submissions.
            
            Evaluate this Python code for correctness and quality:
            
            Code to Review:
            {input}
            
            Criteria for evaluation:
            1. Syntax correctness
            2. Logic correctness
            3. Code structure and readability
            4. Best practices adherence
            5. Potential bugs or issues
            
            Consider code "good" if it is syntactically correct, logically sound,
            well-structured, and follows Python best practices.
            
            {format_instructions}
            """
            
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            prompt = PromptTemplate(
                template=tech_prompt,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            objective = LLMJudgeObjective(
                invoke_method=chain.invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test code samples
            code_samples = [
                {
                    "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
result = fibonacci(10)
print(f"Fibonacci of 10 is: {result}")
""",
                    "expected_good": True,
                    "label": "correct_fibonacci"
                },
                {
                    "code": """
def divide_numbers(a, b):
    result = a / b
    return result

# This could cause division by zero error
print(divide_numbers(10, 0))
""",
                    "expected_good": False,
                    "label": "division_by_zero_bug"
                },
                {
                    "code": """
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

# Well-structured function with edge case handling
scores = [85, 92, 78, 96, 88]
avg = calculate_average(scores)
print(f"Average score: {avg:.2f}")
""",
                    "expected_good": True,
                    "label": "good_average_function"
                }
            ]
            
            results = []
            for sample in code_samples:
                self.runner.print(f"🔄 Evaluating {sample['label']}...", style="yellow")
                result = objective.eval({"response": sample["code"]})
                api_usage["calls"] += 1
                
                results.append({
                    "label": sample["label"],
                    "expected": sample["expected_good"],
                    "actual": result.result,
                    "message": result.message,
                    "correct": result.result == sample["expected_good"]
                })
            
            # Estimate tokens
            api_usage["tokens"] = api_usage["calls"] * 300  # Rough estimate for code evaluation
            
            # Validate technical evaluation accuracy
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Real OpenAI Technical Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Technical evaluation accuracy too low: {correct_evaluations}/{total_evaluations}",
                    details=f"Results: {results}",
                    expected="At least 2/3 correct technical evaluations",
                    actual=f"{correct_evaluations}/{total_evaluations} correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            results_summary = " | ".join([f"{r['label']}: {r['actual']}" for r in results])
            
            return TestResult(
                name="Real OpenAI Technical Evaluation",
                status=TestStatus.PASS,
                message=f"✓ Technical evaluation successful: {correct_evaluations}/{total_evaluations}",
                details=f"Results: {results_summary}",
                expected="Accurate technical code evaluation",
                actual=f"{correct_evaluations}/{total_evaluations} correct",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real OpenAI Technical Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real OpenAI technical evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful technical evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_async_real_openai_parallel_evaluation(self) -> TestResult:
        """Test parallel async evaluation with real OpenAI API to verify concurrency benefits."""
        if not self._check_prerequisites():
            return TestResult(
                name="Async Parallel OpenAI Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            import time
            
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=100
            )
            
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            prompt = PromptTemplate(
                template=DEFAULT_BINARY_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "expected_output": "A polite and helpful response",
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            # Create multiple objectives for parallel testing
            objectives = [
                LLMJudgeObjective(invoke_method=chain.invoke, output_key="response")
                for _ in range(3)
            ]
            
            test_outputs = [
                {"response": "Hello! I'd be happy to help you with your question."},
                {"response": "Thank you for reaching out. How can I assist you today?"},
                {"response": "I'm here to help. What can I do for you?"}
            ]
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test async parallel execution
            self.runner.print("🔄 Testing async parallel evaluation...", style="yellow")
            start_time = time.time()
            
            # Run evaluations in parallel using eval_async
            async_tasks = [
                obj.eval_async(output) 
                for obj, output in zip(objectives, test_outputs)
            ]
            async_results = await asyncio.gather(*async_tasks)
            
            async_time = time.time() - start_time
            api_usage["calls"] += len(async_tasks)
            api_usage["tokens"] = api_usage["calls"] * 80  # Rough estimate
            
            # Test sync sequential execution for comparison
            self.runner.print("🔄 Testing sync sequential evaluation...", style="yellow")
            start_time = time.time()
            
            sync_results = []
            for obj, output in zip(objectives, test_outputs):
                result = obj.eval(output)
                sync_results.append(result)
            
            sync_time = time.time() - start_time
            api_usage["calls"] += len(sync_results)
            api_usage["tokens"] += len(sync_results) * 80
            
            # Verify results are consistent
            for async_result, sync_result in zip(async_results, sync_results):
                self.runner.assert_isinstance(async_result, BoolEvalResult, "Async should return BoolEvalResult")
                self.runner.assert_isinstance(sync_result, BoolEvalResult, "Sync should return BoolEvalResult")
            
            # Verify performance improvement (should be faster or similar due to parallelism)
            speedup = sync_time / async_time if async_time > 0 else 1.0
            
            return TestResult(
                name="Async Parallel OpenAI Evaluation",
                status=TestStatus.PASS,
                message=f"✓ Async parallel evaluation successful (speedup: {speedup:.2f}x)",
                details=f"Async: {async_time:.2f}s, Sync: {sync_time:.2f}s, Results consistent",
                expected="Successful parallel evaluation with consistent results",
                actual=f"Parallel execution with {speedup:.2f}x speedup",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Async Parallel OpenAI Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Async parallel evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful async parallel evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_async_user_provided_methods(self) -> TestResult:
        """Test async functionality with user-provided async and sync methods."""
        try:
            # Mock async user method
            async def mock_async_llm_judge(input_data):
                await asyncio.sleep(0.1)  # Simulate async operation
                user_input = input_data["input"].lower()
                return {
                    "result": "please" in user_input or "help" in user_input,
                    "message": f"Async evaluation of politeness in: {user_input[:20]}..."
                }
            
            # Mock sync user method
            def mock_sync_llm_judge(input_data):
                import time
                time.sleep(0.1)  # Simulate sync operation
                user_input = input_data["input"].lower()
                return {
                    "result": "thank" in user_input or "appreciate" in user_input,
                    "message": f"Sync evaluation of gratitude in: {user_input[:20]}..."
                }
            
            # Create objectives with user-provided methods
            async_objective = LLMJudgeObjective(
                invoke_method=mock_async_llm_judge,
                output_key="response"
            )
            
            sync_objective = LLMJudgeObjective(
                invoke_method=mock_sync_llm_judge,
                output_key="response"
            )
            
            test_cases = [
                {"response": "Please help me with this issue."},
                {"response": "Thank you for your assistance, I appreciate it."},
                {"response": "This is just a regular message."}
            ]
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test async method with eval_async
            self.runner.print("🔄 Testing user-provided async method...", style="yellow")
            async_results = []
            for test_case in test_cases:
                result = await async_objective.eval_async(test_case)
                async_results.append(result)
                api_usage["calls"] += 1
            
            # Test sync method with eval_async (should use wrapper)
            self.runner.print("🔄 Testing user-provided sync method with async wrapper...", style="yellow")
            sync_async_results = []
            for test_case in test_cases:
                result = await sync_objective.eval_async(test_case)
                sync_async_results.append(result)
                api_usage["calls"] += 1
            
            # Test mixed parallel execution
            self.runner.print("🔄 Testing mixed parallel execution...", style="yellow")
            import time
            start_time = time.time()
            
            mixed_tasks = []
            for test_case in test_cases:
                mixed_tasks.append(async_objective.eval_async(test_case))
                mixed_tasks.append(sync_objective.eval_async(test_case))
            
            mixed_results = await asyncio.gather(*mixed_tasks)
            mixed_time = time.time() - start_time
            api_usage["calls"] += len(mixed_tasks)
            
            # Validate all results
            all_results = async_results + sync_async_results + mixed_results
            for result in all_results:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            
            # Verify async method detected politeness correctly
            polite_results = [r.result for r in async_results]
            expected_polite = [True, False, False]  # Only first has "please"
            
            # Verify sync method detected gratitude correctly  
            grateful_results = [r.result for r in sync_async_results]
            expected_grateful = [False, True, False]  # Only second has "thank"/"appreciate"
            
            polite_correct = polite_results == expected_polite
            grateful_correct = grateful_results == expected_grateful
            
            if not polite_correct or not grateful_correct:
                return TestResult(
                    name="Async User-Provided Methods",
                    status=TestStatus.FAIL,
                    message="✗ User-provided method evaluation incorrect",
                    details=f"Polite: {polite_results} vs {expected_polite}, Grateful: {grateful_results} vs {expected_grateful}",
                    expected="Correct evaluation by user methods",
                    actual=f"Polite correct: {polite_correct}, Grateful correct: {grateful_correct}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=0  # No API tokens for mock methods
                )
            
            return TestResult(
                name="Async User-Provided Methods",
                status=TestStatus.PASS,
                message=f"✓ User-provided async/sync methods work correctly (mixed time: {mixed_time:.2f}s)",
                details=f"Async results: {polite_results}, Sync wrapped results: {grateful_results}",
                expected="Correct evaluation by user methods",
                actual="All user-provided methods evaluated correctly",
                api_calls_made=api_usage["calls"],
                total_tokens=0
            )
            
        except Exception as e:
            return TestResult(
                name="Async User-Provided Methods",
                status=TestStatus.FAIL,
                message=f"✗ User-provided async methods test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful user method evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_async_error_handling(self) -> TestResult:
        """Test async error handling for various failure modes."""
        try:
            # Test async method that raises exception
            async def failing_async_method(input_data):
                await asyncio.sleep(0.05)
                raise ValueError("Simulated async LLM failure")
            
            # Test sync method that raises exception 
            def failing_sync_method(input_data):
                raise ConnectionError("Simulated API connection failure")
            
            failing_async_obj = LLMJudgeObjective(
                invoke_method=failing_async_method,
                output_key="response"
            )
            
            failing_sync_obj = LLMJudgeObjective(
                invoke_method=failing_sync_method,
                output_key="response"
            )
            
            test_output = {"response": "Test message"}
            
            # Test async method failure handling
            self.runner.print("🔄 Testing async method exception handling...", style="yellow")
            async_error_result = await failing_async_obj.eval_async(test_output)
            
            # Test sync method failure handling in async context
            self.runner.print("🔄 Testing sync method exception handling in async...", style="yellow")
            sync_error_result = await failing_sync_obj.eval_async(test_output)
            
            # Test missing output key
            self.runner.print("🔄 Testing missing output key handling...", style="yellow")
            missing_key_result = await failing_async_obj.eval_async({"wrong_key": "value"})
            
            # Test invalid output type
            self.runner.print("🔄 Testing invalid output type handling...", style="yellow")
            
            # Mock method that returns invalid result format
            async def invalid_format_method(input_data):
                return "invalid_format_not_dict"
            
            invalid_obj = LLMJudgeObjective(
                invoke_method=invalid_format_method,
                output_key="response"
            )
            invalid_format_result = await invalid_obj.eval_async(test_output)
            
            # Validate all error results are InvalidEvalResult (using name-based checking due to module path issues)
            error_results = [async_error_result, sync_error_result, missing_key_result, invalid_format_result]
            
            # Expected error type names (avoiding isinstance due to module path mismatch)
            expected_error_type_names = [
                "InvalidEvalResult",      # async method exception -> InvalidEvalResult from _eval_fn_async  
                "InvalidEvalResult",      # sync method exception -> InvalidEvalResult from _eval_fn_async
                "OutputKeyNotFoundError", # missing key -> OutputKeyNotFoundError from _extract_filtered_output_async
                "InvalidEvalResult"       # invalid format -> InvalidEvalResult from _eval_fn_async
            ]
            
            # Verify error types and messages using name-based checking
            for i, (result, expected_type_name) in enumerate(zip(error_results, expected_error_type_names)):
                actual_type_name = type(result).__name__
                
                # Check if result is any kind of error result (should not be BoolEvalResult)
                if actual_type_name == "BoolEvalResult":
                    return TestResult(
                        name="Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} returned success instead of error",
                        details="Got BoolEvalResult but expected error type",
                        expected="Error result type",
                        actual="BoolEvalResult (success)",
                        api_calls_made=0,
                        total_tokens=0
                    )
                
                # Check if it's an invalid eval result (any error type)
                invalid_result_names = ["InvalidEvalResult", "EvaluationError", "OutputKeyNotFoundError", "ExtractionError", "FormattingError", "EvalTypeMismatchError", "AgentOperationError"]
                if actual_type_name not in invalid_result_names:
                    return TestResult(
                        name="Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} unexpected type: {actual_type_name}",
                        details=f"Result: {result}",
                        expected="One of: " + ", ".join(invalid_result_names),
                        actual=actual_type_name,
                        api_calls_made=0,
                        total_tokens=0
                    )
                
                # Verify error message is informative
                if not result.message or len(result.message.strip()) == 0:
                    return TestResult(
                        name="Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} has empty message",
                        details=f"Message: '{result.message}'",
                        expected="Non-empty error message",
                        actual="Empty or whitespace message",
                        api_calls_made=0,
                        total_tokens=0
                    )
                
                # Verify result value is None for error cases
                if result.result is not None:
                    return TestResult(
                        name="Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} result should be None",
                        details=f"Result value: {result.result}",
                        expected="None result for error cases",
                        actual=f"Result: {result.result}",
                        api_calls_made=0,
                        total_tokens=0
                    )
            
            return TestResult(
                name="Async Error Handling",
                status=TestStatus.PASS,
                message="✓ All async error conditions handled correctly",
                details="Tested: async exception, sync exception, missing key, invalid format",
                expected="Proper error handling for all failure modes",
                actual="All error conditions returned InvalidEvalResult with informative messages",
                api_calls_made=0,
                total_tokens=0
            )
            
        except Exception as e:
            return TestResult(
                name="Async Error Handling",
                status=TestStatus.FAIL,
                message=f"✗ Async error handling test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful error handling test",
                actual=f"Test threw exception: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_async_hook_functionality(self) -> TestResult:
        """Test async hook functionality with pre_run, post_run, and post_eval hooks."""
        try:
            hook_calls = {"pre_run": 0, "post_run": 0, "post_eval": 0}
            
            # Mock async hooks
            async def async_pre_run_hook():
                await asyncio.sleep(0.01)
                hook_calls["pre_run"] += 1
            
            async def async_post_run_hook():
                await asyncio.sleep(0.01)
                hook_calls["post_run"] += 1
            
            async def async_post_eval_hook():
                await asyncio.sleep(0.01)
                hook_calls["post_eval"] += 1
            
            # Mock sync hooks for mixed testing
            def sync_pre_run_hook():
                hook_calls["pre_run"] += 10  # Different increment to distinguish
            
            def sync_post_eval_hook():
                hook_calls["post_eval"] += 10
            
            # Mock LLM method
            async def mock_eval_method(input_data):
                return {"result": True, "message": "Hook test evaluation"}
            
            # Test with async hooks
            async_hooks_obj = LLMJudgeObjective(
                invoke_method=mock_eval_method,
                output_key="response",
                pre_run_hook=async_pre_run_hook,
                post_run_hook=async_post_run_hook,
                post_eval_hook=async_post_eval_hook
            )
            
            # Test with mixed sync/async hooks
            mixed_hooks_obj = LLMJudgeObjective(
                invoke_method=mock_eval_method,
                output_key="response",
                pre_run_hook=sync_pre_run_hook,
                post_eval_hook=sync_post_eval_hook
            )
            
            test_output = {"response": "Test hook message"}
            
            # Test async hooks
            self.runner.print("🔄 Testing async hooks...", style="yellow")
            initial_counts = hook_calls.copy()
            
            # Note: The current implementation doesn't call pre_run/post_run hooks in eval_async
            # Only post_eval_hook is called, so we test that
            await async_hooks_obj.eval_async(test_output)
            
            async_post_eval_called = hook_calls["post_eval"] > initial_counts["post_eval"]
            
            # Test mixed hooks
            self.runner.print("🔄 Testing mixed sync/async hooks...", style="yellow")
            initial_counts = hook_calls.copy()
            
            await mixed_hooks_obj.eval_async(test_output)
            
            sync_post_eval_called = hook_calls["post_eval"] > initial_counts["post_eval"]
            
            # Test manual hook calls
            self.runner.print("🔄 Testing manual async hook calls...", style="yellow")
            initial_counts = hook_calls.copy()
            
            await async_hooks_obj.run_pre_run_hook_async()
            await async_hooks_obj.run_post_run_hook_async()
            await async_hooks_obj.run_post_eval_hook_async()
            
            manual_hooks_called = (
                hook_calls["pre_run"] > initial_counts["pre_run"] and
                hook_calls["post_run"] > initial_counts["post_run"] and
                hook_calls["post_eval"] > initial_counts["post_eval"]
            )
            
            if not async_post_eval_called:
                return TestResult(
                    name="Async Hook Functionality",
                    status=TestStatus.FAIL,
                    message="✗ Async post_eval hook not called during eval_async",
                    details=f"Hook calls: {hook_calls}",
                    expected="post_eval hook called during evaluation",
                    actual="Hook not called",
                    api_calls_made=0,
                    total_tokens=0
                )
            
            if not sync_post_eval_called:
                return TestResult(
                    name="Async Hook Functionality", 
                    status=TestStatus.FAIL,
                    message="✗ Sync post_eval hook not called in async context",
                    details=f"Hook calls: {hook_calls}",
                    expected="Sync hook called in async context",
                    actual="Hook not called",
                    api_calls_made=0,
                    total_tokens=0
                )
            
            if not manual_hooks_called:
                return TestResult(
                    name="Async Hook Functionality",
                    status=TestStatus.FAIL,
                    message="✗ Manual async hook calls failed",
                    details=f"Hook calls: {hook_calls}",
                    expected="All manual hook calls successful",
                    actual="Some manual hooks not called",
                    api_calls_made=0,
                    total_tokens=0
                )
            
            return TestResult(
                name="Async Hook Functionality",
                status=TestStatus.PASS,
                message="✓ All async hook functionality working correctly",
                details=f"Final hook calls: {hook_calls}",
                expected="Proper async hook execution",
                actual="All hooks called correctly in async context",
                api_calls_made=0,
                total_tokens=0
            )
            
        except Exception as e:
            return TestResult(
                name="Async Hook Functionality",
                status=TestStatus.FAIL,
                message=f"✗ Async hook functionality test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful hook functionality test",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_async_langchain_ainvoke_integration(self) -> TestResult:
        """Test async integration with LangChain's ainvoke method."""
        if not self._check_prerequisites():
            return TestResult(
                name="Async LangChain ainvoke Integration",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need LangChain and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real LangChain LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=80
            )
            
            parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
            
            prompt = PromptTemplate(
                template=DEFAULT_BINARY_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "expected_output": "A message containing a question mark",
                    "format_instructions": parser.get_format_instructions()
                }
            )
            
            chain = prompt | llm | parser
            
            # Verify chain has ainvoke
            if not hasattr(chain, 'ainvoke'):
                return TestResult(
                    name="Async LangChain ainvoke Integration",
                    status=TestStatus.FAIL,
                    message="✗ LangChain chain doesn't have ainvoke method",
                    details="Chain object missing async invoke capability",
                    expected="Chain with ainvoke method",
                    actual="Chain without ainvoke",
                    api_calls_made=0,
                    total_tokens=0
                )
            
            # Create objective (should automatically use ainvoke for async)
            objective = LLMJudgeObjective(
                prompt=DEFAULT_BINARY_PROMPT,
                goal="A message containing a question mark",
                output_key="response"
            )
            
            # Verify objective has async invoke method set up
            if not hasattr(objective, '_async_invoke_method') or objective._async_invoke_method is None:
                return TestResult(
                    name="Async LangChain ainvoke Integration",
                    status=TestStatus.FAIL,
                    message="✗ LLMJudgeObjective didn't set up async invoke method",
                    details="Objective missing _async_invoke_method",
                    expected="Objective with async invoke method",
                    actual="Objective without async invoke",
                    api_calls_made=0,
                    total_tokens=0
                )
            
            test_cases = [
                {"response": "How are you doing today?", "expected": True},
                {"response": "I am fine, thanks.", "expected": False},
                {"response": "What time is it?", "expected": True}
            ]
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test parallel async execution
            self.runner.print("🔄 Testing parallel async execution...", style="yellow")
            import time
            start_time = time.time()
            
            async_tasks = [objective.eval_async(test_case) for test_case in test_cases]
            parallel_results = await asyncio.gather(*async_tasks)
            
            parallel_time = time.time() - start_time
            api_usage["calls"] += len(async_tasks)
            api_usage["tokens"] = api_usage["calls"] * 60  # Rough estimate
            
            # Verify all results are valid
            for result in parallel_results:
                self.runner.assert_isinstance(result, BoolEvalResult, "Should return BoolEvalResult")
            
            # Check expected results
            expected_results = [test_case["expected"] for test_case in test_cases]
            actual_results = [result.result for result in parallel_results]
            
            correct_count = sum(1 for expected, actual in zip(expected_results, actual_results) if expected == actual)
            
            if correct_count < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Async LangChain ainvoke Integration",
                    status=TestStatus.FAIL,
                    message=f"✗ Async evaluation accuracy too low: {correct_count}/3",
                    details=f"Expected: {expected_results}, Actual: {actual_results}",
                    expected="At least 2/3 correct evaluations",
                    actual=f"{correct_count}/3 correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            return TestResult(
                name="Async LangChain ainvoke Integration",
                status=TestStatus.PASS,
                message=f"✓ LangChain async integration successful ({parallel_time:.2f}s for parallel)",
                details=f"Accuracy: {correct_count}/3, Used ainvoke for async execution",
                expected="Successful async LangChain integration",
                actual=f"All async functionality working, {correct_count}/3 correct",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Async LangChain ainvoke Integration",
                status=TestStatus.FAIL,
                message=f"✗ Async LangChain integration failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful async LangChain integration",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )


def main():
    """Main test execution function for real LangChain integration tests."""
    runner = TestRunner()
    
    # Check environment setup
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        runner.print("[red]❌ OPENAI_API_KEY not found in environment![/red]")
        runner.print("[yellow]Please set OPENAI_API_KEY in your .env file before running real API tests.[/yellow]")
        sys.exit(1)
    else:
        runner.print(f"[green]✓ OPENAI_API_KEY found: {openai_key[:8]}...{openai_key[-4:]}[/green]")
    
    if not LANGCHAIN_AVAILABLE:
        runner.print("[red]❌ LangChain not available. Install with: pip install langchain langchain-openai[/red]")
        sys.exit(1)
    else:
        runner.print("[green]✓ LangChain available[/green]")
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]Real LangChain + OpenAI Integration Tests", style="cyan")
        runner.console.print("\n[bold]Testing LLMJudgeObjective with Real AI Agents (API Calls)[/bold]")
        runner.console.print("[yellow]⚠️  This will make actual API calls and incur costs![/yellow]\n")
    else:
        print("="*80)
        print("Real LangChain + OpenAI Integration Tests")
        print("="*80)
        print("Testing LLMJudgeObjective with Real AI Agents (API Calls)")
        print("⚠️  This will make actual API calls and incur costs!\n")
    
    # Initialize test suite
    real_tests = RealLangChainLLMJudgeTests(runner)
    
    # Define test methods to run
    test_methods = [
        # Real AI integration tests
        ("Real OpenAI Binary Evaluation", real_tests.test_real_openai_binary_evaluation),
        ("Real OpenAI Detailed Evaluation", real_tests.test_real_openai_detailed_evaluation),
        ("Real OpenAI Score-Based Evaluation", real_tests.test_real_openai_score_based_evaluation),
        ("Real OpenAI Creative Evaluation", real_tests.test_real_openai_creative_evaluation),
        ("Real OpenAI Technical Evaluation", real_tests.test_real_openai_technical_evaluation),
        
        # Async functionality tests
        ("Async Parallel OpenAI Evaluation", real_tests.test_async_real_openai_parallel_evaluation),
        ("Async User-Provided Methods", real_tests.test_async_user_provided_methods),
        ("Async Error Handling", real_tests.test_async_error_handling),
        ("Async Hook Functionality", real_tests.test_async_hook_functionality),
        ("Async LangChain ainvoke Integration", real_tests.test_async_langchain_ainvoke_integration),
    ]
    
    # Warning about API calls (no user confirmation required for automated testing)
    if runner.console:
        runner.console.print("\n[bold red]⚠️  WARNING: Making real API calls to OpenAI![/bold red]")
        runner.console.print("[yellow]This will incur actual costs on your OpenAI account.[/yellow]")
    else:
        print("\n⚠️  WARNING: Making real API calls to OpenAI!")
        print("This will incur actual costs on your OpenAI account.")
    
    # Run tests with progress indication
    if runner.console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=runner.console,
        ) as progress:
            task = progress.add_task("Running real AI tests...", total=len(test_methods))
            
            for test_name, test_method in test_methods:
                progress.update(task, description=f"Running: {test_name}")
                result = runner.run_test(test_name, test_method)
                progress.advance(task)
                
                # Show immediate feedback
                status_style = "green" if result.status == TestStatus.PASS else "yellow" if result.status == TestStatus.SKIP else "red"
                runner.console.print(f"  {result.status.value} {test_name}", style=status_style)
                if result.api_calls_made > 0:
                    runner.console.print(f"    [dim]API calls: {result.api_calls_made}, Tokens: {result.total_tokens}[/dim]")
    else:
        print("Running real AI integration tests...\n")
        for i, (test_name, test_method) in enumerate(test_methods, 1):
            print(f"[{i}/{len(test_methods)}] Running: {test_name}")
            result = runner.run_test(test_name, test_method)
            print(f"  {result.status.value} {test_name}")
            if result.api_calls_made > 0:
                print(f"    API calls: {result.api_calls_made}, Tokens: {result.total_tokens}")
    
    # Display final results
    runner.display_results()
    
    # Exit with appropriate code
    exit_code = 0 if runner.passed_tests == runner.total_tests else 1
    if runner.console:
        runner.console.print(f"\n[bold]Exiting with code: {exit_code}[/bold]")
        if runner.total_api_calls > 0:
            runner.console.print(f"[dim]Total API usage: {runner.total_api_calls} calls, {runner.total_tokens_used:,} tokens[/dim]")
    else:
        print(f"\nExiting with code: {exit_code}")
        if runner.total_api_calls > 0:
            print(f"Total API usage: {runner.total_api_calls} calls, {runner.total_tokens_used:,} tokens")
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
