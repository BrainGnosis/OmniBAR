# © 2023 BrainGnosis Inc. All rights reserved.

from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, PrivateAttr, ConfigDict, Field
import json
import asyncio
import inspect
import uuid
from uuid import UUID

from tqdm import tqdm_notebook
from tqdm import tqdm

# Optional imports for backwards compatibility
try:
    from langchain.memory import CombinedMemory
    from langchain_core.memory import BaseMemory
except ImportError:
    # Fallback classes for when LangChain is not available
    class CombinedMemory:
        pass
    class BaseMemory:
        pass

from omnibar.objectives.base import BaseBenchmarkObjective
from omnibar.core.types import (
    EvalResult, 
    ValidEvalResult, 
    InvalidEvalResult,
    AgentOperationError,
    BoolEvalResult,
    FloatEvalResult
)
from omnibar.logging.logger import BenchmarkLogger, BenchmarkLog, LogEntry
from omnibar.logging.evaluator import BaseEvaluator, BooleanEvaluator, FloatEvaluator
from datetime import datetime

class Benchmark(BaseModel):
    '''
    Individual benchmark specification.
    '''
    name: str = Field(default="")
    uuid: UUID = Field(default_factory=uuid.uuid4)
    input_kwargs: Dict[str, Any]
    objective : BaseBenchmarkObjective
    iterations: int
    active: bool = True
    verbose: bool = True  # Controls logging for this specific benchmark
    invoke_method: str | None = None  # Optional override for agent invoke method
    

