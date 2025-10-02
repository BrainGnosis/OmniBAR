#!/usr/bin/env python3
"""
GPT-4 Reliability Benchmark with OmniBAR

This streamlined example focuses on a single GPT-4 (chat) agent powered by Pydantic AI.
It benchmarks the agent on a literary analysis task and evaluates:
  • Response correctness (boolean pass/fail)
  • Reasoning quality (0.0 – 1.0 scored rubric via LLM Judge)

Run it after setting an `OPENAI_API_KEY` (no Anthropic key required):

    python examples/pydantic_ai_example.py

It prints verbose benchmark logs plus an aggregated summary that you can map into
frontend dashboards such as the Reliability Control Room.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from omnibar import Benchmark
from omnibar.core.types import BoolEvalResult, FloatEvalResult
from omnibar.integrations.pydantic_ai import PydanticAIOmniBarmarker
from omnibar.objectives import CombinedBenchmarkObjective, LLMJudgeObjective

# -----------------------------------------------------------------------------
# Environment helpers
# -----------------------------------------------------------------------------

def load_environment_variables() -> bool:
    """Locate a `.env` file and load API keys."""
    search_paths = [
        Path(__file__).parent / '.env',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent.parent / '.env',
    ]

    custom_env = os.getenv('OMNIBAR_ENV_PATH')
    if custom_env:
        custom_path = Path(custom_env)
        if custom_path.exists():
            load_dotenv(custom_path)
            print(f"✅ Loaded environment variables from custom path: {custom_path}")
            return True
        print(f"⚠️  Custom env path not found: {custom_path}")

    for env_path in search_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            return True

    print("⚠️  No .env file found in common locations")
    print("💡  Set OMNIBAR_ENV_PATH or export OPENAI_API_KEY directly")
    return False


# -----------------------------------------------------------------------------
# Agent + objectives
# -----------------------------------------------------------------------------

class AgentResponse(BaseModel):
    """Structured fields used by OmniBAR objectives."""

    answer: str = Field(description="Concise answer to the user's question")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Supporting reasoning or evidence")


def create_gpt4_agent() -> Agent:
    """Factory for a GPT-4o chat agent that yields structured outputs."""

    return Agent(
        model=OpenAIChatModel('gpt-4o'),
        output_type=AgentResponse,
        instructions=(
            "You are a literary analyst. Provide an `answer`, `reasoning`, and a `confidence` score between 0 and 1. "
            "Keep reasoning factual and avoid speculation."
        ),
    )


def build_combined_objective() -> CombinedBenchmarkObjective:
    """Create two LLM-judge objectives and combine them."""

    response_correctness = LLMJudgeObjective(
        name='response_correctness',
        description="Checks whether the author of 1984 is correctly identified",
        output_key='answer',
        goal="Identify George Orwell as the author of '1984'",
        prompt="""
            Evaluate this answer about the novel 1984 for factual correctness.

            Question: {expected_output}
            Agent Answer: {input}

            Return true if the author is correctly identified.
            {format_instructions}
        """,
        valid_eval_result_type=BoolEvalResult,
    )

    reasoning_quality = LLMJudgeObjective(
        name='reasoning_quality',
        description="Scores depth and clarity of reasoning",
        output_key='reasoning',
        goal=(
            "Provide clear, logical reasoning that demonstrates understanding of 1984's themes, "
            "historical context, and literary significance"
        ),
        prompt="""
            Evaluate the reasoning provided for this literature question.

            Question: {expected_output}
            Agent Reasoning: {input}

            Consider clarity, depth, structure, contextual accuracy, and insight.
            Rate from 0.0 (poor) to 1.0 (excellent).
            {format_instructions}
        """,
        valid_eval_result_type=FloatEvalResult,
    )

    return CombinedBenchmarkObjective(
        name='1984_comprehensive_evaluation',
        description='Combined evaluation of correctness and reasoning quality',
        objectives=[response_correctness, reasoning_quality],
    )


# -----------------------------------------------------------------------------
# Benchmark execution
# -----------------------------------------------------------------------------

async def run_gpt4_benchmark(iterations: int = 3):
    """Execute the GPT-4 benchmark asynchronously and return the benchmarker."""

    print("\n🔬 Starting GPT-4 Reliability Evaluation")

    benchmark = Benchmark(
        name='1984 Novel Analysis - GPT-4',
        input_kwargs={
            'user_prompt': (
                "Who wrote the novel '1984'? Explain its central theme in a way that helps a business leader appreciate it."
            )
        },
        objective=build_combined_objective(),
        iterations=iterations,
        verbose=True,
        invoke_method='run',
    )

    benchmarker = PydanticAIOmniBarmarker(
        executor_fn=create_gpt4_agent,
        executor_kwargs={},
        initial_input=[benchmark],
        enable_logging=True,
        auto_assign_evaluators=True,
    )

    await benchmarker.benchmark_async(max_concurrent=2)
    return benchmarker


def summarize_benchmarks(benchmarker: PydanticAIOmniBarmarker) -> None:
    """Compute and print aggregated correctness/reasoning stats."""

    logs = benchmarker.logger.get_all_logs()
    correctness_scores: list[float] = []
    reasoning_scores: list[float] = []

    for log in logs:
        objective_name = log.metadata.get('objective_name', '').lower()
        for entry in log.entries:
            result = getattr(entry.eval_result, 'result', None)
            if result is None:
                continue
            if 'correctness' in objective_name:
                correctness_scores.append(1.0 if bool(result) else 0.0)
            elif 'reasoning' in objective_name:
                reasoning_scores.append(float(result))

    def describe(label: str, values: list[float]) -> str:
        if not values:
            return f"- {label}: no successful evaluations"
        avg = sum(values) / len(values)
        return f"- {label}: {avg:.2%} avg over {len(values)} runs" if label == 'Correctness' else f"- {label}: {avg:.2f} avg over {len(values)} runs"

    print("\n📈 GPT-4 Benchmark Summary")
    print(describe('Correctness', correctness_scores))
    print(describe('Reasoning quality', reasoning_scores))


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

def main() -> None:
    load_environment_variables()

    if not os.getenv('OPENAI_API_KEY'):
        raise EnvironmentError('OPENAI_API_KEY environment variable not set. Please export it before running.')

    benchmarker = asyncio.run(run_gpt4_benchmark())

    print("\n============================================================")
    print("📊 DETAILED GPT-4 LOGS")
    print("============================================================")
    benchmarker.print_logger_details(detail_level='full')

    summarize_benchmarks(benchmarker)
    print("\n✅ GPT-4 reliability benchmark complete!")


if __name__ == '__main__':
    main()
