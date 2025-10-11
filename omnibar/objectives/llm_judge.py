# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any, Type
from pydantic import Field, model_validator, BaseModel, PrivateAttr
import inspect
import asyncio
from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult,
    BoolEvalResult,
    FloatEvalResult,
    InvalidEvalResult
)
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, BaseOutputParser
from langchain_core.runnables import Runnable

DEFAULT_BINARY_PROMPT = """
Your job is to judge the output of an AI Agent and return a boolean value indicating whether the output is correct or not and a message explaining why.

The expected output is:
{expected_output}

The output of the AI Agent is:
{input}

The format of the output should be:
{format_instructions}
"""

DEFAULT_SCORE_PROMPT = """
Your job is to judge the output of an AI Agent and return a score between 0 and 1 indicating how close the output is to the expected output and a message explaining why.

The expected output is:
{expected_output}

The output of the AI Agent is:
{input}

The format of the output should be:
{format_instructions}
"""

class LLMBinaryOutputSchema(BaseModel):
    """
    Schema for binary evaluation of the output
    """
    result: bool = Field(description="Whether the output is correct or not")
    message: str = Field(description="A message explaining why the output is correct or not")

class LLMPartialOutputSchema(BaseModel):
    """
    Schema for score-based evaluation of the output
    """
    result: float = Field(description="A score between 0 and 1 indicating how close the output is to the expected output")
    message: str = Field(description="A message explaining why the output is correct or not")

