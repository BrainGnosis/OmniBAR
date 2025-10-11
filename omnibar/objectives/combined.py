# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any, Type, List
from pydantic import Field, model_validator, BaseModel, PrivateAttr, InstanceOf
import inspect
import asyncio
from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult,
    BoolEvalResult,
    InvalidEvalResult
)
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, BaseOutputParser
from langchain_core.runnables import Runnable

from omnibar.core.types import ExtractionError, OutputKeyNotFoundError

class CombinedBenchmarkObjective(BaseBenchmarkObjective):
    """
    CombinedBenchmarkObjective is a benchmark objective that combines multiple benchmark objectives.
    """
    objectives: List[InstanceOf[BaseBenchmarkObjective]]
    
    # These fields are excluded as they are handled by individual objectives
    goal: Any = Field(default=None, exclude=True, description="Not used in combined objectives")
    output_key: str = Field(default="", exclude=True, description="Not used in combined objectives")
    valid_eval_result_type: Type = Field(default=dict, exclude=True, description="Not used in combined objectives")

    
    def _eval_fn(self, formatted_output: Dict[str, Any], **kwargs) -> Dict[str, EvalResult]:
        """
        Evaluation function that combines the evaluation functions of the individual objectives.
        Returns a dict mapping each objective's UUID to its EvalResult.
        """
        results = {}
        for objective in self.objectives:
            result = objective.eval(formatted_output)
            # Use the UUID of the objective as the key
            results[str(objective.uuid)] = result
        return results
    
    def _extract_filtered_output(self, agent_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Passes the agent output through and the extraction is handled in the individual objectives.
        """
        return agent_output
    
    def _format_filtered_output(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Passes the filtered output through and the formatting is handled in the individual objectives.
        """
        return filtered_output
    
    def eval(self, agent_output: Dict[str, Any]) -> Dict[str, EvalResult]:
        """
        Run the benchmark objective.
        """
        #format, filter, eval

        filtered_output = self._extract_filtered_output(agent_output, **self.extract_filtered_output_fn_kwargs)
        formatted_output = self._format_filtered_output(filtered_output, **self.format_filtered_output_fn_kwargs)
        eval_results = self._eval_fn(formatted_output=formatted_output, **self.eval_fn_kwargs)
        return eval_results


    async def eval_async(self, agent_output: Dict[str, Any]) -> Dict[str, EvalResult]:
        """
        Run the benchmark objective asynchronously.
        """
        #format, filter, eval
        filtered_output = await self._extract_filtered_output_async(agent_output, **self.extract_filtered_output_fn_kwargs)
        formatted_output = await self._format_filtered_output_async(filtered_output, **self.format_filtered_output_fn_kwargs)

        eval_results = await self._eval_fn_async(formatted_output=formatted_output, **self.eval_fn_kwargs)
        return eval_results

    async def _eval_fn_async(self, formatted_output: Dict[str, Any], **kwargs) -> Dict[str, EvalResult]:
        """
        Async evaluation function that combines the evaluation functions of the individual objectives.
        Returns a dict mapping each objective's UUID to its EvalResult.
        """
        # Create coroutines for all objective evaluations
        eval_coroutines = [objective.eval_async(formatted_output) for objective in self.objectives]
        
        # Run all evaluations concurrently
        eval_results = await asyncio.gather(*eval_coroutines)
        
        # Build results dictionary mapping UUIDs to results
        results = {}
        for objective, result in zip(self.objectives, eval_results):
            results[str(objective.uuid)] = result
        
        return results
        

    async def _extract_filtered_output_async(self, agent_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        This is a pass through function that passes the agent output through to the individual objectives.
        """
        return agent_output
    
    async def _format_filtered_output_async(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        This is a pass through function that passes the filtered output through to the individual objectives.
        """
        return filtered_output
    
    def run_pre_run_hook(self) -> None:
        """
        Run the pre run hook for all objectives.
        """
        for objective in self.objectives:
            objective.run_pre_run_hook()
    
    def run_post_run_hook(self) -> None:
        """
        Run the post run hook for all objectives.
        """
        for objective in self.objectives:
            objective.run_post_run_hook()
    
    def run_post_eval_hook(self) -> None:
        """
        Run the post eval hook for all objectives.
        """
        for objective in self.objectives:
            objective.run_post_eval_hook()

    async def run_pre_run_hook_async(self) -> None:
        """
        Run the pre run hook for all objectives asynchronously.
        """
        # Create coroutines for all objective pre-run hooks
        hook_coroutines = [objective.run_pre_run_hook_async() for objective in self.objectives]
        
        # Run all hooks concurrently
        await asyncio.gather(*hook_coroutines)
    
    async def run_post_run_hook_async(self) -> None:
        """
        Run the post run hook for all objectives asynchronously.
        """
        # Create coroutines for all objective post-run hooks
        hook_coroutines = [objective.run_post_run_hook_async() for objective in self.objectives]
        
        # Run all hooks concurrently
        await asyncio.gather(*hook_coroutines)
    
    async def run_post_eval_hook_async(self) -> None:
        """
        Run the post eval hook for all objectives asynchronously.
        """
        # Create coroutines for all objective post-eval hooks
        hook_coroutines = [objective.run_post_eval_hook_async() for objective in self.objectives]
        
        # Run all hooks concurrently
        await asyncio.gather(*hook_coroutines)