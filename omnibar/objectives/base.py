# © 2023 BrainGnosis Inc. All rights reserved.

from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, Type, List
from uuid import UUID
import uuid
import inspect

from omnibar.core.types import (EvalResult, ValidEvalResult, ExtractionError, AgentOperationError, InvalidEvalResult, OutputKeyNotFoundError, FormattingError, EvaluationError, EvalTypeMismatchError)

class BaseBenchmarkObjective(BaseModel):
    '''
    Base class for benchmark objectives.
    '''
    # Goal and output key
    #TODO: We have added in additinoal fields which we need to include in tests for them to run properly
    name: str = Field(description="The name of the benchmark objective", default="")
    description: str = Field(description="A description of the benchmark objective", default="")
    category: str = Field(description="The category of the benchmark objective", default="")
    tags: List[str] = Field(description="The tags of the benchmark objective", default_factory=list)
    uuid: UUID = Field(default_factory=uuid.uuid4)
    goal: Any = Field(description="The goal of the benchmark objective")
    output_key: str = Field(description="The key of the output to be extracted from the agent's output")

    # Private function runtime kwargs
    extract_filtered_output_fn_kwargs: Dict[str, Any] = Field(default_factory=dict)
    format_filtered_output_fn_kwargs: Dict[str, Any] = Field(default_factory=dict)
    eval_fn_kwargs: Dict[str, Any] = Field(default_factory=dict)

    # Hooks
    pre_run_hook: Callable | None = None
    post_run_hook: Callable | None = None
    post_eval_hook: Callable | None = None

    # Hook kwargs
    pre_run_hook_kwargs: Dict[str, Any] = Field(default_factory=dict)
    post_run_hook_kwargs: Dict[str, Any] = Field(default_factory=dict)
    post_eval_hook_kwargs: Dict[str, Any] = Field(default_factory=dict)

    valid_eval_result_type: Type[ValidEvalResult]
    


    def _extract_filtered_output(self, agent_output: Dict[str, Any], **kwargs) -> Dict[str, Any] | OutputKeyNotFoundError | ExtractionError:
        '''
        Helper function to extract filtered output based on output_key.
        
        Args:
            agent_output: The full agent output dictionary
            
        Returns:
            Filtered output dictionary or OutputKeyNotFoundError if key not found
        '''
        try:
            filtered_output = {self.output_key: agent_output[self.output_key]}
            return filtered_output
        except KeyError as e:
            return OutputKeyNotFoundError(result=None, message=str(e))
        except Exception as e:
            return ExtractionError(result=None, message=str(e))

    def _format_filtered_output(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        '''
        Helper function to format filtered output after extrace
        '''
        return filtered_output
    
    def _eval_fn(self, goal: Any, filtered_output: Dict[str, Any], **kwargs) -> EvalResult:
        '''
        Helper function to evaluate the formatted output against the goal.
        '''
        raise NotImplementedError("Please subclass BaseBenchmarkObjective and implement _eval_fn")

    async def _extract_filtered_output_async(self, agent_output: Dict[str, Any], **kwargs) -> Dict[str, Any] | OutputKeyNotFoundError | ExtractionError:
        '''
        Async helper function to extract filtered output based on output_key.
        
        Args:
            agent_output: The full agent output dictionary
            
        Returns:
            Filtered output dictionary or OutputKeyNotFoundError if key not found
        '''
        try:
            filtered_output = {self.output_key: agent_output[self.output_key]}
            return filtered_output
        except KeyError as e:
            return OutputKeyNotFoundError(result=None, message=str(e))
        except Exception as e:
            return ExtractionError(result=None, message=str(e))

    async def _format_filtered_output_async(self, filtered_output: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        '''
        Async helper function to format filtered output after extraction
        '''
        return filtered_output
    
    async def _eval_fn_async(self, goal: Any, filtered_output: Dict[str, Any], **kwargs) -> EvalResult:
        '''
        Async helper function to evaluate the formatted output against the goal.
        '''
        raise NotImplementedError("Please subclass BaseBenchmarkObjective and implement _eval_fn_async")

    def eval(self, agent_output: Dict[str, Any]) -> EvalResult:
        '''
        Run the benchmark objective.
        '''
        # Extract filtered output, check for errors and return error result
        try:
            filtered_output = self._extract_filtered_output(agent_output, **self.extract_filtered_output_fn_kwargs)
        except Exception as e:
            self.run_post_eval_hook()
            return ExtractionError(result=None, message=str(e))
        
        # If the filtered output is an error, return the error result
        if isinstance(filtered_output, InvalidEvalResult):
            self.run_post_eval_hook()
            return filtered_output
        
        # Format filtered output, check for errors and return error result
        try:
            formatted_output = self._format_filtered_output(filtered_output, **self.format_filtered_output_fn_kwargs)
        except Exception as e:
            self.run_post_eval_hook()
            return FormattingError(result=None, message=str(e))
        
        # If the formatted output is an error, return the error result
        if isinstance(formatted_output, InvalidEvalResult):
            self.run_post_eval_hook()
            return formatted_output
        
        # Evaluate the formatted output, check for errors and return error result
        try:
            output = self._eval_fn(self.goal, formatted_output, **self.eval_fn_kwargs)
        except Exception as e:
            self.run_post_eval_hook()
            return EvaluationError(result=None, message=str(e))
        
        # If the evaluation result is an error, return the error result
        if  not isinstance(output, EvalResult):
            self.run_post_eval_hook()
            return EvalTypeMismatchError(result=None, message=f"Evaluation result is not a valid EvalResult: {output}")
        
        # If the evaluation result is a valid result, but not the expected type, return an error
        if isinstance(output, ValidEvalResult) and not isinstance(output, self.valid_eval_result_type):
            self.run_post_eval_hook()
            return EvalTypeMismatchError(result=None, message=f"Evaluation result is not a valid {self.valid_eval_result_type}: {output}")
        
        # Return the evaluation result
        self.run_post_eval_hook()
        return output

    async def eval_async(self, agent_output: Dict[str, Any]) -> EvalResult:
        '''
        Run the benchmark objective asynchronously.
        '''
        # Extract filtered output, check for errors and return error result
        try:
            filtered_output = await self._extract_filtered_output_async(agent_output, **self.extract_filtered_output_fn_kwargs)
        except Exception as e:
            await self.run_post_eval_hook_async()
            return ExtractionError(result=None, message=str(e))
        
        # If the filtered output is an error, return the error result
        if isinstance(filtered_output, InvalidEvalResult):
            await self.run_post_eval_hook_async()
            return filtered_output
        
        # Format filtered output, check for errors and return error result
        try:
            formatted_output = await self._format_filtered_output_async(filtered_output, **self.format_filtered_output_fn_kwargs)
        except Exception as e:
            await self.run_post_eval_hook_async()
            return FormattingError(result=None, message=str(e))
        
        # If the formatted output is an error, return the error result
        if isinstance(formatted_output, InvalidEvalResult):
            await self.run_post_eval_hook_async()
            return formatted_output
        
        # Evaluate the formatted output, check for errors and return error result
        try:
            output = await self._eval_fn_async(self.goal, formatted_output, **self.eval_fn_kwargs)
        except Exception as e:
            await self.run_post_eval_hook_async()
            return EvaluationError(result=None, message=str(e))

        # If the evaluation result is an error, return the error result
        if  not isinstance(output, EvalResult):
            await self.run_post_eval_hook_async()
            return EvalTypeMismatchError(result=None, message=f"Evaluation result is not a valid EvalResult: {output}")
        
        # If the evaluation result is a valid result, but not the expected type, return an error
        if isinstance(output, ValidEvalResult) and not isinstance(output, self.valid_eval_result_type):
            await self.run_post_eval_hook_async()
            return EvalTypeMismatchError(result=None, message=f"Evaluation result is not a valid {self.valid_eval_result_type}: {output}")
        
        # Return the evaluation result
        await self.run_post_eval_hook_async()
        return output
    
    # TODO this can be removed if it is done in the benchmark runner
    def agent_error(self, error_eval_message: str) -> InvalidEvalResult:
        '''
        Returns metric in case of agent error
        '''
        return AgentOperationError(result=None, message=error_eval_message)
    
    def run_pre_run_hook(self) -> None:
        '''
        Run the pre run hook.
        '''
        if self.pre_run_hook:
            self.pre_run_hook(**self.pre_run_hook_kwargs)
    
    def run_post_run_hook(self) -> None:
        '''
        Run the post run hook.
        '''
        if self.post_run_hook:
            self.post_run_hook(**self.post_run_hook_kwargs)
    
    def run_post_eval_hook(self) -> None:
        '''
        Run the post eval hook.
        '''
        if self.post_eval_hook:
            self.post_eval_hook(**self.post_eval_hook_kwargs)

    async def run_pre_run_hook_async(self) -> None:
        '''
        Run the pre run hook asynchronously.
        '''
        if self.pre_run_hook:
            if inspect.iscoroutinefunction(self.pre_run_hook):
                await self.pre_run_hook(**self.pre_run_hook_kwargs)
            else:
                self.pre_run_hook(**self.pre_run_hook_kwargs)
    
    async def run_post_run_hook_async(self) -> None:
        '''
        Run the post run hook asynchronously.
        '''
        if self.post_run_hook:
            if inspect.iscoroutinefunction(self.post_run_hook):
                await self.post_run_hook(**self.post_run_hook_kwargs)
            else:
                self.post_run_hook(**self.post_run_hook_kwargs)
    
    async def run_post_eval_hook_async(self) -> None:
        '''
        Run the post eval hook asynchronously.
        '''
        if self.post_eval_hook:
            if inspect.iscoroutinefunction(self.post_eval_hook):
                await self.post_eval_hook(**self.post_eval_hook_kwargs)
            else:
                self.post_eval_hook(**self.post_eval_hook_kwargs)