from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import Field

from omnibar.core.types import FloatEvalResult, InvalidEvalResult
from omnibar.objectives.llm_judge import DEFAULT_SCORE_PROMPT, LLMJudgeObjective

from ..config import Settings


@dataclass
class ScoreResult:
    score: float
    note: str
    breakdown: dict[str, Any]


class LatteJudgeObjective(LLMJudgeObjective):
    scoring_model: str = Field(default="gpt-4o-mini")
    api_key: str | None = Field(default=None)

    def _build_llm_chain(self):  # type: ignore[override]
        if isinstance(self.prompt, str):
            prompt = PromptTemplate(
                template=self.prompt,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": self._output_parser.get_format_instructions(),
                    "expected_output": self.goal,
                },
            )
        elif self.prompt is None:
            prompt = PromptTemplate(
                template=DEFAULT_SCORE_PROMPT,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": self._output_parser.get_format_instructions(),
                    "expected_output": self.goal,
                },
            )
        else:
            prompt = self.prompt

        llm = ChatOpenAI(
            model=self.scoring_model, temperature=0, max_retries=2, api_key=self.api_key
        )
        chain = prompt | llm | self._output_parser
        return chain


def _mock_score(response: str, user_prompt: str) -> ScoreResult:
    word_count = len(response.split())
    uniqueness = len(set(response.lower().split()))
    score = 0.4 + 0.6 * (
        math.tanh(word_count / 75) * 0.6 + math.tanh(uniqueness / 60) * 0.4
    )
    score = max(0.0, min(1.0, score))
    note = (
        "Mock scoring estimates quality based on response richness."
        f" Detected {word_count} words with {uniqueness} unique terms."
    )
    return ScoreResult(
        score=round(score, 3),
        note=note,
        breakdown={
            "mode": "mock",
            "word_count": word_count,
            "unique_terms": uniqueness,
        },
    )


def evaluate_with_omnibar(
    *,
    response: str,
    system_prompt: str,
    user_prompt: str,
    settings: Settings,
) -> ScoreResult:
    if settings.mock_mode or not settings.openai_api_key:
        return _mock_score(response, user_prompt)

    goal = (
        "Judge how well the assistant replied to the latte order."
        " Prioritise factual accuracy, clarity, and alignment with the system instructions."
        f" User request: {user_prompt}\nSystem guidance: {system_prompt}"
        " Score 1.0 for precise, helpful answers that follow the system prompt;"
        " score near 0 for harmful or irrelevant replies."
    )

    objective = LatteJudgeObjective(
        name="latte_quality",
        output_key="assistant",
        goal=goal,
        scoring_model=settings.scoring_model,
        api_key=settings.openai_api_key,
        valid_eval_result_type=FloatEvalResult,
        prompt=(
            "You are OmniBAR judging drinks in OmniBrew.\n"
            "Use the guidance in {expected_output} to score the assistant's reply below (0-1 scale).\n"
            "Assistant reply:\n{input}\n"
            "Respond with JSON that follows these instructions:\n{format_instructions}\n"
            "Keep the message energetic but professional."
        ),
    )

    try:
        eval_result = objective.eval({"assistant": response})
    except Exception as error:  # pragma: no cover - defensive guard
        return ScoreResult(
            score=0.0,
            note=f"Scoring failed: {error}",
            breakdown={"mode": "error", "detail": str(error)},
        )

    if isinstance(eval_result, FloatEvalResult):
        score = max(0.0, min(1.0, float(eval_result.result)))
        note = eval_result.message or "OmniBAR returned a score without commentary."
        breakdown = {
            "mode": "omnibar",
            "raw_result": float(eval_result.result),
            "message": eval_result.message,
        }
    elif isinstance(eval_result, InvalidEvalResult):
        score = 0.0
        note = f"OmniBAR reported an invalid evaluation: {eval_result.message}"
        breakdown = {
            "mode": "omnibar",
            "error": eval_result.message,
        }
    else:
        score = getattr(eval_result, "result", 0.0) or 0.0
        note = getattr(
            eval_result, "message", "OmniBAR returned an unexpected result type."
        )
        breakdown = {
            "mode": "omnibar",
            "raw_type": type(eval_result).__name__,
        }

    return ScoreResult(score=round(score, 3), note=note, breakdown=breakdown)