class LLMJudgeObjective(BaseBenchmarkObjective):
    """
    LLMJudgeObjective is a benchmark objective that uses an LLM to judge the output of an AI Agent.
    
    Supports both boolean (pass/fail) and float (0.0-1.0 scoring) evaluation types for partial scoring.
    
    Users can either:
    1. Provide an invoke_method callable that takes a dict with "input" key and returns evaluation results
    2. Provide a goal (and optionally a prompt), which will create a LangChain LLM chain whose invoke method will be used
    3. Provide only a goal, which will use default prompts based on valid_eval_result_type:
       - BoolEvalResult: Uses DEFAULT_BINARY_PROMPT for pass/fail evaluation
       - FloatEvalResult: Uses DEFAULT_SCORE_PROMPT for 0.0-1.0 scoring
    
    The valid_eval_result_type determines:
    - The output parser schema (LLMBinaryOutputSchema vs LLMPartialOutputSchema)
    - The default prompt template if no custom prompt is provided
    - The return type of evaluation results (BoolEvalResult vs FloatEvalResult)
    """
    # Override goal to be optional for LLM-based evaluation
    goal: str | None = None
    # Required output_key for agent responses
    output_key: str
    
    # If the user provides a prompt and goal, we build an OpenAI LLM chain to judge the output
    prompt: str | PromptTemplate | None = None
    # If the user provides an invoke_method, it will be used to judge the output
    invoke_method: Any | None = None

    eval_fn_kwargs: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    valid_eval_result_type: Type[BoolEvalResult] | Type[FloatEvalResult] = BoolEvalResult

    # Internal invoke method and parser to judge the output
    _invoke_method: Any | None = PrivateAttr(default=None)
    _async_invoke_method: Any | None = PrivateAttr(default=None)
    _output_parser: BaseOutputParser | None = PrivateAttr(default=None)

    @model_validator(mode='after')
    def validate_prompt_template(self) -> 'LLMJudgeObjective':
        """
        Validate that if prompt is a PromptTemplate, it has the required attributes and variables.
        """
        # Pydantic already validates the type, so we know if it's not str/None, it's PromptTemplate
        if isinstance(self.prompt, PromptTemplate):
            # Validate that prompt has required input and partial variables
            if not hasattr(self.prompt, "input_variables") or not hasattr(self.prompt, "partial_variables"):
                raise ValueError("Prompt must have 'input_variables' and 'partial_variables' attributes.")

            if "input" not in getattr(self.prompt, "input_variables", []):
                raise ValueError("Prompt must have 'input' in its input_variables.")

            partial_vars = getattr(self.prompt, "partial_variables", {})
            if not isinstance(partial_vars, dict):
                raise ValueError("Prompt's partial_variables must be a dict.")

            for required_var in ["format_instructions", "expected_output"]:
                if required_var not in partial_vars:
                    raise ValueError(f"Prompt's partial_variables must include '{required_var}'.")
        
        return self
    
    def model_post_init(self, __context: Any) -> None:
        # Set up the output parser based on the valid_eval_result_type
        if self.valid_eval_result_type == BoolEvalResult:
            self._output_parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
        elif self.valid_eval_result_type == FloatEvalResult:
            self._output_parser = JsonOutputParser(pydantic_object=LLMPartialOutputSchema)
        else:
            raise ValueError(f"Unsupported valid_eval_result_type: {self.valid_eval_result_type}")
        
        # If the user provides an invoke_method, we use it directly
        if self.invoke_method is not None:
            # Check if the invoke method is async and set up appropriate versions
            if inspect.iscoroutinefunction(self.invoke_method):
                # For async methods, only set async version - sync eval() should not be used
                self._async_invoke_method = self.invoke_method
                self._invoke_method = None  # Explicitly set to None for async-only functions
            else:
                # For sync methods, use them directly and create async wrapper
                self._invoke_method = self.invoke_method
                self._async_invoke_method = self._create_async_wrapper(self.invoke_method)
        elif self.goal is not None:
            # Build the LLM chain and assign its invoke method (prompt can be None for default prompts)
            llm_chain = self._build_llm_chain()
            self._invoke_method = llm_chain.invoke
            # LangChain chains support async invoke with ainvoke
            if hasattr(llm_chain, 'ainvoke'):
                self._async_invoke_method = llm_chain.ainvoke
            else:
                # Fallback to sync wrapper
                self._async_invoke_method = self._create_async_wrapper(llm_chain.invoke)
        else:
            raise ValueError("Either invoke_method or goal must be provided")

    def _create_async_wrapper(self, sync_method):
        """Create an async wrapper for synchronous methods"""
        async def async_wrapper(*args, **kwargs):
            # Run the synchronous method in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: sync_method(*args, **kwargs))
        return async_wrapper

    def _build_llm_chain(self) -> Runnable:
        """
        Build the LLM chain to judge the output. Override in subclasses to customize the chain.
        """
        if isinstance(self.prompt, str):
            prompt = PromptTemplate(
                template=self.prompt, input_variables=["input"], 
                partial_variables={
                    "format_instructions": self._output_parser.get_format_instructions(),
                    "expected_output": self.goal
                }
            )
        elif self.prompt is None:
            # Use default prompt based on the evaluation type
            if self.valid_eval_result_type == BoolEvalResult:
                default_prompt = DEFAULT_BINARY_PROMPT
            elif self.valid_eval_result_type == FloatEvalResult:
                default_prompt = DEFAULT_SCORE_PROMPT
            else:
                raise ValueError(f"Unsupported valid_eval_result_type: {self.valid_eval_result_type}")
            
            prompt = PromptTemplate(
                template=default_prompt, input_variables=["input"], 
                partial_variables={
                    "format_instructions": self._output_parser.get_format_instructions(),
                    "expected_output": self.goal
                }
            )
        else:
            # Validation is now handled by the model validator
            prompt = self.prompt
        
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        chain = prompt | llm | self._output_parser
        return chain

    def _eval_fn(self, goal: str | None, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Evaluate the output of an AI Agent
        """
        # Check if only async method is available
        if self._invoke_method is None:
            return InvalidEvalResult(
                result=None, 
                message="Cannot use sync eval() with async-only invoke method. Use eval_async() instead."
            )
        
        # Goal parameter comes from parent class but may be None for LLM-based evaluation
        # formatted_output will be a dict with a single key-value pair, the output of the AI Agent
        output = next(iter(formatted_output.values()))
        key = next(iter(formatted_output.keys()))

        # Try casting the output to a string if it's not already if we cant, return an invalid result
        try:
            output = str(output)
        except Exception as e:
            return InvalidEvalResult(result=None, message=f"Value for key {key} is not a string: {e}")
        
        # Run the invoke method
        try:
            # The result here is expected to be the output of the output parser,
            # so it should already be in the format specified by self._output_parser.
            # For example, if the output parser returns a dict with 'result' and 'message',
            # we use those fields directly.
            result = self._invoke_method({"input": output})
            
            # Return the appropriate result type based on valid_eval_result_type
            if self.valid_eval_result_type == BoolEvalResult:
                return BoolEvalResult(result=result["result"], message=result.get("message", ""))
            elif self.valid_eval_result_type == FloatEvalResult:
                return FloatEvalResult(result=result["result"], message=result.get("message", ""))
            else:
                return InvalidEvalResult(result=None, message=f"Unsupported valid_eval_result_type: {self.valid_eval_result_type}")
        except Exception as e:
            return InvalidEvalResult(result=None, message=f"Error invoking method: {e}")

    async def _eval_fn_async(self, goal: str | None, formatted_output: Dict[str, Any], **kwargs) -> EvalResult:
        """
        Asynchronously evaluate the output of an AI Agent
        """
        # Goal parameter comes from parent class but may be None for LLM-based evaluation
        # formatted_output will be a dict with a single key-value pair, the output of the AI Agent
        output = next(iter(formatted_output.values()))
        key = next(iter(formatted_output.keys()))

        # Try casting the output to a string if it's not already if we cant, return an invalid result
        try:
            output = str(output)
        except Exception as e:
            return InvalidEvalResult(result=None, message=f"Value for key {key} is not a string: {e}")
        
        # Run the async invoke method
        try:
            # The result here is expected to be the output of the output parser,
            # so it should already be in the format specified by self._output_parser.
            # For example, if the output parser returns a dict with 'result' and 'message',
            # we use those fields directly.
            result = await self._async_invoke_method({"input": output})
            
            # Return the appropriate result type based on valid_eval_result_type
            if self.valid_eval_result_type == BoolEvalResult:
                return BoolEvalResult(result=result["result"], message=result.get("message", ""))
            elif self.valid_eval_result_type == FloatEvalResult:
                return FloatEvalResult(result=result["result"], message=result.get("message", ""))
            else:
                return InvalidEvalResult(result=None, message=f"Unsupported valid_eval_result_type: {self.valid_eval_result_type}")
        except Exception as e:
            return InvalidEvalResult(result=None, message=f"Error invoking async method: {e}")