class OmniBarmarker(BaseModel):
    '''
    Modern benchmarker that uses BaseBenchmarkObjective instances for evaluation.
    
    This benchmarker replaces the old validation system with a more flexible
    objective-based evaluation system that supports complex evaluation criteria.
    
    ## Async Support:
    
    The OmniBarmarker supports both sync and async execution modes:
    
    1. **Method-Level Control**: Each benchmark can specify its own invoke_method 
       to use different agent methods (e.g., "invoke", "ainvoke", "run", etc.)
    
    2. **Async Execution**: Use benchmark_async() for concurrent execution with 
       configurable concurrency limits
    
    3. **Sync Execution**: Use benchmark() for traditional synchronous execution
    
    ## Usage Examples:
    
    ```python
    # Basic synchronous usage - runs all benchmarks with their specified iterations
    results = benchmarker.benchmark()
    
    # Async usage with concurrency control
    results = await benchmarker.benchmark_async(max_concurrent=3)
    
    # Per-benchmark configuration
    benchmarks = [
        Benchmark(..., iterations=5, invoke_method="invoke", verbose=True),     # Sync method, 5 iterations, verbose
        Benchmark(..., iterations=3, invoke_method="ainvoke", verbose=False),   # Async method, 3 iterations, quiet
        Benchmark(..., iterations=10, invoke_method="run", verbose=True),       # Custom method, 10 iterations, verbose
    ]
    ```
    
    ## Agent Creation Pattern:
    
    The executor_fn should return an agent object that has a callable method for invocation.
    
    Example usage patterns:
    
    1. LangChain AgentExecutor (default):
       executor_fn=lambda: create_langchain_agent()
       agent_invoke_method_name="invoke"  # default
    
    2. Custom agent with different method name:
       executor_fn=lambda: MyAgent()
       agent_invoke_method_name="run"
    
    3. Async-capable agent:
       executor_fn=lambda: AsyncAgent()
       agent_invoke_method_name="invoke"  # will auto-detect "ainvoke"
    
    The benchmarker will call getattr(agent, method_name)(**input_kwargs)
    where input_kwargs contains the specific input parameters for each benchmark
    '''
    # Config
    model_config = ConfigDict(validate_assignment=True)

    # Public Attributes
    executor_fn: Callable[..., Any]  # Returns an agent object
    executor_kwargs: Dict[str, Any]
    agent_invoke_method_name: str = "invoke"  # Name of the method to call on the agent object
    initial_input: List[Benchmark]
    notebook: bool = False
    reset_system: Callable | None = None
    validate_reset: bool = None
    enable_logging: bool = True  # Whether to enable comprehensive logging
    auto_assign_evaluators: bool = True  # Whether to auto-assign evaluators to logs
    evaluator_type_mapping: Dict[type, type] = Field(default_factory=lambda: {
        BoolEvalResult: BooleanEvaluator,
        FloatEvalResult: FloatEvaluator
    })  # Mapping of result types to evaluator classes
    
    # Private Attributes
    _tqdm: Any = PrivateAttr(default=None)
    _logger: BenchmarkLogger = PrivateAttr(default_factory=BenchmarkLogger)
    _active_logs: Dict[str, BenchmarkLog] = PrivateAttr(default_factory=dict)  # Track active logs by key

    def model_post_init(self, __context: Any):
        '''
        Post init assignments
        '''
        if self.notebook:
            self._tqdm = tqdm_notebook
        else:
            self._tqdm = tqdm
    
    # Properties for accessing logger data
    @property
    def logger(self) -> BenchmarkLogger:
        """Access the benchmark logger."""
        return self._logger
    
    @property
    def success_iter(self) -> int:
        """Number of successful iterations (computed from logger)."""
        if not self.enable_logging:
            return 0
        
        total_success = 0
        for log in self._logger.get_all_logs():
            for entry in log.entries:
                if hasattr(entry.eval_result, 'result') and entry.eval_result.result:
                    total_success += 1
        return total_success
    
    @property
    def fail_iter(self) -> int:
        """Number of failed iterations (computed from logger)."""
        if not self.enable_logging:
            return 0
        
        total_fail = 0
        for log in self._logger.get_all_logs():
            for entry in log.entries:
                if not (hasattr(entry.eval_result, 'result') and entry.eval_result.result):
                    total_fail += 1
        return total_fail
    
    @property
    def total_iter(self) -> int:
        """Total number of iterations (computed from logger)."""
        if not self.enable_logging:
            return 0
        
        return sum(len(log.entries) for log in self._logger.get_all_logs())
    
    @property
    def success_rate(self) -> float:
        """Success rate as a percentage (computed from logger)."""
        total = self.total_iter
        return (self.success_iter / total * 100) if total > 0 else 0.0
    
    # Logging Methods
    def _create_log_key(self, benchmark_id: UUID, objective_id: UUID) -> str:
        """Create a unique key for tracking active logs."""
        return f"{benchmark_id}:{objective_id}"
    
    def _start_benchmark_log(self, benchmark: Benchmark, objective_id: UUID) -> BenchmarkLog:
        """Start a new benchmark log for a specific objective."""
        if not self.enable_logging:
            return None
        
        # Determine which objective this log is for (handle combined objectives)
        target_objective = None
        if hasattr(benchmark.objective, 'objectives'):
            # Combined objective - find the specific sub-objective
            for sub_objective in benchmark.objective.objectives:
                if sub_objective.uuid == objective_id:
                    target_objective = sub_objective
                    break
        else:
            # Single objective
            if benchmark.objective.uuid == objective_id:
                target_objective = benchmark.objective
        
        # Get appropriate evaluator for this objective
        evaluator = None
        if target_objective is not None:
            evaluator = self._get_evaluator_for_objective(target_objective)
            
        log = BenchmarkLog(
            benchmark_id=benchmark.uuid,
            objective_id=objective_id,
            time_started=datetime.now(),
            time_ended=datetime.now(),  # Will be updated when log ends
            entries=[],
            metadata={
                'benchmark_name': benchmark.name,
                'benchmark_iterations': benchmark.iterations,
                'benchmark_invoke_method': benchmark.invoke_method or self.agent_invoke_method_name,
                'benchmark_verbose': benchmark.verbose,
                'objective_name': getattr(target_objective, 'name', 'Unknown') if target_objective else 'Unknown',
                'auto_evaluator_assigned': evaluator is not None,
                # Enhanced objective information for AI analysis
                'objective_type': type(target_objective).__name__ if target_objective else 'Unknown',
                'objective_description': getattr(target_objective, 'description', '') if target_objective else '',
                'objective_goal': str(getattr(target_objective, 'goal', '')) if target_objective else '',
                'objective_output_key': getattr(target_objective, 'output_key', '') if target_objective else '',
                'objective_category': getattr(target_objective, 'category', '') if target_objective else '',
                'valid_eval_result_type': getattr(target_objective.valid_eval_result_type, '__name__', str(target_objective.valid_eval_result_type)) if target_objective and hasattr(target_objective, 'valid_eval_result_type') else ''
            },
            evaluator=evaluator  # Auto-assign evaluator based on configuration
        )
        
        # Track active log
        log_key = self._create_log_key(benchmark.uuid, objective_id)
        self._active_logs[log_key] = log
        
        return log
    
    def _end_benchmark_log(self, benchmark: Benchmark, objective_id: UUID):
        """End a benchmark log and add it to the logger."""
        if not self.enable_logging:
            return
            
        log_key = self._create_log_key(benchmark.uuid, objective_id)
        if log_key in self._active_logs:
            log = self._active_logs[log_key]
            log.time_ended = datetime.now()
            self._logger.add_log(log)
            del self._active_logs[log_key]
    
    def _log_benchmark_iteration(self, benchmark: Benchmark, objective_id: UUID, 
                                eval_result: EvalResult, agent_output: Dict[str, Any]):
        """Log a single benchmark iteration result."""
        if not self.enable_logging:
            return
            
        log_key = self._create_log_key(benchmark.uuid, objective_id)
        if log_key in self._active_logs:
            log_entry = LogEntry(
                objective_id=objective_id,
                eval_result=eval_result,
                evaluated_output=agent_output,
                timestamp=datetime.now(),
                metadata={}
            )
            self._active_logs[log_key].log(log_entry)
    
    def _handle_combined_objective_logging(self, benchmark: Benchmark, 
                                         objective_results: Dict[str, EvalResult], 
                                         agent_output: Dict[str, Any]):
        """Handle logging for combined objectives - each sub-objective gets its own log."""
        if not self.enable_logging:
            return
            
        # For combined objectives, we need to log each sub-objective separately
        if hasattr(benchmark.objective, 'objectives'):
            # This is a combined objective
            for sub_objective in benchmark.objective.objectives:
                sub_objective_uuid = str(sub_objective.uuid)
                if sub_objective_uuid in objective_results:
                    # Check if we need to start a new log for this sub-objective
                    log_key = self._create_log_key(benchmark.uuid, sub_objective.uuid)
                    if log_key not in self._active_logs:
                        self._start_benchmark_log(benchmark, sub_objective.uuid)
                    
                    # Log this iteration for the sub-objective
                    self._log_benchmark_iteration(
                        benchmark, 
                        sub_objective.uuid, 
                        objective_results[sub_objective_uuid], 
                        agent_output
                    )
        else:
            # Single objective - use the main objective's UUID
            objective_uuid = str(benchmark.objective.uuid)
            if objective_uuid in objective_results:
                log_key = self._create_log_key(benchmark.uuid, benchmark.objective.uuid)
                if log_key not in self._active_logs:
                    self._start_benchmark_log(benchmark, benchmark.objective.uuid)
                
                self._log_benchmark_iteration(
                    benchmark, 
                    benchmark.objective.uuid, 
                    objective_results[objective_uuid], 
                    agent_output
                )
    
    def _finalize_benchmark_logging(self, benchmark: Benchmark):
        """Finalize logging for a completed benchmark."""
        if not self.enable_logging:
            return
            
        # End all logs for this benchmark
        if hasattr(benchmark.objective, 'objectives'):
            # Combined objective - end logs for all sub-objectives
            for sub_objective in benchmark.objective.objectives:
                self._end_benchmark_log(benchmark, sub_objective.uuid)
        else:
            # Single objective
            self._end_benchmark_log(benchmark, benchmark.objective.uuid)
    
    def get_logs_for_benchmark(self, benchmark_id: UUID) -> Dict[UUID, BenchmarkLog]:
        """Get all logs for a specific benchmark."""
        return self._logger.get_logs_by_benchmark(benchmark_id)
    
    def get_logs_for_objective(self, objective_id: UUID) -> Dict[UUID, BenchmarkLog]:
        """Get all logs for a specific objective across all benchmarks."""
        return self._logger.get_logs_by_objective(objective_id)
    
    def print_logger_summary(self):
        """Print a summary of all logged benchmarks."""
        self._logger.print_summary()
    
    def print_logger_details(self, detail_level: str = "summary"):
        """Print detailed view of all logged benchmarks."""
        self._logger.pretty_print(detail_level=detail_level)
    
    def _get_evaluator_for_objective(self, objective: BaseBenchmarkObjective) -> Optional[BaseEvaluator]:
        """
        Get the appropriate evaluator for an objective based on its valid_eval_result_type.
        
        Args:
            objective: The benchmark objective to get evaluator for
            
        Returns:
            BaseEvaluator instance if mapping exists and auto_assign_evaluators is True, None otherwise
        """
        if not self.auto_assign_evaluators:
            return None
            
        try:
            # Get the valid_eval_result_type from the objective
            result_type = getattr(objective, 'valid_eval_result_type', None)
            if result_type is None:
                return None
            
            # Look up evaluator class in the mapping
            evaluator_class = self.evaluator_type_mapping.get(result_type)
            if evaluator_class is None:
                return None
            
            # Instantiate the evaluator
            return evaluator_class()
            
        except Exception as e:
            # Log the error but don't fail the benchmarking process
            if hasattr(self, '_verbose_log'):
                self._verbose_log(f"⚠️  Warning: Failed to create evaluator for objective {getattr(objective, 'name', 'Unknown')}: {str(e)}")
            return None

    def _create_error_results_for_all_objectives(self, benchmark: Benchmark, error_result: EvalResult) -> Dict[str, EvalResult]:
        """
        Create error results for all objectives in a benchmark (handles both single and combined objectives).
        
        This ensures that errors are properly logged for each sub-objective in combined objectives,
        rather than just using the parent objective's UUID which won't match the logging system.
        
        Args:
            benchmark: The benchmark that failed
            error_result: The error result to assign to all objectives
            
        Returns:
            Dict mapping objective UUIDs to error results
        """
        error_results = {}
        
        if hasattr(benchmark.objective, 'objectives'):
            # Combined objective - create error results for all sub-objectives
            for sub_objective in benchmark.objective.objectives:
                error_results[str(sub_objective.uuid)] = error_result
        else:
            # Single objective - use the main objective's UUID
            error_results[str(benchmark.objective.uuid)] = error_result
        
        return error_results

    
    def _new_agent(self) -> Any:
        '''
        Creates a new agent instance
        '''
        return self.executor_fn(**self.executor_kwargs)
    
    def convert_agent_output(self, agent_output: Any) -> Dict[str, Any]:
        '''
        Convert agent output to the format expected by objectives.
        
        This method can be overridden by users to transform agent output
        into a dictionary format that objectives can process. By default,
        it's a pass-through function that returns the output unchanged.
        
        Args:
            agent_output: The raw output from the agent execution
            
        Returns:
            Dict[str, Any]: The converted output (by default, unchanged)
            
        Example:
            def convert_agent_output(self, agent_output):
                # Convert string output to dictionary
                if isinstance(agent_output, str):
                    return {"output": agent_output}
                # Convert custom object to dictionary
                elif hasattr(agent_output, 'to_dict'):
                    return agent_output.to_dict()
                # Return as-is for dictionary outputs
                return agent_output
        '''
        return agent_output
    
    def _get_invoke_method_name(self, benchmark: Benchmark) -> str:
        '''
        Get the invoke method name for a specific benchmark.
        Uses benchmark-specific method if provided, otherwise falls back to default.
        '''
        return benchmark.invoke_method or self.agent_invoke_method_name
    
    def _invoke_agent(self, agent: Any, benchmark: Benchmark) -> Any:
        '''
        Invokes the agent using the specified method name for a single benchmark
        '''
        method_name = self._get_invoke_method_name(benchmark)
        
        if not hasattr(agent, method_name):
            raise AttributeError(f"Agent object does not have method '{method_name}'")
        
        invoke_method = getattr(agent, method_name)
        if not callable(invoke_method):
            raise AttributeError(f"Agent method '{method_name}' is not callable")
        

        return invoke_method(**benchmark.input_kwargs)

    async def _invoke_agent_async(self, agent: Any, benchmark: Benchmark) -> Any:
        '''
        Invokes the agent using async method for a single benchmark
        '''
        method_name = self._get_invoke_method_name(benchmark)
        
        if not hasattr(agent, method_name):
            raise AttributeError(f"Agent object does not have method '{method_name}'")
        
        invoke_method = getattr(agent, method_name)
        if not callable(invoke_method):
            raise AttributeError(f"Agent method '{method_name}' is not callable")
        
        # Agent should only receive the actual input data, not benchmark internals
        
        # Check if method is actually async
        if inspect.iscoroutinefunction(invoke_method):
            return await invoke_method(**benchmark.input_kwargs)
        else:
            # If method is sync, run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: invoke_method(**benchmark.input_kwargs))

    def _get_info(self) -> Dict[str, Any]:
        '''
        Get comprehensive info about the benchmarking run
        '''
        info = {}
        
        # Try to get agent info, but handle gracefully if it fails
        try:
            agent = self._new_agent()
            info['agent_type'] = type(agent).__name__
            info['agent_invoke_method'] = self.agent_invoke_method_name
            
            # Log Tool(s) if available
            if hasattr(agent, 'tools') and agent.tools:
                try:
                    info['tools'] = [
                        {
                            'name': getattr(tool, 'name', 'Unknown'),
                            'description': getattr(tool, 'description', 'No description')
                        } 
                        for tool in agent.tools
                    ]
                except Exception as e:
                    info['tools'] = f"Error retrieving tools: {str(e)}"
            else:
                info['tools'] = "No tools available or agent doesn't support tools"

            # Log memory configuration if available
            if hasattr(agent, 'memory'):
                try:
                    if agent.memory is None:
                        info['memory'] = None
                    elif isinstance(agent.memory, CombinedMemory):
                        info['memory_type'] = 'CombinedMemory'
                        for i, memory in enumerate(agent.memory.memories):
                            info[f'memory_{i}'] = str(type(memory))
                            if hasattr(memory, 'buffer'):
                                info[f'buffer_{i}'] = str(memory.buffer)
                    elif isinstance(agent.memory, BaseMemory):
                        info['memory'] = str(type(agent.memory))
                        if hasattr(agent.memory, 'buffer'):
                            info['buffer'] = str(agent.memory.buffer)
                    else:
                        info['memory'] = str(type(agent.memory))
                except Exception as e:
                    info['memory'] = f"Error retrieving memory info: {str(e)}"
            else:
                info['memory'] = "No memory available or agent doesn't support memory"
                
        except Exception as e:
            info['agent_info_error'] = f"Could not retrieve agent info: {str(e)}"
            info['agent_type'] = "Unknown"
        
        # Log input and objectives (this should always work)
        info['initial_input'] = {
            'num_benchmarks': len(self.initial_input),
            'benchmarks': [
                {
                    'iterations': b.iterations,
                    'active': b.active,
                    'async_mode': b.async_mode,
                    'verbose': b.verbose,
                    'input_kwargs_count': len(b.input_kwargs)
                }
                for b in self.initial_input
            ],
            'total_iterations': sum(b.iterations for b in self.initial_input)
        }
        
        # Calculate number of objectives (handle both single and combined)
        if hasattr(self.objective, 'objectives'):
            info['num_objectives'] = len(self.objective.objectives)
        else:
            info['num_objectives'] = 1
            
        info['require_all_objectives'] = self.require_all_objectives
        
        # Log objectives info safely
        try:
            if hasattr(self.objective, 'objectives'):
                # Combined objective
                info['objectives'] = [
                    {
                        'uuid': str(obj.uuid),
                        'type': type(obj).__name__,
                        'goal': str(getattr(obj, 'goal', 'Unknown')),
                        'output_key': getattr(obj, 'output_key', ''),
                        'valid_eval_result_type': getattr(obj.valid_eval_result_type, '__name__', str(obj.valid_eval_result_type))
                    }
                    for obj in self.objective.objectives
                ]
                info['objective_type'] = 'CombinedBenchmarkObjective'
            else:
                # Single objective
                info['objectives'] = [{
                    'uuid': str(self.objective.uuid),
                    'type': type(self.objective).__name__,
                    'goal': str(getattr(self.objective, 'goal', 'Unknown')),
                    'output_key': getattr(self.objective, 'output_key', ''),
                    'valid_eval_result_type': getattr(self.objective.valid_eval_result_type, '__name__', str(self.objective.valid_eval_result_type))
                }]
                info['objective_type'] = 'SingleBenchmarkObjective'
        except Exception as e:
            info['objectives'] = f"Error retrieving objective info: {str(e)}"

        # Log Statistics (computed from logger)
        info['total_iter'] = self.total_iter
        info['success_iter'] = self.success_iter
        info['fail_iter'] = self.fail_iter
        info['success_rate'] = self.success_rate
        
        # Log detailed objective results if available
        if self.enable_logging and len(self._logger) > 0:
            try:
                info['objective_performance'] = self._analyze_objective_performance()
            except Exception as e:
                info['objective_performance'] = f"Error analyzing objective performance: {str(e)}"

        return info
    
    def _analyze_objective_performance(self) -> Dict[str, Any]:
        '''
        Analyze performance of individual objectives across all runs using logger data
        '''
        objective_stats = {}
        
        # Get all unique objective IDs from logger
        all_objective_ids = self._logger.get_all_objective_ids()
        
        # Analyze performance for each objective UUID
        for objective_id in all_objective_ids:
            successes = 0
            total_runs = 0
            
            # Get objective info for display
            obj_info = self._get_objective_info_by_uuid(str(objective_id))
            obj_name = obj_info.get('name', f"Objective_{str(objective_id)[:8]}")
            
            # Get all logs for this objective
            objective_logs = self._logger.get_logs_by_objective(objective_id)
            
            for log in objective_logs.values():
                for entry in log.entries:
                    total_runs += 1
                    if hasattr(entry.eval_result, 'result') and entry.eval_result.result:
                        successes += 1
            
            objective_stats[obj_name] = {
                'uuid': str(objective_id),
                'success_count': successes,
                'total_runs': total_runs,
                'success_rate': (successes / total_runs * 100) if total_runs > 0 else 0.0,
                'goal': obj_info.get('goal', 'Unknown'),
                'output_keys': obj_info.get('output_keys', [])
            }
        
        return objective_stats
    
    def _get_objective_info_by_uuid(self, uuid_key: str) -> Dict[str, Any]:
        '''
        Get objective information by UUID
        '''
        # Check if it's a combined objective
        if hasattr(self.objective, 'objectives'):
            for obj in self.objective.objectives:
                if str(obj.uuid) == uuid_key:
                    return {
                        'name': f"{type(obj).__name__}",
                        'goal': str(getattr(obj, 'goal', 'Unknown')),
                        'output_keys': getattr(obj, 'output_keys', [getattr(obj, 'output_key', '')])
                    }
        else:
            # Single objective
            if str(self.objective.uuid) == uuid_key:
                return {
                    'name': f"{type(self.objective).__name__}",
                    'goal': str(getattr(self.objective, 'goal', 'Unknown')),
                    'output_keys': [getattr(self.objective, 'output_key', '')]
                }
        
        # Fallback if not found
        return {
            'name': f"Unknown_{uuid_key[:8]}",
            'goal': 'Unknown',
            'output_keys': []
        }
    
    def _info_log(self, **dumps_kwargs):
        '''
        Log's final info JSON
        '''
        print('- Benchmarking Log:')
        print(json.dumps(self._get_info(), **dumps_kwargs))
    
    def _verbose_log(self, msg: str, benchmark: Benchmark = None) -> None:
        '''
        Log's output in verbose mode to stdout (print)
        Uses benchmark-specific verbose setting if provided, otherwise checks if any benchmark wants verbose output.
        '''
        if benchmark is not None:
            # Use benchmark-specific verbose setting
            if benchmark.verbose:
                print(msg)
        else:
            # For global messages (like overview), check if any benchmark wants verbose output
            any_verbose = any(b.verbose for b in self.initial_input)
            if any_verbose:
                print(msg)
    
    def _format_eval_result(self, result: EvalResult, objective_name: str) -> str:
        '''
        Format evaluation result with detailed information
        '''
        result_type = type(result).__name__
        
        if isinstance(result, ValidEvalResult):
            status_icon = "✅"
            status_color = "SUCCESS"
            result_value = getattr(result, 'result', 'N/A')
        elif isinstance(result, InvalidEvalResult):
            status_icon = "❌"
            status_color = "FAILURE"
            result_value = "N/A"
        else:
            status_icon = "❓"
            status_color = "UNKNOWN"
            result_value = "N/A"
        
        message = getattr(result, 'message', 'No message available')
        
        # Create formatted output
        formatted = f"{status_icon} {objective_name}\n"
        formatted += f"    ├─ Type: {result_type}\n"
        formatted += f"    ├─ Status: {status_color}\n"
        if result_value != 'N/A':
            formatted += f"    ├─ Result: {result_value}\n"
        formatted += f"    └─ Message: {message}"
        
        return formatted

    async def _evaluate_objectives(self, agent_output: Dict[str, Any], is_async: bool = False) -> tuple[bool, Dict[str, EvalResult]]:
        '''
        Evaluate the objective against the agent output (unified sync/async method)
        
        Args:
            agent_output: The output from the agent execution
            is_async: Whether to use async evaluation methods
            
        Returns:
            Tuple of (success: bool, results: Dict[str, EvalResult])
        '''
        mode_label = "(Async)" if is_async else ""
        self._verbose_log(f"📋 Evaluating Objectives {mode_label}:")
        self._verbose_log("─" * 50)
        
        try:
            # Run the objective's pre-run hook
            if is_async and hasattr(self.objective, 'run_pre_run_hook_async'):
                await self.objective.run_pre_run_hook_async()
            else:
                self.objective.run_pre_run_hook()
            
            # Evaluate the objective
            if is_async and hasattr(self.objective, 'eval_async'):
                eval_result = await self.objective.eval_async(agent_output)
            elif is_async:
                # Fall back to sync evaluation in executor
                loop = asyncio.get_event_loop()
                eval_result = await loop.run_in_executor(None, lambda: self.objective.eval(agent_output))
            else:
                eval_result = self.objective.eval(agent_output)
            
            # Standardize to Dict[str, EvalResult] format using UUID keys
            if isinstance(eval_result, dict):
                # Combined objective - already returns Dict[str, EvalResult]
                results = eval_result
            else:
                # Single objective - wrap in dict with UUID key
                results = {str(self.objective.uuid): eval_result}
            
            # Log detailed objective results with formatting
            self._log_objective_results(results, eval_result)
            
            # Run the objective's post-run hook
            if is_async and hasattr(self.objective, 'run_post_run_hook_async'):
                await self.objective.run_post_run_hook_async()
            else:
                self.objective.run_post_run_hook()
            
        except Exception as e:
            # Handle objective evaluation errors
            error_msg = f"{'Async' if is_async else ''} objective evaluation failed: {str(e)}"
            error_result = AgentOperationError(result=None, message=error_msg)
            results = {str(self.objective.uuid): error_result}
            
            # Log error with formatting
            obj_name = f"{type(self.objective).__name__}"
            formatted_error = self._format_eval_result(error_result, obj_name)
            self._verbose_log(formatted_error)
        
        self._verbose_log("─" * 50)
        
        # Determine overall success and log results
        success = self._evaluate_success_and_log(results, is_async)
        
        return success, results

    def _log_objective_results(self, results: Dict[str, EvalResult], eval_result: Any) -> None:
        '''Log detailed objective results with formatting'''
        for uuid_key, result in results.items():
            # Try to get objective name from UUID, fallback to generic name
            if hasattr(self.objective, 'objectives') and isinstance(eval_result, dict):
                # Combined objective - find the specific objective
                obj_name = None
                for obj in self.objective.objectives:
                    if str(obj.uuid) == uuid_key:
                        obj_name = f"{type(obj).__name__}"
                        break
                if obj_name is None:
                    obj_name = f"Objective_{uuid_key[:8]}"
            else:
                # Single objective
                obj_name = f"{type(self.objective).__name__}"
            
            formatted_result = self._format_eval_result(result, obj_name)
            self._verbose_log(formatted_result)

    def _evaluate_success_and_log(self, results: Dict[str, EvalResult], is_async: bool = False) -> bool:
        '''Determine overall success and log results'''
        # Determine overall success based on evaluation mode
        valid_results = [r for r in results.values() if isinstance(r, ValidEvalResult)]
        
        if self.require_all_objectives:
            # ALL objectives must pass (be ValidEvalResult)
            success = len(valid_results) == len(results)
            eval_mode = "ALL objectives must pass"
        else:
            # ANY objective passing is sufficient
            success = len(valid_results) > 0
            eval_mode = "ANY objective passing is sufficient"
        
        # Log overall result with pretty formatting
        success_count = len(valid_results)
        total_count = len(results)
        
        if success:
            overall_icon = "🎉"
            overall_status = f"ITERATION SUCCESS{' (ASYNC)' if is_async else ''}"
        else:
            overall_icon = "💔"
            overall_status = f"ITERATION FAILED{' (ASYNC)' if is_async else ''}"
        
        self._verbose_log(f"{overall_icon} {overall_status}")
        self._verbose_log(f"    ├─ Evaluation Mode: {eval_mode}")
        self._verbose_log(f"    ├─ Objectives Passed: {success_count}/{total_count}")
        self._verbose_log(f"    └─ Success Rate: {(success_count/total_count)*100:.1f}%")
        
        return success



    def _log_agent_output(self, output: Any, is_async: bool = False) -> None:
        '''Log agent output with consistent formatting'''
        mode_label = " (Async)" if is_async else ""
        self._verbose_log(f"🤖 Agent Output{mode_label}:")
        self._verbose_log("─" * 30)
        
        if isinstance(output, dict):
            for key, value in output.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                self._verbose_log(f"    {key}: {value_str}")
        else:
            output_str = str(output)
            if len(output_str) > 200:
                output_str = output_str[:197] + "..."
            self._verbose_log(f"    {output_str}")
        
        self._verbose_log("─" * 30)

    def _log_benchmark_header(self, iterations: int, is_async: bool = False, max_concurrent: int = None) -> None:
        '''Log benchmark header with configuration details'''
        mode = "ASYNC" if is_async else ""
        self._verbose_log(f"🚀 {mode} BENCHMARK STARTING")
        self._verbose_log("═" * 60)
        self._verbose_log("📊 Configuration:")
        self._verbose_log(f"    ├─ Total Iterations: {iterations}")
        
        if is_async:
            self._verbose_log(f"    ├─ Max Concurrent: {max_concurrent}")
        else:
            self._verbose_log("    ├─ Execution Mode: SYNC")
        
        # Calculate number of objectives
        num_objectives = len(self.objective.objectives) if hasattr(self.objective, 'objectives') else 1
        self._verbose_log(f"    ├─ Number of Objectives: {num_objectives}")
        self._verbose_log(f"    ├─ Evaluation Mode: {'ALL objectives must pass' if self.require_all_objectives else 'ANY objective passing is sufficient'}")
        self._verbose_log(f"    ├─ Number of Benchmarks: {len(self.initial_input)}")
        
        # Display benchmark summary
        for i, benchmark in enumerate(self.initial_input):
            method_name = benchmark.invoke_method or self.agent_invoke_method_name
            self._verbose_log(f"    │   {i+1}. Benchmark with {benchmark.iterations} iterations (method: {method_name})")
        self._verbose_log(f"    └─ Total Benchmark Iterations: {sum(b.iterations for b in self.initial_input)}")
        self._verbose_log("")

    def _log_benchmark_details(self) -> None:
        '''Log detailed benchmark configuration'''
        self._verbose_log("📋 Benchmark Details:")
        for i, benchmark in enumerate(self.initial_input):
            method_name = benchmark.invoke_method or self.agent_invoke_method_name
            self._verbose_log(f"    {i+1}. Benchmark {i+1}:")
            self._verbose_log(f"       ├─ Iterations: {benchmark.iterations}")
            self._verbose_log(f"       ├─ Active: {benchmark.active}")
            self._verbose_log(f"       ├─ Invoke Method: {method_name}")
            self._verbose_log(f"       └─ Input kwargs: {len(benchmark.input_kwargs)} parameters")
        self._verbose_log("")

    def _log_objectives_info(self) -> None:
        '''Log objectives information'''
        self._verbose_log("🎯 Objectives:")
        if hasattr(self.objective, 'objectives'):
            # Combined objective
            for i, obj in enumerate(self.objective.objectives):
                goal_str = str(getattr(obj, 'goal', 'Unknown'))
                if len(goal_str) > 50:
                    goal_str = goal_str[:47] + "..."
                self._verbose_log(f"    {i+1}. {type(obj).__name__} (UUID: {str(obj.uuid)[:8]}...)")
                self._verbose_log(f"       ├─ Goal: {goal_str}")
                self._verbose_log(f"       └─ Output Key: {getattr(obj, 'output_key', 'N/A')}")
        else:
            # Single objective
            goal_str = str(getattr(self.objective, 'goal', 'Unknown'))
            if len(goal_str) > 50:
                goal_str = goal_str[:47] + "..."
            self._verbose_log(f"    1. {type(self.objective).__name__} (UUID: {str(self.objective.uuid)[:8]}...)")
            self._verbose_log(f"       ├─ Goal: {goal_str}")
            self._verbose_log(f"       └─ Output Key: {getattr(self.objective, 'output_key', 'N/A')}")

    def _log_final_results(self, is_async: bool = False) -> None:
        '''Log final benchmark results'''
        mode = "ASYNC" if is_async else ""
        self._verbose_log(f"\n🏁 {mode} BENCHMARK COMPLETED")
        self._verbose_log("═" * 60)
        
        # Final statistics summary
        self._verbose_log("📊 Final Results Summary:")
        self._verbose_log(f"    ├─ Total Iterations: {self.total_iter}")
        self._verbose_log(f"    ├─ Successful: {self.success_iter}")
        self._verbose_log(f"    ├─ Failed: {self.fail_iter}")
        self._verbose_log(f"    └─ Overall Success Rate: {self.success_rate:.1f}%")
        
        # Per-objective performance summary
        if self.enable_logging and len(self._logger) > 0:
            self._verbose_log("")
            self._verbose_log("🎯 Per-Objective Performance:")
            obj_perf = self._analyze_objective_performance()
            for obj_name, stats in obj_perf.items():
                self._verbose_log(f"    • {obj_name}: {stats['success_count']}/{stats['total_runs']} ({stats['success_rate']:.1f}%)")
        
        self._verbose_log("═" * 60)


    
    def _reset_system(self) -> None:
        '''
        Resets the system to it's initial state if a reset function 
        is provided. 
        
        Confirms with the user that the reset is finished if validate
        reset is provided
        '''
        if isinstance(self.reset_system, Callable):
            self.reset_system()
        if self.validate_reset:
            input('Confirm when reset is finished: ')    

    def benchmark(self) -> Dict[str, Any]:
        '''
        Executes all benchmarks according to their individual specifications.
        Each benchmark runs for its specified number of iterations.
        Each benchmark controls its own verbose logging.
            
        Returns:
            Dictionary with benchmarking results
        '''

        # Calculate total work
        total_iterations = sum(b.iterations for b in self.initial_input)
        
        # Log benchmark overview
        self._verbose_log("🚀 Starting Benchmark Execution")
        self._verbose_log("═" * 60)
        self._verbose_log("📊 Benchmark Overview:")
        self._verbose_log(f"    ├─ Number of Benchmarks: {len(self.initial_input)}")
        self._verbose_log(f"    └─ Total Iterations: {total_iterations}")
        self._verbose_log("")

        # Execute each benchmark according to its own iteration count
        completed_iterations = 0
        for benchmark_idx, benchmark in enumerate(self.initial_input):
            if not benchmark.active:
                self._verbose_log(f"⏭️  Skipping inactive benchmark {benchmark_idx + 1}", benchmark)
                continue
                
            self._verbose_log(f"\n📋 Benchmark {benchmark_idx + 1}/{len(self.initial_input)}", benchmark)
            self._verbose_log(f"    ├─ Iterations: {benchmark.iterations}", benchmark)
            self._verbose_log(f"    ├─ Invoke Method: {benchmark.invoke_method or self.agent_invoke_method_name}", benchmark)
            self._verbose_log(f"    └─ Objective: {type(benchmark.objective).__name__}", benchmark)
            self._verbose_log("─" * 40, benchmark)
            
            # Initialize logging for this benchmark (handles both single and combined objectives)
            if self.enable_logging:
                if hasattr(benchmark.objective, 'objectives'):
                    # Combined objective - start logs for all sub-objectives
                    for sub_objective in benchmark.objective.objectives:
                        self._start_benchmark_log(benchmark, sub_objective.uuid)
                else:
                    # Single objective
                    self._start_benchmark_log(benchmark, benchmark.objective.uuid)
            
            # Run iterations for this specific benchmark
            for iteration in range(benchmark.iterations):
                completed_iterations += 1
                self._verbose_log(f"\n🔄 Benchmark {benchmark_idx + 1} - Iteration {iteration + 1}/{benchmark.iterations} (Global: {completed_iterations}/{total_iterations})", benchmark)
                
                try:
                    loop_success, objective_results = self._run_single_benchmark_iteration(benchmark)
                    status = "✅ Success" if loop_success else "❌ Failed"
                    self._verbose_log(f"    └─ {status}", benchmark)
                except Exception as e:
                    self._verbose_log(f"    └─ 💥 Exception: {e}", benchmark)
            
            # Finalize logging for this benchmark
            self._finalize_benchmark_logging(benchmark)

        # Log completion
        self._verbose_log(f"\n🏁 All benchmarks completed: {completed_iterations} total iterations processed")
        
        return {"message": f"All benchmarks completed: {completed_iterations} total iterations processed"}

    def _run_single_benchmark_iteration(self, benchmark: Benchmark) -> tuple[bool, Dict[str, EvalResult]]:
        '''
        Runs a single iteration of a specific benchmark.
        
        Args:
            benchmark: The benchmark to execute
            
        Returns:
            Tuple of (success: bool, objective_results: Dict[str, EvalResult])
        '''
        # Reset system if needed
        self._reset_system()
        
        # Create agent
        agent = self._new_agent()
        
        # Run pre-run hooks (BEFORE agent execution)
        try:
            if hasattr(benchmark.objective, 'run_pre_run_hook'):
                benchmark.objective.run_pre_run_hook()
        except Exception as e:
            self._verbose_log(f"💥 Pre-run Hook Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Pre-run hook failed: {str(e)}")
            
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, {})
            return False, error_results
        
        # Invoke agent for this benchmark
        try:
            agent_output = self._invoke_agent(agent, benchmark)
            # Convert agent output using the configurable converter
            output = self.convert_agent_output(agent_output)
            self._verbose_log(f"🤖 Agent Output: {output}", benchmark)
        except Exception as e:
            self._verbose_log(f"💥 Agent Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Agent execution failed: {str(e)}")
            
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, {})
            return False, error_results
        
        # Run post-run hooks (AFTER agent execution, BEFORE evaluation)
        try:
            if hasattr(benchmark.objective, 'run_post_run_hook'):
                benchmark.objective.run_post_run_hook()
        except Exception as e:
            self._verbose_log(f"💥 Post-run Hook Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Post-run hook failed: {str(e)}")
            
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, output)
            return False, error_results
        
        # Evaluate objectives for this benchmark
        try:
            # Evaluate the objective
            eval_result = benchmark.objective.eval(output)
            
            # Handle both single and combined objectives
            if isinstance(eval_result, dict):
                # Combined objective - already returns Dict[str, EvalResult]
                objective_results = eval_result
            else:
                # Single objective - wrap in dict with UUID key
                objective_results = {str(benchmark.objective.uuid): eval_result}
            
            # Determine success based on objective results
            valid_results = [r for r in objective_results.values() if isinstance(r, ValidEvalResult)]
            success = len(valid_results) > 0  # ANY valid result counts as success
            
            # Log the results
            self._handle_combined_objective_logging(benchmark, objective_results, output)
            
            return success, objective_results
            
        except Exception as e:
            self._verbose_log(f"💥 Objective Evaluation Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Objective evaluation failed: {str(e)}")
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, output)
            return False, error_results

    async def benchmark_async(
        self,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        '''
        Executes all benchmarks asynchronously with concurrency control.
        Each benchmark runs for its specified number of iterations.
        Each benchmark controls its own verbose logging.
        
        Args:
            max_concurrent: Maximum number of concurrent async operations (default: 5)
            
        Returns:
            Dictionary with benchmarking results
        '''

        # Calculate total work
        total_iterations = sum(b.iterations for b in self.initial_input)
        
        # Log benchmark overview
        self._verbose_log("🚀 Starting Async Benchmark Execution")
        self._verbose_log("═" * 60)
        self._verbose_log("📊 Benchmark Overview:")
        self._verbose_log(f"    ├─ Number of Benchmarks: {len(self.initial_input)}")
        self._verbose_log(f"    ├─ Total Iterations: {total_iterations}")
        self._verbose_log(f"    └─ Max Concurrent: {max_concurrent}")
        self._verbose_log("")

        # Initialize logging for all benchmarks upfront
        if self.enable_logging:
            for benchmark in self.initial_input:
                if not benchmark.active:
                    continue
                    
                if hasattr(benchmark.objective, 'objectives'):
                    # Combined objective - start logs for all sub-objectives
                    for sub_objective in benchmark.objective.objectives:
                        self._start_benchmark_log(benchmark, sub_objective.uuid)
                else:
                    # Single objective
                    self._start_benchmark_log(benchmark, benchmark.objective.uuid)
        
        # Create all benchmark iteration tasks
        all_tasks = []
        task_info = []  # Track which benchmark each task belongs to
        
        for benchmark_idx, benchmark in enumerate(self.initial_input):
            if not benchmark.active:
                self._verbose_log(f"⏭️  Skipping inactive benchmark {benchmark_idx + 1}", benchmark)
                continue
                
            # Create tasks for all iterations of this benchmark
            for iteration in range(benchmark.iterations):
                task = self._run_single_benchmark_iteration_async(benchmark)
                all_tasks.append(task)
                task_info.append({
                    'benchmark_idx': benchmark_idx,
                    'iteration': iteration,
                    'benchmark': benchmark
                })

        # Run with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task, info):
            async with semaphore:
                try:
                    success, results = await task
                    status = "✅ Success" if success else "❌ Failed"
                    self._verbose_log(f"🔄 Benchmark {info['benchmark_idx'] + 1} - Iteration {info['iteration'] + 1}: {status}", info['benchmark'])
                    return success, results
                except Exception as e:
                    self._verbose_log(f"💥 Benchmark {info['benchmark_idx'] + 1} - Iteration {info['iteration'] + 1}: Exception: {e}", info['benchmark'])
                    return False, {}

        # Execute all tasks with concurrency control
        semaphore_tasks = [run_with_semaphore(task, info) for task, info in zip(all_tasks, task_info)]
        completed_results = await asyncio.gather(*semaphore_tasks, return_exceptions=True)

        # Count successes
        successful = sum(1 for result in completed_results if isinstance(result, tuple) and result[0])
        total_completed = len([r for r in completed_results if not isinstance(r, Exception)])

        # Finalize logging for all benchmarks
        if self.enable_logging:
            for benchmark in self.initial_input:
                if not benchmark.active:
                    continue
                self._finalize_benchmark_logging(benchmark)
        
        # Log completion
        self._verbose_log(f"\n🏁 Async benchmark completed: {total_completed} total iterations processed ({successful} successful)")
        
        return {"message": f"Async benchmark completed: {total_completed} total iterations processed"}

    async def _run_single_benchmark_iteration_async(self, benchmark: Benchmark) -> tuple[bool, Dict[str, EvalResult]]:
        '''
        Runs a single iteration of a specific benchmark asynchronously.
        
        Args:
            benchmark: The benchmark to execute
            
        Returns:
            Tuple of (success: bool, objective_results: Dict[str, EvalResult])
        '''
        # Reset system if needed (run in executor for sync method)
        if callable(self.reset_system):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._reset_system)
        
        # Create agent
        agent = self._new_agent()
        
        # Run pre-run hooks (BEFORE agent execution)
        try:
            if hasattr(benchmark.objective, 'run_pre_run_hook_async'):
                await benchmark.objective.run_pre_run_hook_async()
            elif hasattr(benchmark.objective, 'run_pre_run_hook'):
                # Run sync hook in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: benchmark.objective.run_pre_run_hook())
        except Exception as e:
            self._verbose_log(f"💥 Pre-run Hook Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Pre-run hook failed: {str(e)}")
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, {})
            return False, error_results
        
        # Invoke agent for this benchmark
        try:
            agent_output = await self._invoke_agent_async(agent, benchmark)
            # Convert agent output using the configurable converter
            output = self.convert_agent_output(agent_output)
            self._verbose_log(f"🤖 Agent Output: {output}", benchmark)
        except Exception as e:
            self._verbose_log(f"💥 Agent Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Agent execution failed: {str(e)}")
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, {})
            return False, error_results
        
        # Run post-run hooks (AFTER agent execution, BEFORE evaluation)
        try:
            if hasattr(benchmark.objective, 'run_post_run_hook_async'):
                await benchmark.objective.run_post_run_hook_async()
            elif hasattr(benchmark.objective, 'run_post_run_hook'):
                # Run sync hook in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: benchmark.objective.run_post_run_hook())
        except Exception as e:
            self._verbose_log(f"💥 Post-run Hook Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Post-run hook failed: {str(e)}")
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, output)
            return False, error_results
        
        # Evaluate objectives for this benchmark
        try:
            # Evaluate the objective
            if hasattr(benchmark.objective, 'eval_async'):
                eval_result = await benchmark.objective.eval_async(output)
            else:
                # Run sync eval in executor
                loop = asyncio.get_event_loop()
                eval_result = await loop.run_in_executor(None, lambda: benchmark.objective.eval(output))
            
            # Handle both single and combined objectives
            if isinstance(eval_result, dict):
                # Combined objective - already returns Dict[str, EvalResult]
                objective_results = eval_result
            else:
                # Single objective - wrap in dict with UUID key
                objective_results = {str(benchmark.objective.uuid): eval_result}
            
            # Determine success based on objective results
            valid_results = [r for r in objective_results.values() if isinstance(r, ValidEvalResult)]
            success = len(valid_results) > 0  # ANY valid result counts as success
            
            # Log the results
            self._handle_combined_objective_logging(benchmark, objective_results, output)
            
            return success, objective_results
            
        except Exception as e:
            self._verbose_log(f"💥 Objective Evaluation Error: {str(e)}", benchmark)
            error_result = AgentOperationError(result=None, message=f"Objective evaluation failed: {str(e)}")
            # Create error results for all relevant objectives (handles both single and combined)
            error_results = self._create_error_results_for_all_objectives(benchmark, error_result)
            # Log the error result
            self._handle_combined_objective_logging(benchmark, error_results, output)
            return False, error_results