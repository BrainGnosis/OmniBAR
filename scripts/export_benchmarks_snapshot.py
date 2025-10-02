"""Utilities for generating OmniBAR benchmark snapshots and suite runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Tuple

from omnibar import Benchmark
from omnibar.core.benchmarker import OmniBarmarker
from omnibar.core.types import BoolEvalResult
from omnibar.objectives import CombinedBenchmarkObjective, RegexMatchObjective, StringEqualityObjective

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
# Suite runners
# ---------------------------------------------------------------------------


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
                if evaluated_output:
                    # Rough token estimate based on json length
                    try:
                        encoded = json.dumps(evaluated_output)
                    except TypeError:
                        encoded = str(evaluated_output)
                    stats["token_counts"].append(max(len(encoded) // 4, 1))
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
    summary = {"total": 0, "success": 0, "failed": 0}

    for benchmark_id, data in results.items():
        total = data["iterations"]
        failure_flag = data.get("failure_flag", False)
        success_count = 0 if failure_flag else total
        success_rate = success_count / total if total else 0.0
        status = "success" if not failure_flag else "failed"

        summary["total"] += 1
        summary["success"] += 1 if status == "success" else 0
        summary["failed"] += 1 if status == "failed" else 0

        avg_latency = sum(data.get("latencies", [])) / len(data.get("latencies", [])) if data.get("latencies") else 0.0
        avg_tokens = sum(data.get("token_counts", [])) / len(data.get("token_counts", [])) if data.get("token_counts") else 0.0
        cost_usd = round((avg_tokens / 1000) * 0.003, 6)
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
    return payload


def get_suite_runs(suite: str) -> List[SuiteRun]:
    if suite == "custom":
        return run_custom_agents_suite()
    if suite == "crisis":
        return run_crisis_command_suite()
    runs: List[SuiteRun] = [run_output_evaluation_suite(), run_translation_suite()]
    if suite == "all":
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
