#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Model Parity Comparison Example with Pydantic AI and OmniBAR

This example demonstrates how to use OmniBAR for model parity comparisons by
benchmarking Claude 3.5 Sonnet vs GPT-4 on the same literary analysis task.
It showcases how to objectively compare different AI models using identical
evaluation criteria.

Features:
- Head-to-head model comparison (Claude 3.5 Sonnet vs GPT-4)
- Identical evaluation objectives for fair comparison
- Response correctness evaluation (Boolean scoring)
- Reasoning quality assessment (Float 0-1 scoring)
- Comprehensive comparison table with statistical analysis
- Structured output using Pydantic models
- Async execution support for efficient benchmarking

Requirements:
- pip install pydantic-ai
- pip install pydantic-ai[anthropic] for Anthropic support
- pip install pydantic-ai[openai] for OpenAI support
- Set ANTHROPIC_API_KEY environment variable (for Claude agents)
- Set OPENAI_API_KEY environment variable (for GPT-4 agents and LLM Judge evaluation)

Usage:
    python pydantic_ai_example.py

Output:
    - Detailed benchmark results for each model
    - Side-by-side comparison table
    - Statistical analysis and recommendations
"""

import asyncio
from pathlib import Path

# Flexible environment variable loading
def load_environment_variables():
    """
    Load environment variables from various possible locations.
    
    Priority order:
    1. OMNIBAR_ENV_PATH environment variable (if set)
    2. .env in current directory  
    3. .env in parent directory (examples/)
    4. .env in project root (../../)
    5. Skip if none found
    """
    try:
        from dotenv import load_dotenv
        import os
        
        # Option 1: Check for custom env path
        custom_env = os.getenv('OMNIBAR_ENV_PATH')
        if custom_env:
            custom_path = Path(custom_env)
            if custom_path.exists():
                load_dotenv(custom_path)
                print(f"✅ Loaded environment variables from custom path: {custom_path}")
                return True
            else:
                print(f"⚠️  Custom env path not found: {custom_path}")
        
        # Option 2-4: Check common locations
        current_dir = Path(__file__).parent
        search_paths = [
            current_dir / '.env',                    # ./env
            current_dir.parent / '.env',             # ../env  
            current_dir.parent.parent / '.env'       # ../../.env (project root)
        ]
        
        for env_path in search_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded environment variables from {env_path}")
                return True
        
        print("⚠️  No .env file found in common locations")
        print("💡 To specify a custom location, set OMNIBAR_ENV_PATH environment variable")
        return False
        
    except ImportError:
        print("⚠️  python-dotenv not available, environment variables should be set manually")
        return False

# Load environment variables
load_environment_variables()

# Import OmniBAR components
from omnibar import Benchmark
from omnibar.objectives import LLMJudgeObjective, CombinedBenchmarkObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult
from omnibar.integrations.pydantic_ai import PydanticAIOmniBarmarker

# Pydantic AI imports
try:
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.openai import OpenAIModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False


# Response model for structured output
class AgentResponse(BaseModel):
    """Structured response from our Pydantic AI agent."""
    answer: str = Field(description="The main answer to the question")
    confidence: float = Field(description="Confidence level (0.0 to 1.0)", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation of the reasoning")



def create_claude_agent() -> Agent:
    """Factory function to create Claude 3.5 Sonnet agent instances for OmniBAR."""
    if not PYDANTIC_AI_AVAILABLE:
        raise ImportError("Pydantic AI is required but not available")
    
    # Create the Pydantic AI agent with Claude 3.5 Sonnet
    agent = Agent(
        model=AnthropicModel("claude-3-5-sonnet-20241022"),
        result_type=AgentResponse,
        system_prompt=(
            "You are a helpful assistant that provides accurate, concise answers. "
            "Always include your confidence level and reasoning for your answers. "
            "Be honest if you're not sure about something."
        )
    )
    
    return agent


def create_gpt4_agent() -> Agent:
    """Factory function to create GPT-4 agent instances for OmniBAR."""
    if not PYDANTIC_AI_AVAILABLE:
        raise ImportError("Pydantic AI is required but not available")
    
    # Create the Pydantic AI agent with GPT-4
    agent = Agent(
        model=OpenAIModel("gpt-4"),
        result_type=AgentResponse,
        system_prompt=(
            "You are a helpful assistant that provides accurate, concise answers. "
            "Always include your confidence level and reasoning for your answers. "
            "Be honest if you're not sure about something."
        )
    )
    
    return agent


async def run_benchmark_with_model(agent_factory, model_name: str):
    """Run benchmark with a specific model and return results."""
    
    if not PYDANTIC_AI_AVAILABLE:
        raise ImportError("Pydantic AI is required but not available. Install with: pip install pydantic-ai[anthropic]")
    
    print(f"\n{'='*60}")
    print(f"🤖 Running Benchmark with {model_name}")
    print(f"{'='*60}")
    
    # Create multiple evaluation objectives for the 1984 book question
    
    # Objective 1: Response correctness evaluation (Boolean)
    response_correctness_objective = LLMJudgeObjective(
        name="response_correctness",
        description="Evaluates if the response correctly identifies the author of 1984",
        output_key="answer",  # Pydantic AI agent returns structured output with 'answer' field
        goal="Correctly identify George Orwell as the author of '1984'",
        prompt="""
        Evaluate this response about the novel 1984 for factual correctness.
        
        Question: {expected_output}
        Agent Response: {input}
        
        Return true if the author is correctly identified.
        {format_instructions}
        """,
        valid_eval_result_type=BoolEvalResult
    )
    
    # Objective 2: Reasoning quality evaluation (Float 0-1)
    reasoning_quality_objective = LLMJudgeObjective(
        name="reasoning_quality",
        description="Evaluates the quality and depth of reasoning provided in the response",
        output_key="reasoning",  # Pydantic AI agent returns structured output with 'reasoning' field
        goal="Provide clear, logical, and well-structured reasoning that demonstrates deep understanding of the novel's themes and context",
        prompt="""
        Evaluate the quality of reasoning provided for this literature question.
        
        Question: {expected_output}
        Agent Reasoning: {input}
        
        Consider these aspects:
        - Clarity: Is the reasoning clear and easy to follow?
        - Depth: Does it show deep understanding beyond surface facts?
        - Structure: Is the reasoning well-organized and logical?
        - Context: Does it place the novel in historical/literary context?
        - Insight: Does it provide meaningful insights about the themes?
        
        Rate the reasoning quality from 0.0 (poor) to 1.0 (excellent).
        Consider:
        - 0.0-0.2: Very poor reasoning, unclear or incorrect
        - 0.3-0.4: Below average, basic understanding
        - 0.5-0.6: Average reasoning, adequate explanation
        - 0.7-0.8: Good reasoning, shows good understanding
        - 0.9-1.0: Excellent reasoning, demonstrates deep insight
        
        {format_instructions}
        """,
        valid_eval_result_type=FloatEvalResult
    )
    
    # Combine the objectives
    combined_objective = CombinedBenchmarkObjective(
        name="1984_comprehensive_evaluation",
        description="Comprehensive evaluation of response correctness and reasoning quality for 1984 novel question",
        objectives=[response_correctness_objective, reasoning_quality_objective]
    )
    
    # Create single benchmark with combined objectives
    benchmarks = [
        Benchmark(
            name=f"1984 Novel Analysis - {model_name}",
            input_kwargs={"user_prompt": "Who wrote the novel '1984' and what is its main theme? Give a descriptive detail for this to make sure reader appreciates it"},
            objective=combined_objective,
            iterations=3,
            verbose=True,
            invoke_method="run"  # Use Pydantic AI's native async run method
        )
    ]
    
    # Create the Pydantic AI benchmarker with automatic output conversion and comprehensive logging enabled
    benchmarker = PydanticAIOmniBarmarker(
        executor_fn=agent_factory,
        executor_kwargs={},
        initial_input=benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True  # Automatically assign evaluators for statistics
    )
    
    # Run the benchmark asynchronously
    results = await benchmarker.benchmark_async(max_concurrent=2)
    
    # Extract results for comparison
    model_results = {
        'model_name': model_name,
        'benchmarker': benchmarker,
        'results': results
    }
    
    return model_results


async def run_model_comparison():
    """Run benchmarks with both Claude and GPT-4 for comparison."""
    
    print("🔬 Starting Model Parity Comparison")
    print("This will benchmark both Claude 3.5 Sonnet and GPT-4 on the same task")
    
    # Run benchmarks with both models
    claude_results = await run_benchmark_with_model(create_claude_agent, "Claude 3.5 Sonnet")
    gpt4_results = await run_benchmark_with_model(create_gpt4_agent, "GPT-4")
    
    # Print detailed results for both models
    print(f"\n{'='*60}")
    print("📊 DETAILED RESULTS")
    print(f"{'='*60}")
    
    print("\n🤖 Claude 3.5 Sonnet Results:")
    print("-" * 40)
    claude_results['benchmarker'].print_logger_details(detail_level="full")
    
    print("\n🤖 GPT-4 Results:")
    print("-" * 40)
    gpt4_results['benchmarker'].print_logger_details(detail_level="full")
    
    # Create comparison table
    create_comparison_table(claude_results, gpt4_results)
    
    return claude_results, gpt4_results


def create_comparison_table(claude_results, gpt4_results):
    """
    Create and display a comparison table of model results.
    
    📊 HOW THE CALCULATION WORKS:
    ────────────────────────────────
    1. **Response Correctness**: Boolean results converted to 0.0/1.0, then averaged
       - True → 1.0 (100%), False → 0.0 (0%)
       - Final score = (sum of all results) / (number of samples)
    
    2. **Reasoning Quality**: Float results (0.0-1.0) directly averaged
       - LLM Judge evaluates reasoning depth, clarity, structure, context, insight
       - Final score = (sum of all scores) / (number of samples)
    
    3. **Statistical Comparison**: 
       - Difference = Model_A_Score - Model_B_Score
       - Winner determined by significance thresholds (>10% for correctness, >0.1 for reasoning)
    """
    
    print(f"\n{'='*80}")
    print("📈 MODEL PARITY COMPARISON TABLE")
    print(f"{'='*80}")
    
    # Extract statistics from both models
    claude_logs = claude_results['benchmarker'].logger.get_all_logs()
    gpt4_logs = gpt4_results['benchmarker'].logger.get_all_logs()
    
    # Calculate averages for each model
    def calculate_stats(logs):
        correctness_scores = []
        reasoning_scores = []
        
        for log in logs:
            # Check metadata to determine objective type
            objective_name = log.metadata.get('objective_name', '').lower()
            
            for entry in log.entries:
                if hasattr(entry.eval_result, 'result') and entry.eval_result.result is not None:
                    if 'correctness' in objective_name:
                        if isinstance(entry.eval_result.result, bool):
                            correctness_scores.append(1.0 if entry.eval_result.result else 0.0)
                        else:
                            correctness_scores.append(float(entry.eval_result.result))
                    elif 'reasoning' in objective_name:
                        reasoning_scores.append(float(entry.eval_result.result))
        
        return {
            'correctness_avg': sum(correctness_scores) / len(correctness_scores) if correctness_scores else 0,
            'correctness_count': len(correctness_scores),
            'reasoning_avg': sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0,
            'reasoning_count': len(reasoning_scores)
        }
    
    claude_stats = calculate_stats(claude_logs)
    gpt4_stats = calculate_stats(gpt4_logs)
    
    # Display comparison table
    print(f"| {'Metric':<25} | {'Claude 3.5 Sonnet':<20} | {'GPT-4':<20} | {'Difference':<15} |")
    print(f"|{'-'*27}|{'-'*22}|{'-'*22}|{'-'*17}|")
    
    # Response Correctness
    claude_correct = claude_stats['correctness_avg']
    gpt4_correct = gpt4_stats['correctness_avg']
    correct_diff = claude_correct - gpt4_correct
    print(f"| {'Response Correctness':<25} | {claude_correct:<20.1%} | {gpt4_correct:<20.1%} | {correct_diff:+.1%}           |")
    
    # Reasoning Quality
    claude_reasoning = claude_stats['reasoning_avg']
    gpt4_reasoning = gpt4_stats['reasoning_avg']
    reasoning_diff = claude_reasoning - gpt4_reasoning
    print(f"| {'Reasoning Quality':<25} | {claude_reasoning:<20.2f} | {gpt4_reasoning:<20.2f} | {reasoning_diff:+.2f}           |")
    
    # Sample counts
    print(f"| {'Sample Count':<25} | {claude_stats['correctness_count']:<20} | {gpt4_stats['correctness_count']:<20} | {'N/A':<15} |")
    
    print(f"|{'-'*27}|{'-'*22}|{'-'*22}|{'-'*17}|")
    
    # Analysis
    print(f"\n🎯 ANALYSIS:")
    if abs(correct_diff) > 0.1:  # 10% difference threshold
        better_model = "Claude 3.5" if correct_diff > 0 else "GPT-4"
        print(f"• **Correctness Winner**: {better_model} ({abs(correct_diff):.1%} advantage)")
    else:
        print("• **Correctness**: Models perform similarly")
    
    if abs(reasoning_diff) > 0.1:  # 0.1 point difference threshold
        better_model = "Claude 3.5" if reasoning_diff > 0 else "GPT-4"
        print(f"• **Reasoning Winner**: {better_model} ({abs(reasoning_diff):.2f} point advantage)")
    else:
        print("• **Reasoning**: Models perform similarly")
    
    print(f"\n💡 This comparison demonstrates how OmniBAR enables objective model evaluation!")
    
    return {
        'claude_stats': claude_stats,
        'gpt4_stats': gpt4_stats,
        'correctness_difference': correct_diff,
        'reasoning_difference': reasoning_diff
    }


def run_sync_example():
    """Run a synchronous version for comparison (using asyncio.run wrapper)."""
    
    if not PYDANTIC_AI_AVAILABLE:
        raise ImportError("Pydantic AI is required but not available")
    
    # Since Pydantic AI is async-only, we run the async version using asyncio.run
    return asyncio.run(run_model_comparison())


def main():
    """Main function to run the model parity comparison with Pydantic AI."""
    
    if not PYDANTIC_AI_AVAILABLE:
        raise ImportError("Pydantic AI is not available! Install with: pip install pydantic-ai[anthropic] pydantic-ai[openai]")
    
    # Check for required API keys
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set! Please set your Anthropic API key to run Claude agents.")
    
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY environment variable not set! Please set your OpenAI API key to run GPT-4 agents and LLM judge evaluation.")
    
    print("🚀 Starting Model Parity Comparison Example")
    print("This will benchmark Claude 3.5 Sonnet vs GPT-4 on the same literary analysis task")
    print("Each model will be evaluated on response correctness and reasoning quality\n")
    
    # Run the model comparison - the OmniBAR logging system will handle all output
    claude_results, gpt4_results = asyncio.run(run_model_comparison())
    
    print("\n✅ Model comparison completed!")
    print("Check the comparison table above to see which model performs better on each metric.")
    
    return claude_results, gpt4_results


if __name__ == "__main__":
    main()
