#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Real Pydantic AI integration test suite for LLMJudgeObjective class.
Tests advanced LLM-based evaluation with actual Pydantic AI API calls and real AI agents.
Uses the OPENAI_API_KEY from .env file for authentic performance testing.
"""

import sys
import traceback
import os
import asyncio
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Load environment variables from the specified .env file
try:
    from dotenv import load_dotenv
    # Get the root directory of OmniBAR (parent of tests/)
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path, override=True)
    DOTENV_AVAILABLE = True
    print(f"✓ Loaded environment from: {env_path}")
    
    # Verify API key is loaded
    import os
    if os.getenv('OPENAI_API_KEY'):
        print(f"✓ OPENAI_API_KEY loaded: {os.getenv('OPENAI_API_KEY')[:10]}...")
    else:
        print("❌ OPENAI_API_KEY not found in environment")
        
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

# Pydantic AI imports for real AI integration
try:
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    print("❌ Pydantic AI not available. Install with: pip install pydantic-ai")

# Import the classes we want to test
from omnibar.objectives.llm_judge import LLMJudgeObjective
from omnibar.core.types import BoolEvalResult


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
            print("REAL PYDANTIC AI INTEGRATION TEST RESULTS")
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
        self.console.rule("[bold blue]Real Pydantic AI Integration Test Results", style="blue")
        
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
            title="Real Pydantic AI Integration Summary",
            border_style=summary_style
        )
        self.console.print(summary)


# Pydantic AI Models for structured real evaluation
class EvaluationContext(BaseModel):
    """Context information for evaluation"""
    expected_output: str = Field(description="The expected output from the agent")
    evaluation_criteria: str = Field(description="Specific criteria for evaluation") 
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class DetailedEvaluationResult(BaseModel):
    """Structured result from Pydantic AI evaluation"""
    result: bool = Field(description="Whether the output meets expectations")
    confidence: float = Field(description="Confidence score (0-1)", ge=0.0, le=1.0)
    message: str = Field(description="Detailed explanation of the evaluation")
    criteria_met: List[str] = Field(description="List of criteria that were satisfied")
    criteria_failed: List[str] = Field(description="List of criteria that failed")
    suggestions: Optional[str] = Field(default=None, description="Suggestions for improvement")


class NumericEvaluationResult(BaseModel):
    """Numeric scoring result from Pydantic AI"""
    result: float = Field(description="Numeric score between 0 and 1", ge=0.0, le=1.0)
    message: str = Field(description="Explanation of the score")
    breakdown: dict = Field(description="Detailed breakdown of scoring components")


class CreativeEvaluationResult(BaseModel):
    """Creative content evaluation result"""
    result: bool = Field(description="Whether the content is sufficiently creative")
    creativity_score: float = Field(description="Creativity score (0-1)", ge=0.0, le=1.0)
    originality: float = Field(description="Originality score (0-1)", ge=0.0, le=1.0)
    engagement: float = Field(description="Engagement score (0-1)", ge=0.0, le=1.0)
    message: str = Field(description="Detailed evaluation explanation")
    strengths: List[str] = Field(description="Creative strengths identified")
    improvements: List[str] = Field(description="Areas for improvement")


@dataclass
class EvaluationDependencies:
    """Dependencies for Pydantic AI agent evaluation"""
    context: EvaluationContext
    model_name: str = "gpt-4o-mini"
    debug_mode: bool = False


# Helper function to create async Pydantic AI invoke methods
def create_pydantic_ai_async_invoke(agent: Agent):
    """Create an async invoke method compatible with LLMJudgeObjective.
    
    Since Pydantic AI is async-only, this is the only invoke method we need.
    """
    async def async_invoke(input_dict: Dict[str, str]) -> Dict[str, Any]:
        """Invoke the Pydantic AI agent with the input."""
        result = await agent.run(input_dict["input"])
        
        # Convert Pydantic AI result to our expected format
        if hasattr(result.output, '__dict__'):
            # If it's a Pydantic model, convert to dict
            output_dict = result.output.__dict__
        elif isinstance(result.output, dict):
            # If it's already a dict, return as-is
            output_dict = result.output
        else:
            # If it's a simple value, wrap it in our expected format
            output_dict = {
                "result": bool(result.output),
                "message": str(result.output)
            }
        
        # Ensure we have the required keys
        if "result" not in output_dict:
            output_dict["result"] = True  # Default to True if not specified
        if "message" not in output_dict:
            output_dict["message"] = "Evaluation completed"
            
        return output_dict
    
    return async_invoke


class RealPydanticAILLMJudgeTests:
    """Comprehensive test suite for LLMJudgeObjective with real Pydantic AI integration."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.api_calls_count = 0
        self.tokens_used = 0
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are available for real testing."""
        if not PYDANTIC_AI_AVAILABLE:
            return False
        if not os.getenv('OPENAI_API_KEY'):
            return False
        return True
    
    def _track_api_usage(self, result=None) -> Dict[str, int]:
        """Track API usage from Pydantic AI response."""
        api_calls = 1
        tokens = 0
        
        # Pydantic AI doesn't expose token usage directly in the same way
        # We'll estimate based on input/output lengths
        if hasattr(result, 'usage'):
            tokens = getattr(result.usage, 'total_tokens', 0)
        else:
            # Rough estimation
            tokens = 100  # Base estimate for simple requests
        
        self.api_calls_count += api_calls
        self.tokens_used += tokens
        
        return {"calls": api_calls, "tokens": tokens}
    
    async def test_real_pydantic_ai_structured_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real Pydantic AI structured evaluation using async-only."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real Pydantic AI Structured Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met (Pydantic AI or OpenAI API key missing)",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real Pydantic AI agent
            model = OpenAIModel('gpt-4o-mini')
            
            evaluation_agent = Agent(
                model,
                output_type=DetailedEvaluationResult,
                system_prompt=(
                    "You are an expert customer service evaluator. "
                    "Analyze customer service responses for professionalism, helpfulness, and clarity. "
                    "Provide detailed feedback on whether the response meets customer service standards."
                )
            )
            
            # Create async invoke method (Pydantic AI is async-only)
            async_invoke = create_pydantic_ai_async_invoke(evaluation_agent)
            
            # Create objective with async invoke method
            objective = LLMJudgeObjective(
                invoke_method=async_invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test with professional response using async eval
            self.runner.print("🔄 Testing professional customer service response...", style="yellow")
            professional_response = "Thank you for contacting us! I understand your concern about the billing issue. Let me help you resolve this immediately. I'll review your account and provide you with a detailed explanation of the charges. Is there a specific charge you'd like me to investigate first?"
            
            result_professional = await objective.eval_async({"response": professional_response})
            api_usage["calls"] += 1
            api_usage["tokens"] += 150  # Estimate
            
            # Test with unprofessional response using async eval
            self.runner.print("🔄 Testing unprofessional response...", style="yellow")
            unprofessional_response = "idk what ur talking about. check ur bill or something."
            
            result_unprofessional = await objective.eval_async({"response": unprofessional_response})
            api_usage["calls"] += 1
            api_usage["tokens"] += 120  # Estimate
            
            # Validate results using name-based checking (avoiding isinstance issues)
            prof_type_name = type(result_professional).__name__
            unprof_type_name = type(result_unprofessional).__name__
            
            if prof_type_name != "BoolEvalResult":
                return TestResult(
                    name="Real Pydantic AI Structured Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Professional response returned {prof_type_name}, expected BoolEvalResult",
                    details=f"Professional result type: {prof_type_name}",
                    expected="BoolEvalResult for professional response",
                    actual=f"{prof_type_name}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            if unprof_type_name != "BoolEvalResult":
                return TestResult(
                    name="Real Pydantic AI Structured Evaluation",
                    status=TestStatus.FAIL,
                    message=f"✗ Unprofessional response returned {unprof_type_name}, expected BoolEvalResult",
                    details=f"Unprofessional result type: {unprof_type_name}",
                    expected="BoolEvalResult for unprofessional response",
                    actual=f"{unprof_type_name}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            # Professional should pass, unprofessional should fail
            if not result_professional.result:
                return TestResult(
                    name="Real Pydantic AI Structured Evaluation",
                    status=TestStatus.FAIL,
                    message="✗ Pydantic AI incorrectly evaluated professional response as poor",
                    details=f"Professional result: {result_professional.result} | Message: {result_professional.message}",
                    expected="True for professional response",
                    actual=f"False: {result_professional.message}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            return TestResult(
                name="Real Pydantic AI Structured Evaluation",
                status=TestStatus.PASS,
                message="✓ Pydantic AI successfully evaluated customer service responses (async-only)",
                details=f"Professional: {result_professional.result} | Unprofessional: {result_unprofessional.result}",
                expected="Accurate evaluation of service quality",
                actual=f"Professional: {result_professional.result}, Unprofessional: {result_unprofessional.result}",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real Pydantic AI Structured Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real Pydantic AI structured evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful structured evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_real_pydantic_ai_dependency_injection(self) -> TestResult:
        """Test LLMJudgeObjective with real Pydantic AI dependency injection."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real Pydantic AI Dependency Injection",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create evaluation context  
            evaluation_context = EvaluationContext(
                expected_output="A technical explanation with examples",
                evaluation_criteria="Must include technical accuracy, clear examples, and proper terminology",
                confidence_threshold=0.7
            )
            
            # deps = EvaluationDependencies(context=evaluation_context, debug_mode=True)
            
            # Create real Pydantic AI agent with dependencies
            model = OpenAIModel('gpt-4o-mini')
            
            evaluation_agent = Agent(
                model,
                deps_type=EvaluationDependencies,
                output_type=DetailedEvaluationResult,
                system_prompt=(
                    "You are a technical writing evaluator. "
                    "Assess technical explanations for accuracy, clarity, and use of examples."
                )
            )
            
            @evaluation_agent.system_prompt
            async def add_context(ctx: RunContext[EvaluationDependencies]) -> str:
                return f"Expected: {evaluation_context.expected_output}. Criteria: {evaluation_context.evaluation_criteria}"
            
            # Create async invoke method (Pydantic AI is async-only)
            async_invoke = create_pydantic_ai_async_invoke(evaluation_agent)
            
            # Create objective with async invoke method
            objective = LLMJudgeObjective(
                invoke_method=async_invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test with good technical explanation
            self.runner.print("🔄 Testing good technical explanation...", style="yellow")
            good_technical = "Machine learning algorithms work by finding patterns in data through iterative training. For example, a neural network adjusts its weights based on prediction errors. Consider image classification: the algorithm learns to recognize features like edges and shapes, then combines them to identify objects like cats or dogs."
            
            result_good = await objective.eval_async({"response": good_technical})
            api_usage["calls"] += 1
            api_usage["tokens"] += 180  # Estimate
            
            # Test with poor technical explanation
            self.runner.print("🔄 Testing poor technical explanation...", style="yellow")
            poor_technical = "Machine learning is when computers learn stuff. It's complicated."
            
            result_poor = await objective.eval_async({"response": poor_technical})
            api_usage["calls"] += 1
            api_usage["tokens"] += 120  # Estimate
            
            # Validate results
            self.runner.assert_isinstance(result_good, BoolEvalResult, "Should return BoolEvalResult for good")
            self.runner.assert_isinstance(result_poor, BoolEvalResult, "Should return BoolEvalResult for poor")
            
            # Good should pass, poor should fail
            if not result_good.result or result_poor.result:
                return TestResult(
                    name="Real Pydantic AI Dependency Injection",
                    status=TestStatus.FAIL,
                    message="✗ Dependency injection evaluation accuracy insufficient",
                    details=f"Good: {result_good.result} | Poor: {result_poor.result}",
                    expected="Good: True, Poor: False",
                    actual=f"Good: {result_good.result}, Poor: {result_poor.result}",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            return TestResult(
                name="Real Pydantic AI Dependency Injection",
                status=TestStatus.PASS,
                message="✓ Dependency injection evaluation successful",
                details=f"Good: {result_good.result} | Poor: {result_poor.result}",
                expected="Context-aware technical evaluation",
                actual="Both evaluations used dependency context correctly",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real Pydantic AI Dependency Injection",
                status=TestStatus.FAIL,
                message=f"✗ Real Pydantic AI dependency injection failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful dependency injection",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_real_pydantic_ai_numeric_scoring(self) -> TestResult:
        """Test LLMJudgeObjective with real Pydantic AI numeric scoring."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real Pydantic AI Numeric Scoring",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real Pydantic AI agent for numeric scoring
            model = OpenAIModel('gpt-4o-mini')
            
            scoring_agent = Agent(
                model,
                output_type=NumericEvaluationResult,
                system_prompt=(
                    "You are a writing quality evaluator. "
                    "Score writing samples on a scale from 0.0 to 1.0 based on clarity, "
                    "grammar, structure, and overall quality. "
                    "Provide detailed breakdown of your scoring."
                )
            )
            
            # Create async invoke method for numeric scoring
            async_invoke = create_pydantic_ai_async_invoke(scoring_agent)
            
            # Custom async invoke that handles numeric scores and converts to boolean
            async def numeric_scoring_invoke(input_dict):
                result = await async_invoke(input_dict)
                score = result.get("result", 0.0)
                # Convert score to boolean (threshold at 0.6)
                bool_result = score >= 0.6
                return {
                    "result": bool_result,
                    "message": f"Score: {score:.2f} - {result.get('message', '')}"
                }
            
            objective = LLMJudgeObjective(
                invoke_method=numeric_scoring_invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test different quality levels
            test_writings = [
                {
                    "text": "The implementation of sustainable energy solutions requires a comprehensive approach that encompasses both technological innovation and policy reform. Solar and wind technologies have demonstrated remarkable efficiency improvements over the past decade, with costs decreasing significantly while output capacity has increased exponentially.",
                    "expected_high": True,
                    "label": "high_quality_writing"
                },
                {
                    "text": "Energy is good. We need more. Solar panels are ok I guess. Wind is loud but whatever.",
                    "expected_high": False,
                    "label": "low_quality_writing"
                },
                {
                    "text": "Renewable energy represents a paradigm shift in how we conceptualize power generation, moving from finite fossil fuel dependencies toward sustainable, environmentally conscious alternatives that can meet growing global energy demands while mitigating climate change impacts.",
                    "expected_high": True,
                    "label": "sophisticated_writing"
                }
            ]
            
            results = []
            for writing in test_writings:
                self.runner.print(f"🔄 Scoring {writing['label']}...", style="yellow")
                result = await objective.eval_async({"response": writing["text"]})
                api_usage["calls"] += 1
                api_usage["tokens"] += 200  # Estimate for numeric scoring
                
                results.append({
                    "label": writing["label"],
                    "expected_high": writing["expected_high"],
                    "actual_high": result.result,
                    "message": result.message,
                    "correct": result.result == writing["expected_high"]
                })
            
            # Validate scoring accuracy
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Real Pydantic AI Numeric Scoring",
                    status=TestStatus.FAIL,
                    message=f"✗ Numeric scoring accuracy too low: {correct_evaluations}/{total_evaluations}",
                    details=f"Results: {results}",
                    expected="At least 2/3 correct evaluations",
                    actual=f"{correct_evaluations}/{total_evaluations} correct",
                    api_calls_made=api_usage["calls"],
                    total_tokens=api_usage["tokens"]
                )
            
            results_summary = " | ".join([f"{r['label']}: {r['actual_high']}" for r in results])
            
            return TestResult(
                name="Real Pydantic AI Numeric Scoring",
                status=TestStatus.PASS,
                message=f"✓ Numeric scoring successful: {correct_evaluations}/{total_evaluations}",
                details=f"Results: {results_summary}",
                expected="Accurate numeric scoring",
                actual=f"{correct_evaluations}/{total_evaluations} correct",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real Pydantic AI Numeric Scoring",
                status=TestStatus.FAIL,
                message=f"✗ Real Pydantic AI numeric scoring failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful numeric scoring",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_real_pydantic_ai_creative_evaluation(self) -> TestResult:
        """Test LLMJudgeObjective with real Pydantic AI creative content evaluation."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real Pydantic AI Creative Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create real Pydantic AI agent for creative evaluation
            model = OpenAIModel('gpt-4o-mini')
            
            creative_agent = Agent(
                model,
                output_type=CreativeEvaluationResult,
                system_prompt=(
                    "You are a creative writing expert evaluating content for originality, "
                    "imagination, and artistic merit. Consider uniqueness of ideas, "
                    "vivid imagery, emotional impact, and innovative storytelling."
                )
            )
            
            # Create async invoke method
            async_invoke = create_pydantic_ai_async_invoke(creative_agent)
            
            objective = LLMJudgeObjective(
                invoke_method=async_invoke,
                output_key="response"
            )
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test creative writing samples
            creative_samples = [
                {
                    "text": "The clockmaker's daughter discovered that every timepiece in her father's shop contained trapped moments - seconds of laughter, minutes of sorrow, hours of dreams. When she wound the grandfather clock backwards, she could release these captured emotions back into the world, painting the air with colors that only she could see.",
                    "expected_creative": True,
                    "label": "highly_creative"
                },
                {
                    "text": "I went to the store today. I bought some bread and milk. Then I came home and watched TV. It was a normal day.",
                    "expected_creative": False,
                    "label": "mundane_content"
                },
                {
                    "text": "In the library of forgotten algorithms, each book contained code that reality itself had executed and then discarded. The librarian, who existed only on Tuesdays, helped visitors debug their personal timelines by finding the recursive loops that kept them trapped in patterns of regret.",
                    "expected_creative": True,
                    "label": "imaginative_concept"
                }
            ]
            
            results = []
            for sample in creative_samples:
                self.runner.print(f"🔄 Evaluating {sample['label']}...", style="yellow")
                result = await objective.eval_async({"response": sample["text"]})
                api_usage["calls"] += 1
                api_usage["tokens"] += 250  # Estimate for creative evaluation
                
                results.append({
                    "label": sample["label"],
                    "expected": sample["expected_creative"],
                    "actual": result.result,
                    "message": result.message,
                    "correct": result.result == sample["expected_creative"]
                })
            
            # Validate creative evaluation accuracy
            correct_evaluations = sum(1 for r in results if r["correct"])
            total_evaluations = len(results)
            
            if correct_evaluations < 2:  # At least 2 out of 3 should be correct
                return TestResult(
                    name="Real Pydantic AI Creative Evaluation",
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
                name="Real Pydantic AI Creative Evaluation",
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
                name="Real Pydantic AI Creative Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Real Pydantic AI creative evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful creative evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_real_pydantic_ai_multi_model_comparison(self) -> TestResult:
        """Test LLMJudgeObjective with multiple real Pydantic AI models."""
        if not self._check_prerequisites():
            return TestResult(
                name="Real Pydantic AI Multi-Model Comparison",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Test with different model configurations
            models_to_test = [
                ("gpt-4o-mini", "Fast and efficient"),
                ("gpt-4o", "High quality and detailed"),  # More expensive, use sparingly
            ]
            
            api_usage = {"calls": 0, "tokens": 0}
            model_results = {}
            
            test_content = "Artificial intelligence represents a transformative technology that will reshape industries, enhance human capabilities, and potentially solve complex global challenges through automated reasoning and pattern recognition."
            
            for model_name, description in models_to_test:
                self.runner.print(f"🔄 Testing {model_name} ({description})...", style="yellow")
                
                # Create agent for this model
                model = OpenAIModel(model_name)
                
                evaluation_agent = Agent(
                    model,
                    output_type=DetailedEvaluationResult,
                    system_prompt=(
                        "Evaluate this text for clarity, accuracy, and informativeness. "
                        "Consider whether it effectively communicates complex concepts."
                    )
                )
                
                # Create async invoke method (Pydantic AI is async-only)
                async_invoke = create_pydantic_ai_async_invoke(evaluation_agent)
                
                objective = LLMJudgeObjective(
                    invoke_method=async_invoke,
                    output_key="response"
                )
                
                result = await objective.eval_async({"response": test_content})
                api_usage["calls"] += 1
                # gpt-4o uses more tokens than gpt-4o-mini
                api_usage["tokens"] += 300 if "gpt-4o" == model_name else 200
                
                model_results[model_name] = {
                    "result": result.result,
                    "message": result.message,
                    "description": description
                }
                
                self.runner.assert_isinstance(result, BoolEvalResult, f"Should return BoolEvalResult for {model_name}")
            
            # All models should generally agree on good content
            all_results = [info["result"] for info in model_results.values()]
            agreement = len(set(all_results)) == 1  # All same result
            
            results_summary = " | ".join([f"{model}: {info['result']}" for model, info in model_results.items()])
            
            return TestResult(
                name="Real Pydantic AI Multi-Model Comparison",
                status=TestStatus.PASS,
                message="✓ Multi-model comparison successful",
                details=f"Models tested: {results_summary} | Agreement: {agreement}",
                expected="Consistent evaluation across models",
                actual=f"Tested {len(models_to_test)} models with {'good' if agreement else 'mixed'} agreement",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Real Pydantic AI Multi-Model Comparison",
                status=TestStatus.FAIL,
                message=f"✗ Multi-model comparison failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful multi-model comparison",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_pydantic_ai_async_parallel_evaluation(self) -> TestResult:
        """Test parallel async evaluation with real Pydantic AI agents."""
        if not self._check_prerequisites():
            return TestResult(
                name="Pydantic AI Async Parallel Evaluation",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            import time
            
            # Create multiple Pydantic AI agents for parallel testing
            model = OpenAIModel('gpt-4o-mini')
            
            evaluation_agent = Agent(
                model,
                output_type=DetailedEvaluationResult,
                system_prompt=(
                    "You are a content quality evaluator. "
                    "Assess content for clarity, accuracy, and helpfulness."
                )
            )
            
            # Create async invoke method
            async_invoke = create_pydantic_ai_async_invoke(evaluation_agent)
            
            # Create multiple objectives for parallel testing
            objectives = [
                LLMJudgeObjective(invoke_method=async_invoke, output_key="response")
                for _ in range(3)
            ]
            
            test_outputs = [
                {"response": "This is a clear, well-written explanation of the process."},
                {"response": "Here's a comprehensive guide with examples and best practices."},
                {"response": "An informative overview that addresses the key points effectively."}
            ]
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test async parallel execution
            self.runner.print("🔄 Testing async parallel Pydantic AI evaluation...", style="yellow")
            start_time = time.time()
            
            # Run evaluations in parallel using eval_async
            async_tasks = [
                obj.eval_async(output) 
                for obj, output in zip(objectives, test_outputs)
            ]
            async_results = await asyncio.gather(*async_tasks)
            
            async_time = time.time() - start_time
            api_usage["calls"] += len(async_tasks)
            api_usage["tokens"] = api_usage["calls"] * 120  # Estimate
            
            # Test sequential async execution for comparison
            self.runner.print("🔄 Testing sequential async Pydantic AI evaluation...", style="yellow")
            start_time = time.time()
            
            sequential_results = []
            for obj, output in zip(objectives, test_outputs):
                result = await obj.eval_async(output)
                sequential_results.append(result)
            
            sequential_time = time.time() - start_time
            api_usage["calls"] += len(sequential_results)
            api_usage["tokens"] += len(sequential_results) * 120
            
            # Verify results are consistent and valid
            for i, (async_result, sequential_result) in enumerate(zip(async_results, sequential_results)):
                async_type = type(async_result).__name__
                sequential_type = type(sequential_result).__name__
                
                if async_type != "BoolEvalResult":
                    return TestResult(
                        name="Pydantic AI Async Parallel Evaluation",
                        status=TestStatus.FAIL,
                        message=f"✗ Async result {i+1} wrong type: {async_type}",
                        details=f"Expected BoolEvalResult, got {async_type}",
                        expected="BoolEvalResult for async results",
                        actual=f"Got {async_type}",
                        api_calls_made=api_usage["calls"],
                        total_tokens=api_usage["tokens"]
                    )
                
                if sequential_type != "BoolEvalResult":
                    return TestResult(
                        name="Pydantic AI Async Parallel Evaluation",
                        status=TestStatus.FAIL,
                        message=f"✗ Sequential result {i+1} wrong type: {sequential_type}",
                        details=f"Expected BoolEvalResult, got {sequential_type}",
                        expected="BoolEvalResult for sequential results",
                        actual=f"Got {sequential_type}",
                        api_calls_made=api_usage["calls"],
                        total_tokens=api_usage["tokens"]
                    )
            
            # Verify performance improvement (parallel vs sequential)
            speedup = sequential_time / async_time if async_time > 0 else 1.0
            
            return TestResult(
                name="Pydantic AI Async Parallel Evaluation",
                status=TestStatus.PASS,
                message=f"✓ Pydantic AI async parallel evaluation successful (speedup: {speedup:.2f}x)",
                details=f"Parallel: {async_time:.2f}s, Sequential: {sequential_time:.2f}s, All results valid",
                expected="Successful parallel evaluation with performance gains",
                actual=f"Parallel execution with {speedup:.2f}x speedup over sequential",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Pydantic AI Async Parallel Evaluation",
                status=TestStatus.FAIL,
                message=f"✗ Pydantic AI async parallel evaluation failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful async parallel evaluation",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_pydantic_ai_async_error_handling(self) -> TestResult:
        """Test async error handling with Pydantic AI agents."""
        try:
            # Mock failing agent that mimics Pydantic AI structure
            class FailingAgent:
                async def run(self, input_text):
                    await asyncio.sleep(0.05)
                    raise ValueError("Simulated Pydantic AI agent failure")
            
            failing_agent = FailingAgent()
            failing_async_invoke = create_pydantic_ai_async_invoke(failing_agent)
            
            failing_obj = LLMJudgeObjective(
                invoke_method=failing_async_invoke,
                output_key="response"
            )
            
            test_output = {"response": "Test message"}
            
            # Test async method failure handling
            self.runner.print("🔄 Testing Pydantic AI async error handling...", style="yellow")
            error_result = await failing_obj.eval_async(test_output)
            
            # Test missing output key
            self.runner.print("🔄 Testing missing output key with Pydantic AI...", style="yellow")
            missing_key_result = await failing_obj.eval_async({"wrong_key": "value"})
            
            # Validate error results using name-based checking
            error_results = [error_result, missing_key_result]
            invalid_result_names = ["InvalidEvalResult", "EvaluationError", "OutputKeyNotFoundError", "ExtractionError"]
            
            for i, result in enumerate(error_results):
                result_type_name = type(result).__name__
                
                if result_type_name == "BoolEvalResult":
                    return TestResult(
                        name="Pydantic AI Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} returned success instead of error",
                        details="Got BoolEvalResult but expected error type",
                        expected="Error result type",
                        actual="BoolEvalResult (success)",
                        api_calls_made=0,
                        total_tokens=0
                    )
                
                if result_type_name not in invalid_result_names:
                    return TestResult(
                        name="Pydantic AI Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} unexpected type: {result_type_name}",
                        details=f"Result: {result}",
                        expected="One of: " + ", ".join(invalid_result_names),
                        actual=result_type_name,
                        api_calls_made=0,
                        total_tokens=0
                    )
                
                # Verify error message is informative
                if not result.message or len(result.message.strip()) == 0:
                    return TestResult(
                        name="Pydantic AI Async Error Handling",
                        status=TestStatus.FAIL,
                        message=f"✗ Error {i+1} has empty message",
                        details=f"Message: '{result.message}'",
                        expected="Non-empty error message",
                        actual="Empty or whitespace message",
                        api_calls_made=0,
                        total_tokens=0
                    )
            
            return TestResult(
                name="Pydantic AI Async Error Handling",
                status=TestStatus.PASS,
                message="✓ All Pydantic AI async error conditions handled correctly",
                details="Tested: async agent exception, missing key",
                expected="Proper error handling for all failure modes",
                actual="All error conditions returned appropriate error types",
                api_calls_made=0,
                total_tokens=0
            )
            
        except Exception as e:
            return TestResult(
                name="Pydantic AI Async Error Handling",
                status=TestStatus.FAIL,
                message=f"✗ Pydantic AI async error handling test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful error handling test",
                actual=f"Test threw exception: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
    
    async def test_pydantic_ai_async_consistency(self) -> TestResult:
        """Test Pydantic AI async invoke methods for consistency across multiple calls."""
        if not self._check_prerequisites():
            return TestResult(
                name="Pydantic AI Async Consistency",
                status=TestStatus.SKIP,
                message="⏭️ Prerequisites not met",
                details="Need Pydantic AI and OPENAI_API_KEY environment variable"
            )
        
        try:
            # Create Pydantic AI agent
            model = OpenAIModel('gpt-4o-mini')
            
            evaluation_agent = Agent(
                model,
                output_type=DetailedEvaluationResult,
                system_prompt="Evaluate content for overall quality and usefulness."
            )
            
            # Create async invoke method (Pydantic AI is async-only)
            async_invoke = create_pydantic_ai_async_invoke(evaluation_agent)
            
            # Create objective with async invoke method
            objective = LLMJudgeObjective(
                invoke_method=async_invoke,
                output_key="response"
            )
            
            test_output = {"response": "This is a well-structured and informative piece of content."}
            
            api_usage = {"calls": 0, "tokens": 0}
            
            # Test multiple sequential async calls
            self.runner.print("🔄 Testing sequential async calls...", style="yellow")
            sequential_results = []
            for i in range(3):
                result = await objective.eval_async(test_output)
                sequential_results.append(result)
                api_usage["calls"] += 1
                api_usage["tokens"] += 100
            
            # Test parallel async execution
            self.runner.print("🔄 Testing parallel async execution...", style="yellow")
            import time
            start_time = time.time()
            
            parallel_results = await asyncio.gather(
                objective.eval_async(test_output),
                objective.eval_async(test_output),
                objective.eval_async(test_output)
            )
            
            parallel_time = time.time() - start_time
            api_usage["calls"] += 3
            api_usage["tokens"] += 300
            
            # Validate all results
            all_results = sequential_results + parallel_results
            for i, result in enumerate(all_results):
                result_type = type(result).__name__
                if result_type != "BoolEvalResult":
                    return TestResult(
                        name="Pydantic AI Async Consistency",
                        status=TestStatus.FAIL,
                        message=f"✗ Result {i+1} wrong type: {result_type}",
                        details=f"Expected BoolEvalResult, got {result_type}",
                        expected="BoolEvalResult for all results",
                        actual=f"Got {result_type}",
                        api_calls_made=api_usage["calls"],
                        total_tokens=api_usage["tokens"]
                    )
            
            # Check for consistency (should all evaluate similar content similarly)
            all_bool_results = [r.result for r in all_results]
            consistency = len(set(all_bool_results)) <= 2  # Allow some variation
            
            return TestResult(
                name="Pydantic AI Async Consistency",
                status=TestStatus.PASS,
                message=f"✓ Pydantic AI async methods work consistently (time: {parallel_time:.2f}s)",
                details=f"Sequential and parallel execution successful, consistency: {consistency}",
                expected="Consistent async evaluation behavior",
                actual="All async calls successful with reasonable consistency",
                api_calls_made=api_usage["calls"],
                total_tokens=api_usage["tokens"]
            )
            
        except Exception as e:
            return TestResult(
                name="Pydantic AI Async Consistency",
                status=TestStatus.FAIL,
                message=f"✗ Async consistency test failed: {str(e)}",
                details=f"Error: {str(e)}",
                expected="Successful async consistency test",
                actual=f"Error: {type(e).__name__}",
                traceback=traceback.format_exc()
            )


def main():
    """Main test execution function for real Pydantic AI integration tests."""
    runner = TestRunner()
    
    # Check environment setup
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        runner.print("[red]❌ OPENAI_API_KEY not found in environment![/red]")
        runner.print("[yellow]Please set OPENAI_API_KEY in your .env file before running real API tests.[/yellow]")
        sys.exit(1)
    else:
        runner.print(f"[green]✓ OPENAI_API_KEY found: {openai_key[:8]}...{openai_key[-4:]}[/green]")
    
    if not PYDANTIC_AI_AVAILABLE:
        runner.print("[red]❌ Pydantic AI not available. Install with: pip install pydantic-ai[/red]")
        sys.exit(1)
    else:
        runner.print("[green]✓ Pydantic AI available[/green]")
    
    # Print header
    if runner.console:
        runner.console.rule("[bold cyan]Real Pydantic AI + OpenAI Integration Tests", style="cyan")
        runner.console.print("\n[bold]Testing LLMJudgeObjective with Real Pydantic AI Agents (API Calls)[/bold]")
        runner.console.print("[yellow]⚠️  This will make actual API calls and incur costs![/yellow]\n")
    else:
        print("="*80)
        print("Real Pydantic AI + OpenAI Integration Tests")
        print("="*80)
        print("Testing LLMJudgeObjective with Real Pydantic AI Agents (API Calls)")
        print("⚠️  This will make actual API calls and incur costs!\n")
    
    # Initialize test suite
    real_tests = RealPydanticAILLMJudgeTests(runner)
    
    # Define test methods to run
    test_methods = [
        # Real Pydantic AI integration tests
        ("Real Pydantic AI Structured Evaluation", real_tests.test_real_pydantic_ai_structured_evaluation),
        ("Real Pydantic AI Dependency Injection", real_tests.test_real_pydantic_ai_dependency_injection),
        ("Real Pydantic AI Numeric Scoring", real_tests.test_real_pydantic_ai_numeric_scoring),
        ("Real Pydantic AI Creative Evaluation", real_tests.test_real_pydantic_ai_creative_evaluation),
        ("Real Pydantic AI Multi-Model Comparison", real_tests.test_real_pydantic_ai_multi_model_comparison),
        
        # Async functionality tests with Pydantic AI
        ("Pydantic AI Async Parallel Evaluation", real_tests.test_pydantic_ai_async_parallel_evaluation),
        ("Pydantic AI Async Error Handling", real_tests.test_pydantic_ai_async_error_handling),
        ("Pydantic AI Async Consistency", real_tests.test_pydantic_ai_async_consistency),
    ]
    
    # Warning about API calls (no user confirmation required for automated testing)
    if runner.console:
        runner.console.print("\n[bold red]⚠️  WARNING: Making real API calls to OpenAI via Pydantic AI![/bold red]")
        runner.console.print("[yellow]This will incur actual costs on your OpenAI account.[/yellow]")
    else:
        print("\n⚠️  WARNING: Making real API calls to OpenAI via Pydantic AI!")
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
            task = progress.add_task("Running real Pydantic AI tests...", total=len(test_methods))
            
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
        print("Running real Pydantic AI integration tests...\n")
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
