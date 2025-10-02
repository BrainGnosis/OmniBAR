"""Utilities for generating OmniBAR benchmark snapshots and suite runs."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Tuple
from uuid import uuid4

from omnibar import Benchmark
from omnibar.core.benchmarker import OmniBarmarker
from omnibar.core.types import BoolEvalResult
from omnibar.objectives import CombinedBenchmarkObjective, RegexMatchObjective, StringEqualityObjective

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None


LOGGER = logging.getLogger(__name__)


def _strtobool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


LLM_BENCHMARKS_ENABLED = _strtobool(os.getenv("OMNIBAR_ENABLE_OPENAI_BENCHMARKS"))
DEFAULT_LLM_MODEL = os.getenv("OMNIBAR_OPENAI_BENCHMARK_MODEL", "gpt-4o-mini")
DEFAULT_LLM_TEMPERATURE = float(os.getenv("OMNIBAR_OPENAI_BENCHMARK_TEMPERATURE", "0"))
DEFAULT_LLM_MAX_TOKENS = int(os.getenv("OMNIBAR_OPENAI_BENCHMARK_MAX_TOKENS", "512"))
OPENAI_COST_PER_1K_TOKENS = float(os.getenv("OMNIBAR_OPENAI_COST_PER_1K", "0.003"))
LLM_BUDGET_USD = float(os.getenv("OMNIBAR_OPENAI_BUDGET_USD", "0"))

SPEND_TRACKER_PATH = Path("backend/data/openai_spend.json")
SPEND_EVENT_LIMIT = 200

_OPENAI_SUITE_CLIENT: Any | None = None


def _get_openai_suite_client() -> Any | None:
    """Return a cached OpenAI client when LLM benchmarks are enabled and configured."""

    global _OPENAI_SUITE_CLIENT

    if not LLM_BENCHMARKS_ENABLED:
        return None

    if OpenAI is None:
        LOGGER.warning("OpenAI SDK not installed; disabling LLM-backed benchmarks.")
        return None

    if _OPENAI_SUITE_CLIENT is not None:
        return _OPENAI_SUITE_CLIENT

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        LOGGER.warning("OPENAI_API_KEY missing; disabling LLM-backed benchmarks.")
        return None

    project = os.getenv("OPENAI_PROJECT")

    try:
        _OPENAI_SUITE_CLIENT = OpenAI(api_key=api_key, project=project) if project else OpenAI(api_key=api_key)
    except Exception as error:  # pragma: no cover - defensive
        LOGGER.warning("Failed to initialize OpenAI client for benchmarks: %s", error)
        _OPENAI_SUITE_CLIENT = None

    return _OPENAI_SUITE_CLIENT


def _load_spend_tracker() -> dict[str, Any]:
    if not SPEND_TRACKER_PATH.exists():
        return {
            "total_spend_usd": 0.0,
            "events": [],
            "budget_usd": LLM_BUDGET_USD,
            "remaining_budget_usd": LLM_BUDGET_USD if LLM_BUDGET_USD > 0 else None,
        }

    try:
        with SPEND_TRACKER_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as error:  # pragma: no cover - defensive
        LOGGER.warning("Failed to read spend tracker: %s", error)
        return {
            "total_spend_usd": 0.0,
            "events": [],
            "budget_usd": LLM_BUDGET_USD,
            "remaining_budget_usd": LLM_BUDGET_USD if LLM_BUDGET_USD > 0 else None,
        }

    data.setdefault("events", [])
    data.setdefault("total_spend_usd", 0.0)
    data["budget_usd"] = LLM_BUDGET_USD
    if LLM_BUDGET_USD > 0:
        data["remaining_budget_usd"] = max(LLM_BUDGET_USD - float(data["total_spend_usd"]), 0.0)
    else:
        data["remaining_budget_usd"] = None
    return data


def _store_spend_tracker(tracker: dict[str, Any]) -> None:
    tracker["budget_usd"] = LLM_BUDGET_USD
    if LLM_BUDGET_USD > 0:
        tracker["remaining_budget_usd"] = max(LLM_BUDGET_USD - float(tracker.get("total_spend_usd", 0.0)), 0.0)
    else:
        tracker["remaining_budget_usd"] = None

    try:
        SPEND_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SPEND_TRACKER_PATH.open("w", encoding="utf-8") as handle:
            json.dump(tracker, handle, indent=2)
    except Exception as error:  # pragma: no cover - defensive
        LOGGER.warning("Failed to persist spend tracker: %s", error)


def _record_usage_cost(
    *,
    source: str,
    detail: str,
    total_tokens: int | None,
    cost_override_usd: float | None = None,
) -> dict[str, Any] | None:
    if cost_override_usd is not None:
        cost_usd = float(cost_override_usd)
    elif total_tokens is not None:
        cost_usd = float(total_tokens) / 1000.0 * OPENAI_COST_PER_1K_TOKENS
    else:
        return None

    tracker = _load_spend_tracker()
    tracker["total_spend_usd"] = float(tracker.get("total_spend_usd", 0.0)) + cost_usd

    events = tracker.setdefault("events", [])
    events.insert(
        0,
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "source": source,
            "detail": detail,
            "tokens": total_tokens,
            "cost_usd": round(cost_usd, 6),
        },
    )
    if len(events) > SPEND_EVENT_LIMIT:
        del events[SPEND_EVENT_LIMIT:]

    _store_spend_tracker(tracker)

    total_spend = tracker.get("total_spend_usd", 0.0)
    remaining = tracker.get("remaining_budget_usd")

    if LLM_BUDGET_USD > 0:
        if total_spend >= LLM_BUDGET_USD:
            LOGGER.warning(
                "OpenAI spend %.2f USD reached configured budget %.2f USD.",
                total_spend,
                LLM_BUDGET_USD,
            )
        elif total_spend >= 0.8 * LLM_BUDGET_USD:
            LOGGER.warning(
                "OpenAI spend %.2f USD is at 80%% of configured budget %.2f USD.",
                total_spend,
                LLM_BUDGET_USD,
            )

    return {
        "cost_usd": round(cost_usd, 6),
        "total_spend_usd": round(total_spend, 6),
        "remaining_budget_usd": None if remaining is None else round(remaining, 6),
    }

SuiteRun = Tuple[str, OmniBarmarker]


# ---------------------------------------------------------------------------
# Demo agents reused across suites
# ---------------------------------------------------------------------------


class ArithmeticAgent:
    def __init__(self) -> None:
        self.answers = {
            "7+8": {
                "answer": "15",
                "status": "success",
                "explanation": "Adding 7 + 8 = 15",
            },
            "12*4": {
                "answer": "48",
                "status": "success",
                "explanation": "Multiplying 12 × 4 = 48",
            },
            "5*5": {
                "answer": "20",
                "status": "error",
                "explanation": "Multiplying 5 × 5 = 20",
            },
            "4*6": {
                "answer": "24",
                "status": "success",
                "explanation": "Multiplying 4 × 6 = 24",
            },
        }

    def invoke(self, problem: str) -> dict[str, Any]:
        return self.answers.get(
            problem,
            {
                "problem": problem,
                "answer": None,
                "status": "unknown",
                "explanation": "Agent had no canned reply.",
            },
        )


class TranslationAgent:
    def __init__(self) -> None:
        self.translations = {"hello:spanish": "hola"}

    def invoke(self, word: str, target_language: str) -> dict[str, Any]:
        key = f"{word}:{target_language}"
        translation = self.translations.get(key)
        return {
            "original_word": word,
            "target_language": target_language,
            "translation": translation,
            "status": "translated" if translation else "missing",
        }


class WeatherAgent:
    def __init__(self) -> None:
        self.weather = {
            "New York": {
                "city": "New York",
                "temperature": 72,
                "condition": "sunny",
                "humidity": 45,
                "response": "The weather in New York is sunny with a temperature of 72°F",
                "status": "found",
            }
        }

    def get_weather(self, city: str) -> dict[str, Any]:
        return self.weather.get(
            city,
            {
                "city": city,
                "temperature": None,
                "condition": "unknown",
                "humidity": None,
                "response": f"Weather data for {city} is not available",
                "status": "not_found",
            },
        )


class SimpleTranslatorAgent:
    def invoke(self, word: str, target_language: str) -> dict[str, Any]:
        if word == "hello" and target_language == "spanish":
            return {
                "original_word": word,
                "target_language": target_language,
                "translation": "hola",
                "confidence": "high",
            }
        return {
            "original_word": word,
            "target_language": target_language,
            "translation": None,
            "confidence": "low",
        }


# ---------------------------------------------------------------------------
# Additional demo agents for expanded datasets
# ---------------------------------------------------------------------------


class MathReasoningAgent:
    """Synthetic math reasoning agent with canned solutions for benchmark demos."""

    def __init__(self) -> None:
        self.solutions = {
            "quadratic_roots": {
                "answer": "x = 2 or x = -2",
                "status": "success",
                "explanation": "Solve x^2 - 4 = 0 by factoring into (x - 2)(x + 2) = 0, so x = ±2.",
            },
            "combinatorics_arrangements": {
                "answer": "30",
                "status": "success",
                "explanation": "LEVEL has 5 letters with L repeated twice and E twice: 5! / (2! * 2!) = 30 unique orderings.",
            },
            "limit_sine": {
                "answer": "1",
                "status": "success",
                "explanation": "Using the standard limit lim_{x->0} sin(x)/x = 1.",
            },
        }

    def solve(self, problem: str) -> dict[str, Any]:
        return self.solutions.get(
            problem,
            {
                "problem": problem,
                "answer": None,
                "status": "unknown",
                "explanation": "Problem not available in demo dataset.",
            },
        )


class CodingChallengeAgent:
    """Synthetic coding agent that returns representative code snippets for demos."""

    def __init__(self) -> None:
        self.templates = {
            "fibonacci_sequence": {
                "code": (
                    "def fibonacci(n: int) -> list[int]:\n"
                    "    sequence = [0, 1]\n"
                    "    for _ in range(2, n):\n"
                    "        sequence.append(sequence[-1] + sequence[-2])\n"
                    "    return sequence[:n]\n"
                ),
                "language": "python",
                "status": "ready",
            },
            "anagram_checker": {
                "code": (
                    "def are_anagrams(word_a: str, word_b: str) -> bool:\n"
                    "    normalized_a = ''.join(sorted(word_a.lower()))\n"
                    "    normalized_b = ''.join(sorted(word_b.lower()))\n"
                    "    return normalized_a == normalized_b\n"
                ),
                "language": "python",
                "status": "ready",
            },
            "matrix_trace": {
                "code": (
                    "def matrix_trace(matrix: list[list[int]]) -> int:\n"
                    "    return sum(row[i] for i, row in enumerate(matrix))\n"
                ),
                "language": "python",
                "status": "ready",
            },
        }

    def generate(self, task: str) -> dict[str, Any]:
        return self.templates.get(
            task,
            {
                "task": task,
                "code": "",
                "language": "python",
                "status": "unknown",
            },
        )


# ---------------------------------------------------------------------------
# Suite runners
# ---------------------------------------------------------------------------


MATH_PROBLEM_PROMPTS: dict[str, str] = {
    "quadratic_roots": (
        "Solve the equation x^2 - 4 = 0. Provide both real roots and"
        " explain the factoring method you used."
    ),
    "combinatorics_arrangements": (
        "How many distinct arrangements of the letters in the word LEVEL"
        " are there? Show the factorial expression you relied on."
    ),
    "limit_sine": (
        "Evaluate the limit as x approaches 0 of sin(x) / x and explain"
        " the reasoning."
    ),
}


CODING_TASK_PROMPTS: dict[str, str] = {
    "fibonacci_sequence": (
        "Write a Python function named fibonacci that takes an integer n"
        " and returns a list containing the first n Fibonacci numbers."
    ),
    "anagram_checker": (
        "Write a Python function are_anagrams(word_a, word_b) that"
        " returns True when the inputs are anagrams (case-insensitive) and"
        " False otherwise. Normalize the inputs before comparison."
    ),
    "matrix_trace": (
        "Write a Python function matrix_trace(matrix) that computes the"
        " trace of a square matrix represented as a list of lists."
    ),
}


class OpenAIMathReasoningAgent:
    """Send math problems to OpenAI and coerce JSON aligned with benchmark objectives."""

    def __init__(
        self,
        client: OpenAI,
        *,
        model: str = DEFAULT_LLM_MODEL,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
        max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
    ) -> None:
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def solve(self, problem: str) -> dict[str, Any]:
        prompt = MATH_PROBLEM_PROMPTS.get(problem)
        if prompt is None:
            return {
                "problem": problem,
                "answer": None,
                "status": "unknown",
                "explanation": "Problem not configured for OpenAI math benchmarks.",
            }

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert math assistant. Respond strictly with a JSON object"
                            " containing keys 'answer', 'explanation', and 'status'. When the"
                            " solution is correct, set status to 'success'. If you cannot solve the"
                            " problem, set status to 'error' and provide a brief explanation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as error:  # pragma: no cover - network failure path
            return {
                "problem": problem,
                "answer": None,
                "status": "error",
                "explanation": f"OpenAI request failed: {error}",
            }

        content = response.choices[0].message.content if response.choices else ""

        try:
            payload = json.loads(content)
        except Exception as error:
            return {
                "problem": problem,
                "answer": None,
                "status": "error",
                "explanation": f"Invalid JSON from OpenAI: {error}",
                "raw_output": content,
            }

        answer = payload.get("answer")
        explanation = payload.get("explanation")
        status = payload.get("status", "error")

        call_id = str(uuid4())
        result: dict[str, Any] = {
            "call_id": call_id,
            "problem": problem,
            "answer": answer,
            "status": status,
            "explanation": explanation,
            "raw_output": content,
        }

        usage = getattr(response, "usage", None)
        total_tokens = None
        if usage is not None:
            total_tokens = getattr(usage, "total_tokens", None)
            result["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": total_tokens,
            }

        spend_snapshot = _record_usage_cost(
            source="math_reasoning",
            detail=problem,
            total_tokens=total_tokens,
            cost_override_usd=payload.get("cost_usd"),
        )

        if spend_snapshot is not None:
            result["cost_usd"] = spend_snapshot.get("cost_usd")
            result["total_spend_usd"] = spend_snapshot.get("total_spend_usd")
            result["remaining_budget_usd"] = spend_snapshot.get("remaining_budget_usd")

        return result


class OpenAICodingChallengeAgent:
    """Generate coding solutions via OpenAI while enforcing the benchmark schema."""

    def __init__(
        self,
        client: OpenAI,
        *,
        model: str = DEFAULT_LLM_MODEL,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
        max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
    ) -> None:
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, task: str) -> dict[str, Any]:
        prompt = CODING_TASK_PROMPTS.get(task)
        if prompt is None:
            return {
                "task": task,
                "code": "",
                "language": "python",
                "status": "unknown",
                "explanation": "Task not configured for OpenAI coding benchmarks.",
            }

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior Python developer. Respond with a JSON object containing"
                            " keys 'code', 'language', 'status', and optionally 'explanation'."
                            " Emit valid Python code in the 'code' field. For successful solutions"
                            " set status to 'ready' and language to 'python'."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as error:  # pragma: no cover - network failure path
            return {
                "task": task,
                "code": "",
                "language": "python",
                "status": "error",
                "explanation": f"OpenAI request failed: {error}",
            }

        content = response.choices[0].message.content if response.choices else ""

        try:
            payload = json.loads(content)
        except Exception as error:
            return {
                "task": task,
                "code": "",
                "language": "python",
                "status": "error",
                "explanation": f"Invalid JSON from OpenAI: {error}",
                "raw_output": content,
            }

        code = payload.get("code", "")
        language = payload.get("language", "python")
        status = payload.get("status", "error")
        explanation = payload.get("explanation")

        call_id = str(uuid4())
        result: dict[str, Any] = {
            "call_id": call_id,
            "task": task,
            "code": code,
            "language": language,
            "status": status,
            "explanation": explanation,
            "raw_output": content,
        }

        usage = getattr(response, "usage", None)
        total_tokens = None
        if usage is not None:
            total_tokens = getattr(usage, "total_tokens", None)
            result["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": total_tokens,
            }

        spend_snapshot = _record_usage_cost(
            source="coding_challenges",
            detail=task,
            total_tokens=total_tokens,
            cost_override_usd=payload.get("cost_usd"),
        )

        if spend_snapshot is not None:
            result["cost_usd"] = spend_snapshot.get("cost_usd")
            result["total_spend_usd"] = spend_snapshot.get("total_spend_usd")
            result["remaining_budget_usd"] = spend_snapshot.get("remaining_budget_usd")

        return result


def run_output_evaluation_suite() -> SuiteRun:
    agent = ArithmeticAgent()
    benchmarks = [
        Benchmark(
            name="Addition Accuracy",
            input_kwargs={"problem": "7+8"},
            objective=StringEqualityObjective(
                name="equals_15",
                output_key="answer",
                goal="15",
            ),
            iterations=3,
        ),
        Benchmark(
            name="Multiplication Explanation",
            input_kwargs={"problem": "4*6"},
            objective=RegexMatchObjective(
                name="explanation_pattern",
                output_key="explanation",
                goal=r"Multiplying \d+ × \d+ = \d+",
                valid_eval_result_type=BoolEvalResult,
            ),
            iterations=2,
        ),
        Benchmark(
            name="Comprehensive Calculator Test",
            input_kwargs={"problem": "4*6"},
            objective=CombinedBenchmarkObjective(
                name="calculator_combined",
                objectives=[
                    StringEqualityObjective(
                        name="correct_answer",
                        output_key="answer",
                        goal="24",
                    ),
                    StringEqualityObjective(
                        name="success_status",
                        output_key="status",
                        goal="success",
                    ),
                    RegexMatchObjective(
                        name="valid_explanation",
                        output_key="explanation",
                        goal=r".*\d+.*=.*\d+.*",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                ],
            ),
            iterations=1,
        ),
    ]

    marker = OmniBarmarker(
        executor_fn=lambda: agent,
        executor_kwargs={},
        agent_invoke_method_name="invoke",
        initial_input=benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    marker.benchmark()
    return "output_evaluation", marker


def run_translation_suite() -> SuiteRun:
    agent = TranslationAgent()

    objective = CombinedBenchmarkObjective(
        name="translation_health",
        objectives=[
            StringEqualityObjective(
                name="exact_translation",
                output_key="translation",
                goal="hola",
            ),
            RegexMatchObjective(
                name="status_flag",
                output_key="status",
                goal=r"translated",
                valid_eval_result_type=BoolEvalResult,
            ),
        ],
    )

    benchmark = Benchmark(
        name="Spanish Greeting",
        input_kwargs={"word": "hello", "target_language": "spanish"},
        objective=objective,
        iterations=1,
    )

    marker = OmniBarmarker(
        executor_fn=lambda: agent,
        executor_kwargs={},
        agent_invoke_method_name="invoke",
        initial_input=[benchmark],
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    marker.benchmark()
    return "output_evaluation", marker


def run_custom_agents_suite() -> List[SuiteRun]:
    weather_agent = WeatherAgent()
    weather_benchmarks = [
        Benchmark(
            name="Weather Success",
            input_kwargs={"city": "New York"},
            objective=RegexMatchObjective(
                name="mentions_sunny",
                output_key="response",
                goal=r"sunny",
                valid_eval_result_type=BoolEvalResult,
            ),
            iterations=1,
            invoke_method="get_weather",
        ),
        Benchmark(
            name="Weather Missing City",
            input_kwargs={"city": "Atlantis"},
            objective=StringEqualityObjective(
                name="marked_not_found",
                output_key="status",
                goal="not_found",
            ),
            iterations=1,
            invoke_method="get_weather",
        ),
    ]

    weather_marker = OmniBarmarker(
        executor_fn=lambda: weather_agent,
        executor_kwargs={},
        agent_invoke_method_name="get_weather",
        initial_input=weather_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    weather_marker.benchmark()

    translator_agent = SimpleTranslatorAgent()
    translator_benchmarks = [
        Benchmark(
            name="Simple Translation",
            input_kwargs={"word": "hello", "target_language": "spanish"},
            objective=StringEqualityObjective(
                name="translation_success",
                output_key="translation",
                goal="hola",
            ),
            iterations=1,
        )
    ]

    translator_marker = OmniBarmarker(
        executor_fn=lambda: translator_agent,
        executor_kwargs={},
        agent_invoke_method_name="invoke",
        initial_input=translator_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    translator_marker.benchmark()

    return [
        ("custom_agents", weather_marker),
        ("custom_agents", translator_marker),
    ]


def run_math_reasoning_suite() -> SuiteRun:
    client = _get_openai_suite_client()
    if client is not None:
        agent = OpenAIMathReasoningAgent(
            client,
            model=DEFAULT_LLM_MODEL,
            temperature=DEFAULT_LLM_TEMPERATURE,
            max_tokens=DEFAULT_LLM_MAX_TOKENS,
        )
    else:
        agent = MathReasoningAgent()
    math_benchmarks = [
        Benchmark(
            name="Quadratic Roots Reasoning",
            input_kwargs={"problem": "quadratic_roots"},
            objective=CombinedBenchmarkObjective(
                name="math_quadratic_root_checks",
                objectives=[
                    RegexMatchObjective(
                        name="mentions_factoring",
                        output_key="explanation",
                        goal=r"factor",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    RegexMatchObjective(
                        name="reports_both_roots",
                        output_key="answer",
                        goal=r"x\s*=\s*2.*-2",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="math_status_success",
                        output_key="status",
                        goal="success",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="solve",
        ),
        Benchmark(
            name="Word Arrangement Count",
            input_kwargs={"problem": "combinatorics_arrangements"},
            objective=CombinedBenchmarkObjective(
                name="math_combinatorics_checks",
                objectives=[
                    StringEqualityObjective(
                        name="correct_permutation_count",
                        output_key="answer",
                        goal="30",
                    ),
                    RegexMatchObjective(
                        name="mentions_factorial_reasoning",
                        output_key="explanation",
                        goal=r"5!",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="math_status_factorial",
                        output_key="status",
                        goal="success",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="solve",
        ),
        Benchmark(
            name="Sine Limit Evaluation",
            input_kwargs={"problem": "limit_sine"},
            objective=CombinedBenchmarkObjective(
                name="math_limit_checks",
                objectives=[
                    StringEqualityObjective(
                        name="correct_limit_value",
                        output_key="answer",
                        goal="1",
                    ),
                    RegexMatchObjective(
                        name="mentions_classic_sine_limit",
                        output_key="explanation",
                        goal=r"sin\(x\)/x",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="math_status_limit",
                        output_key="status",
                        goal="success",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="solve",
        ),
    ]

    marker = OmniBarmarker(
        executor_fn=lambda: agent,
        executor_kwargs={},
        agent_invoke_method_name="solve",
        initial_input=math_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    marker.benchmark()
    return "math_reasoning", marker


def run_coding_challenges_suite() -> SuiteRun:
    client = _get_openai_suite_client()
    if client is not None:
        agent = OpenAICodingChallengeAgent(
            client,
            model=DEFAULT_LLM_MODEL,
            temperature=DEFAULT_LLM_TEMPERATURE,
            max_tokens=DEFAULT_LLM_MAX_TOKENS,
        )
    else:
        agent = CodingChallengeAgent()
    coding_benchmarks = [
        Benchmark(
            name="Fibonacci Sequence Implementation",
            input_kwargs={"task": "fibonacci_sequence"},
            objective=CombinedBenchmarkObjective(
                name="coding_fibonacci_checks",
                objectives=[
                    RegexMatchObjective(
                        name="defines_fibonacci_function",
                        output_key="code",
                        goal=r"def\s+fibonacci",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    RegexMatchObjective(
                        name="appends_new_terms",
                        output_key="code",
                        goal=r"sequence\.append",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="coding_language_python",
                        output_key="language",
                        goal="python",
                    ),
                    StringEqualityObjective(
                        name="coding_status_ready",
                        output_key="status",
                        goal="ready",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="generate",
        ),
        Benchmark(
            name="Anagram Checker Implementation",
            input_kwargs={"task": "anagram_checker"},
            objective=CombinedBenchmarkObjective(
                name="coding_anagram_checks",
                objectives=[
                    RegexMatchObjective(
                        name="normalizes_input",
                        output_key="code",
                        goal=r"sorted\(word_a\.lower\(\)\)",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    RegexMatchObjective(
                        name="compares_normalized_strings",
                        output_key="code",
                        goal=r"normalized_a\s*==\s*normalized_b",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="coding_status_anagram",
                        output_key="status",
                        goal="ready",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="generate",
        ),
        Benchmark(
            name="Matrix Trace Helper",
            input_kwargs={"task": "matrix_trace"},
            objective=CombinedBenchmarkObjective(
                name="coding_matrix_trace_checks",
                objectives=[
                    RegexMatchObjective(
                        name="uses_enumerate",
                        output_key="code",
                        goal=r"enumerate\(matrix\)",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    RegexMatchObjective(
                        name="sums_diagonal",
                        output_key="code",
                        goal=r"row\[i\]",
                        valid_eval_result_type=BoolEvalResult,
                    ),
                    StringEqualityObjective(
                        name="coding_status_matrix",
                        output_key="status",
                        goal="ready",
                    ),
                ],
            ),
            iterations=1,
            invoke_method="generate",
        ),
    ]

    marker = OmniBarmarker(
        executor_fn=lambda: agent,
        executor_kwargs={},
        agent_invoke_method_name="generate",
        initial_input=coding_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True,
    )
    marker.benchmark()
    return "coding_challenges", marker


class InventoryCrisisAgent:
    """Simulated crisis-management agent returning structured output without external APIs."""

    def invoke(self, **kwargs) -> dict[str, Any]:
        scenario_input = kwargs.get("input", "")
        return {
            "scenario": scenario_input,
            "status": "partial_success",
            "summary": "Fulfilled 2 of 3 crisis orders; remaining laptops delayed due to capacity bottleneck.",
            "path_score": 0.78,
            "state_score": 0.92,
            "confidence": 0.64,
            "execution_path": [
                ("request_shipment", {"warehouse": "WH003", "items": {"ITEM001": 24}}),
                ("receive_shipment", {"request_id": "REQ_A1", "received": {"ITEM001": 24}}),
                ("move_to_showroom", {"from": "WH003", "to": "SR003", "item": "ITEM001", "qty": 12}),
                ("transfer_warehouse", {"from": "WH003", "to": "WH001", "item": "ITEM001", "qty": 8}),
            ],
        }


def run_crisis_command_suite() -> List[SuiteRun]:
    agent = InventoryCrisisAgent()

    status_objective = StringEqualityObjective(
        name="crisis_status",
        output_key="status",
        goal="success",
    )

    summary_objective = RegexMatchObjective(
        name="crisis_summary_contains",
        output_key="summary",
        goal=r"Fulfilled .* crisis orders",
        valid_eval_result_type=BoolEvalResult,
    )

    combined_objective = CombinedBenchmarkObjective(
        name="crisis_command_combined",
        objectives=[status_objective, summary_objective],
    )

    crisis_benchmark = Benchmark(
        name="Crisis Command Suite",
        input_kwargs={
            "input": (
                "Emergency supply chain crisis: fulfill Orders A, B, C across SR001-003 under severe capacity constraints. "
                "Ensure laptop parity, respect priority ordering, and document any shortfalls."
            )
        },
        objective=combined_objective,
        iterations=1,
        invoke_method="invoke",
    )

    marker = OmniBarmarker(
        executor_fn=lambda: agent,
        executor_kwargs={},
        agent_invoke_method_name="invoke",
        initial_input=[crisis_benchmark],
        enable_logging=True,
        auto_assign_evaluators=True,
    )

    marker.benchmark()
    return [("crisis_command", marker)]


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------


def compute_results(suites: List[SuiteRun]) -> dict[str, dict[str, Any]]:
    aggregated: dict[str, dict[str, Any]] = {}

    for suite_name, marker in suites:
        for benchmark in marker.initial_input:
            aggregated[str(benchmark.uuid)] = {
                "name": benchmark.name,
                "iterations": benchmark.iterations,
                "failure_flag": False,
                "suite": suite_name,
                "latencies": [],
                "token_counts": [],
                "costs": [],
                "usage_call_ids": set(),
                "confidences": [],
                "history": [],
                "error_flags": set(),
                "inputs": benchmark.input_kwargs,
                "latest_failure": None,
            }

        for log in marker.logger.get_all_logs():
            stats = aggregated.get(str(log.benchmark_id))
            if stats is None:
                continue

            latency = (log.time_ended - log.time_started).total_seconds() if log.time_ended and log.time_started else 0.0
            stats["latencies"].append(latency)

            objective_name = log.metadata.get("objective_name")
            output_key = log.metadata.get("objective_output_key")
            expected_goal = log.metadata.get("objective_goal")

            if not log.entries:
                stats["failure_flag"] = True
                stats["history"].append(
                    {
                        "timestamp": log.time_started.isoformat() if log.time_started else None,
                        "objective": objective_name,
                        "result": False,
                        "message": "No evaluator entries recorded",
                        "expected": expected_goal,
                        "actual": None,
                        "failureCategory": "infrastructure",
                        "latencySeconds": latency,
                    }
                )
                continue

            for entry in log.entries:
                result = getattr(entry.eval_result, "result", None)
                success = bool(result)
                message = getattr(entry.eval_result, "message", None)

                evaluated_output = entry.evaluated_output or {}
                token_added = False
                cost_added = False

                call_id = evaluated_output.get("call_id") if isinstance(evaluated_output, dict) else None
                usage = evaluated_output.get("usage") if isinstance(evaluated_output, dict) else None
                cost_usd = evaluated_output.get("cost_usd") if isinstance(evaluated_output, dict) else None

                if call_id and call_id not in stats["usage_call_ids"]:
                    stats["usage_call_ids"].add(call_id)

                    total_tokens = None
                    if isinstance(usage, dict):
                        total_tokens = usage.get("total_tokens")
                        if total_tokens is None:
                            prompt_tokens = usage.get("prompt_tokens")
                            completion_tokens = usage.get("completion_tokens")
                            if isinstance(prompt_tokens, (int, float)) and isinstance(completion_tokens, (int, float)):
                                total_tokens = float(prompt_tokens) + float(completion_tokens)

                    if total_tokens is not None:
                        stats["token_counts"].append(float(total_tokens))
                        token_added = True

                    if cost_usd is not None:
                        stats["costs"].append(float(cost_usd))
                        cost_added = True
                    elif token_added and stats["token_counts"]:
                        stats["costs"].append(float(stats["token_counts"][-1]) / 1000.0 * OPENAI_COST_PER_1K_TOKENS)
                        cost_added = True

                if evaluated_output:
                    # Rough token estimate based on json length when usage not available
                    if not token_added:
                        try:
                            encoded = json.dumps(evaluated_output)
                        except TypeError:
                            encoded = str(evaluated_output)
                        stats["token_counts"].append(max(len(encoded) // 4, 1))
                        token_added = True
                    if not cost_added and token_added and stats["token_counts"]:
                        stats["costs"].append(float(stats["token_counts"][-1]) / 1000.0 * OPENAI_COST_PER_1K_TOKENS)
                    confidence = evaluated_output.get("confidence")
                    if isinstance(confidence, (int, float)):
                        stats["confidences"].append(float(confidence))

                actual_value = evaluated_output.get(output_key) if output_key else None

                if not success:
                    stats["failure_flag"] = True
                    failure_reason = message or (
                        f"Expected {expected_goal}, got {actual_value}" if expected_goal is not None else "Objective failed"
                    )

                    # Categorize failure heuristically
                    if actual_value in (None, "", {}, []):
                        failure_category = "format"
                    elif isinstance(actual_value, str) and actual_value.lower() in {"error", "unsupported", "not_found"}:
                        failure_category = "unsupported"
                    else:
                        failure_category = "logic"

                    stats["error_flags"].add(failure_category)
                    stats["latest_failure"] = {
                        "objective": objective_name,
                        "reason": failure_reason,
                        "category": failure_category,
                        "expected": expected_goal,
                        "actual": actual_value,
                    }
                else:
                    failure_reason = None
                    failure_category = None

                stats["history"].append(
                    {
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "objective": objective_name,
                        "result": success,
                        "message": message,
                        "expected": expected_goal,
                        "actual": actual_value,
                        "failureCategory": failure_category,
                        "latencySeconds": latency,
                    }
                )

    return aggregated


def build_api_payload(suites: List[SuiteRun]) -> dict[str, Any]:
    results = compute_results(suites)

    benchmarks_payload = []
    summary = {"total": 0, "success": 0, "failed": 0, "costUsd": 0.0}

    for benchmark_id, data in results.items():
        total = data["iterations"]
        failure_flag = data.get("failure_flag", False)
        success_count = 0 if failure_flag else total
        success_rate = success_count / total if total else 0.0
        status = "success" if not failure_flag else "failed"

        summary["total"] += 1
        summary["success"] += 1 if status == "success" else 0
        summary["failed"] += 1 if status == "failed" else 0

        latencies = data.get("latencies", [])
        token_counts = data.get("token_counts", [])
        cost_samples = data.get("costs", [])

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        avg_tokens = float(sum(token_counts) / len(token_counts)) if token_counts else 0.0
        avg_cost = sum(cost_samples) / len(cost_samples) if cost_samples else (avg_tokens / 1000.0) * OPENAI_COST_PER_1K_TOKENS
        cost_usd = round(avg_cost, 6)
        summary["costUsd"] += cost_usd
        avg_confidence = sum(data.get("confidences", [])) / len(data.get("confidences", [])) if data.get("confidences") else None
        error_flags_raw = data.get("error_flags") or []
        if isinstance(error_flags_raw, set):
            error_flags = sorted(error_flags_raw)
        else:
            error_flags = list(error_flags_raw)
        latest_failure = data.get("latest_failure")

        benchmarks_payload.append(
            {
                "id": benchmark_id,
                "name": data["name"],
                "iterations": total,
                "successRate": round(success_rate, 2),
                "status": status,
                "updatedAt": datetime.now(UTC).isoformat(),
                "suite": data.get("suite", "default"),
                "latencySeconds": round(avg_latency, 3),
                "tokensUsed": round(avg_tokens, 2),
                "costUsd": cost_usd,
                "confidenceReported": round(avg_confidence, 3) if avg_confidence is not None else None,
                "confidenceCalibrated": round(success_rate, 3),
                "errorFlags": error_flags,
                "history": data.get("history", []),
                "inputs": data.get("inputs", {}),
                "latestFailure": latest_failure,
            }
        )

    now = datetime.now(UTC).isoformat()
    failure_insights = []
    recommendations = []

    for benchmark in benchmarks_payload:
        if benchmark["status"] != "success":
            latest_failure = benchmark.get("latestFailure") or {}
            failure_insights.append(
                {
                    "id": f"issue-{benchmark['id'][:8]}",
                    "benchmarkId": benchmark["id"],
                    "benchmarkName": benchmark["name"],
                    "failureRate": 1 - benchmark["successRate"],
                    "lastFailureAt": now,
                    "topIssues": [
                        latest_failure.get("reason", "Mismatch between expected and actual outputs."),
                        "Agent requires regression coverage for this flow.",
                    ],
                    "recommendedFix": "Tighten validation and adjust prompt/tool usage for this scenario.",
                    "failureCategory": latest_failure.get("category"),
                    "inputs": benchmark.get("inputs"),
                    "history": benchmark.get("history", []),
                }
            )
            recommendations.append(
                {
                    "id": f"rec-{benchmark['id'][:8]}",
                    "title": f"Restore {benchmark['name']}",
                    "impact": "High impact · Medium effort",
                    "summary": latest_failure.get("reason", "Failures in this scenario affect reliability scorecards."),
                    "action": "Add OmniBAR regression test and rerun after fixing agent logic.",
                }
            )

    payload = {
        "generatedAt": now,
        "summary": summary,
        "benchmarks": benchmarks_payload,
        "liveRuns": [],
        "failureInsights": failure_insights,
        "recommendations": recommendations,
    }

    spend_snapshot = _load_spend_tracker()
    if spend_snapshot:
        events = spend_snapshot.get("events") or []
        last_event = events[0] if events else None
        payload["openaiSpend"] = {
            "totalUsd": round(float(spend_snapshot.get("total_spend_usd", 0.0)), 6),
            "budgetUsd": spend_snapshot.get("budget_usd"),
            "remainingUsd": spend_snapshot.get("remaining_budget_usd"),
            "lastEvent": last_event,
        }

    return payload


def get_suite_runs(suite: str) -> List[SuiteRun]:
    if suite == "custom":
        return run_custom_agents_suite()
    if suite == "crisis":
        return run_crisis_command_suite()
    if suite == "math":
        return [run_math_reasoning_suite()]
    if suite == "coding":
        return [run_coding_challenges_suite()]
    runs: List[SuiteRun] = [run_output_evaluation_suite(), run_translation_suite()]
    if suite == "all":
        runs.append(run_math_reasoning_suite())
        runs.append(run_coding_challenges_suite())
        runs.extend(run_custom_agents_suite())
        runs.extend(run_crisis_command_suite())
    return runs


def generate_benchmark_snapshot(suite: str = "output") -> dict[str, Any]:
    suites = get_suite_runs(suite)
    return build_api_payload(suites)


def save_snapshot(target: Path | None = None, suite: str = "output") -> dict[str, Any]:
    payload = generate_benchmark_snapshot(suite=suite)
    output_path = target or Path("frontend/public/api/benchmarks.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"✅ Exported benchmark snapshot to {output_path}")
    return payload


if __name__ == "__main__":
    save_snapshot()
