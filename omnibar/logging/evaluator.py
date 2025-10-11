# © 2023 BrainGnosis Inc. All rights reserved.

from pydantic import BaseModel
from typing import Any, Dict, List, TYPE_CHECKING
import warnings
import numpy as np

from omnibar.core.types import ValidEvalResult, FloatEvalResult, BoolEvalResult

if TYPE_CHECKING:
    from omnibar.logging.logger import LogEntry

class BaseEvaluator(BaseModel):
    '''
    Base class for evaluators.

    Subclasses should implement _filter (if needed) and _eval.

    Run by calling eval() with a list of log entries and a filter flag.
    '''
    def _filter(self, log_entries: List["LogEntry"]) -> List["LogEntry"]:
        '''
        Filter out log enteries that are not valid
        '''
        return [log_entry for log_entry in log_entries if isinstance(log_entry.eval_result, ValidEvalResult)]

    def _eval(self, log_entries: List["LogEntry"]) -> Dict[str, Any]:
        '''
        Evaluate the log entries and return a dictionary of the results.

        Not implemented in base class.
        '''
        raise NotImplementedError("Not implemented in base class, implement in a sublass")

    def eval(self, log_entries: List["LogEntry"], filter_results: bool = False) -> Dict[str, Any]:
        '''
        Evaluate the log entry and return a dictionary of the results.

        If filter is True, filter the log entries first.
        '''
        if filter_results:
            log_entries = self._filter(log_entries)
        return self._eval(log_entries)

class FloatEvaluator(BaseEvaluator):
    '''
    Evaluator for float eval results.
    
    Returns a dictionary with the following keys:
    - mean: the mean of the float eval results
    - std: the standard deviation of the float eval results
    - invalid_count: the number of invalid eval results
    '''
    def _filter(self, log_entries: List["LogEntry"]) -> List["LogEntry"]:
        '''
        Filter out log entries that are not valid and that are not a fload eval resulkt
        '''
        log_entries = super()._filter(log_entries)
        # Only keep log entries whose eval_result is a FloatEvalResult
        filtered = [log_entry for log_entry in log_entries if isinstance(log_entry.eval_result, FloatEvalResult)]
        # Raise a warning if there are valid entries that are not FloatEvalResult
        if len(filtered) < len(log_entries):
            warnings.warn(
                f"FloatEvaluator: {len(log_entries) - len(filtered)} log entries ignored because their eval_result is not a FloatEvalResult."
            )
        return filtered

    def _eval(self, log_entries: List["LogEntry"]) -> Dict[str, Any]:
        '''
        Evaluate the log entries and return a dictionary of the results.
        '''
        # If there are any invalid eval results, count them as 0
        values = []
        for log_entry in log_entries:
            if isinstance(log_entry.eval_result, FloatEvalResult):
                values.append(log_entry.eval_result.result)
            else:
                # Count invalid eval results as 0
                values.append(0.0)

        # Count the number of invalid eval results
        invalid_count = sum(
            1 for log_entry in log_entries if not isinstance(log_entry.eval_result, FloatEvalResult)
        )

        return {
            'mean': np.mean(values) if values else 0.0,
            'std': np.std(values) if values else 0.0,
            'invalid_count': invalid_count,
        }

class BooleanEvaluator(BaseEvaluator):
    '''
    Evaluator for boolean eval results.

    Returns a dictionary with the following keys:
    - pass_rate: the percentage of log entries that passed the evaluation
    - true_count: the number of log entries that evaluated to True
    - false_count: the number of log entries that evaluated to False
    - invalid_count: the number of invalid eval results
    '''
    def _filter(self, log_entries: List["LogEntry"]) -> List["LogEntry"]:
        '''
        Filter out log entries that are not valid and that are not a boolean eval result
        '''
        log_entries = super()._filter(log_entries)
        # Only keep log entries whose eval_result is a BooleanEvalResult
        filtered = [log_entry for log_entry in log_entries if isinstance(log_entry.eval_result, BoolEvalResult)]
        # Raise a warning if there are valid entries that are not BooleanEvalResult
        if len(filtered) < len(log_entries):
            warnings.warn(
                f"BooleanEvaluator: {len(log_entries) - len(filtered)} log entries ignored because their eval_result is not a BooleanEvalResult."
            )
        return filtered

    def _eval(self, log_entries: List["LogEntry"]) -> Dict[str, Any]:
        '''
        Evaluate the log entries and return a dictionary of the results.
        '''
        true_count = 0
        false_count = 0
        invalid_count = 0
        total = len(log_entries)

        for log_entry in log_entries:
            if isinstance(log_entry.eval_result, BoolEvalResult):
                if log_entry.eval_result.result is True:
                    true_count += 1
                elif log_entry.eval_result.result is False:
                    false_count += 1
                else:
                    # Handles the case where result is not strictly True/False
                    invalid_count += 1
            else:
                invalid_count += 1

        pass_rate = (true_count / total) if total > 0 else 0.0

        return {
            'pass_rate': pass_rate,
            'true_count': true_count,
            'false_count': false_count,
            'invalid_count': invalid_count
        }