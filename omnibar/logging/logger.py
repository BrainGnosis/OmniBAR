# © 2023 BrainGnosis Inc. All rights reserved.

"""
Benchmark Logger Module

This module provides comprehensive logging functionality for benchmark operations.
It includes the BenchmarkLogger class for managing multiple benchmark logs indexed
by both benchmark_id and objective_id, with powerful filtering and pretty-printing 
capabilities.

Key Classes:
- LogEntry: Individual log entries with evaluation results
- BenchmarkLog: Collection of log entries for a specific benchmark-objective pair
- BenchmarkLogger: Main logger managing multiple benchmark logs with filtering and display
- Colors: Professional color system for terminal output
- ConsoleFormatter: Utilities for clean console formatting

Features:
- Multi-level filtering by benchmark_id and objective_id
- Professional console output with color support
- Statistics and summaries across multiple logs
- JSON serialization/deserialization
- Pretty printing with multiple detail levels and sorting options

Usage Examples:

    # Create logger and add logs
    logger = BenchmarkLogger()

    # Pretty print with different options
    logger.pretty_print()  # Show all logs with summary detail
    logger.pretty_print(detail_level="detailed")  # Show entries too
    logger.pretty_print(benchmark_ids=[bench_id1])  # Filter by benchmarks
    logger.pretty_print(sort_by="entries_count")  # Sort by entry count

    # Quick summary
    logger.print_summary()

    # Detailed view of specific log
    logger.print_log_details(benchmark_id, objective_id)

    # For AI-powered analysis, use AILogger from ai_logger module
    from omnibar.logging.ai_logger import AILogger
    ai_logger = AILogger()
"""

import uuid
from pydantic import BaseModel, InstanceOf
from omnibar.core.types import (
    EvalResult, ValidEvalResult, InvalidEvalResult
)
from omnibar.logging.evaluator import BaseEvaluator

from typing import Any, Dict, List, Iterator, Optional
from datetime import datetime
import json



class Colors:
    """Professional ANSI color codes for terminal output with production-grade control."""
    
    # Modern color palette inspired by popular CLI tools
    PRIMARY = '\033[38;2;99;102;241m'      # Indigo - primary brand color
    SUCCESS = '\033[38;2;34;197;94m'       # Green - success/positive
    WARNING = '\033[38;2;251;191;36m'      # Amber - warnings
    ERROR = '\033[38;2;239;68;68m'         # Red - errors
    INFO = '\033[38;2;59;130;246m'         # Blue - information
    MUTED = '\033[38;2;107;114;128m'       # Gray - secondary text
    ACCENT = '\033[38;2;139;92;246m'       # Purple - accents
    
    # Legacy colors for compatibility
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Background colors
    BG_PRIMARY = '\033[48;2;99;102;241m'
    BG_SUCCESS = '\033[48;2;34;197;94m'
    BG_WARNING = '\033[48;2;251;191;36m'
    BG_ERROR = '\033[48;2;239;68;68m'
    BG_INFO = '\033[48;2;59;130;246m'
    BG_MUTED = '\033[48;2;107;114;128m'
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    RESET = '\033[0m'
    
    # Global color control flag
    _colors_enabled = True
    
    @classmethod
    def enable_colors(cls) -> None:
        """Enable colored output globally."""
        cls._colors_enabled = True
    
    @classmethod
    def disable_colors(cls) -> None:
        """Disable colored output globally (for testing/production logs)."""
        cls._colors_enabled = False
    
    @classmethod
    def are_colors_enabled(cls) -> bool:
        """Check if colors are currently enabled."""
        return cls._colors_enabled
    
    @classmethod
    def colorize(cls, text: str, color: str, style: str = '') -> str:
        """Apply color and style to text with production-grade control."""
        if not cls._colors_enabled:
            return text
        return f"{style}{color}{text}{cls.RESET}"
    
    @classmethod
    def primary(cls, text: str, bold: bool = False) -> str:
        """Apply primary color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.PRIMARY, style)
    
    @classmethod
    def success(cls, text: str, bold: bool = False) -> str:
        """Apply success color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.SUCCESS, style)
    
    @classmethod
    def warning(cls, text: str, bold: bool = False) -> str:
        """Apply warning color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.WARNING, style)
    
    @classmethod
    def error(cls, text: str, bold: bool = False) -> str:
        """Apply error color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.ERROR, style)
    
    @classmethod
    def info(cls, text: str, bold: bool = False) -> str:
        """Apply info color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.INFO, style)
    
    @classmethod
    def muted(cls, text: str, dim: bool = True) -> str:
        """Apply muted color with optional dim styling."""
        style = cls.DIM if dim else ''
        return cls.colorize(text, cls.MUTED, style)
    
    @classmethod
    def accent(cls, text: str, bold: bool = False) -> str:
        """Apply accent color with optional bold styling."""
        style = cls.BOLD if bold else ''
        return cls.colorize(text, cls.ACCENT, style)
    
    @classmethod
    def auto_detect_color_support(cls) -> bool:
        """Auto-detect if the terminal supports colors."""
        import os
        import sys
        
        # Check if we're in a terminal that supports colors
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
            
        # Check environment variables that indicate color support
        term = os.environ.get('TERM', '')
        colorterm = os.environ.get('COLORTERM', '')
        
        if 'color' in term.lower() or colorterm:
            return True
            
        # Common terminals that support colors
        color_terms = ['xterm', 'xterm-256color', 'screen', 'tmux', 'rxvt']
        return any(color_term in term for color_term in color_terms)

class ConsoleFormatter:
    """Professional console formatting utilities for clean output."""
    
    @staticmethod
    def create_separator(width: int = 80, char: str = "─", style: str = "simple") -> str:
        """Create a professional separator line."""
        if style == "simple":
            return char * width
        elif style == "double":
            return "═" * width
        elif style == "dotted":
            return "┈" * width
        else:
            return char * width
    
    @staticmethod
    def create_header(title: str, width: int = 80, style: str = "box") -> str:
        """Create a professional header with consistent styling."""
        if style == "box":
            padding = (width - len(title) - 2) // 2
            left_pad = " " * padding
            right_pad = " " * (width - len(title) - 2 - padding)
            return f"┌{'─' * (width - 2)}┐\n│{left_pad}{title}{right_pad}│\n└{'─' * (width - 2)}┘"
        elif style == "simple":
            return f"{title}\n{ConsoleFormatter.create_separator(len(title), '─')}"
        elif style == "minimal":
            return f"{title}"
        else:
            return title
    
    @staticmethod
    def create_table_row(columns: List[str], widths: List[int], separator: str = " │ ") -> str:
        """Create a formatted table row with proper alignment.""" 
        formatted_columns = []
        for i, (col, width) in enumerate(zip(columns, widths)):
            # Truncate if too long, pad if too short
            if len(col) > width:
                col = col[:width-3] + "..."
            formatted_columns.append(col.ljust(width))
        
        return separator.join(formatted_columns)
    
    @staticmethod
    def create_table_separator(widths: List[int], style: str = "light") -> str:
        """Create a table separator line."""
        if style == "light":
            parts = ["─" * w for w in widths]
            return "─┼─".join(parts)
        elif style == "heavy":
            parts = ["━" * w for w in widths]
            return "━┿━".join(parts)
        else:
            parts = ["-" * w for w in widths]
            return "-+-".join(parts)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_count(count: int) -> str:
        """Format large numbers in a readable way."""
        if count < 1000:
            return str(count)
        elif count < 1000000:
            return f"{count/1000:.1f}K"
        else:
            return f"{count/1000000:.1f}M"
    
    @staticmethod
    def truncate_uuid(uuid_str: str, length: int = 8) -> str:
        """Truncate UUID for display while keeping readability."""
        return f"{str(uuid_str)[:length]}..."
    
    @staticmethod
    def create_status_indicator(status: str) -> str:
        """Create modern status indicators."""
        indicators = {
            "success": "✓",
            "error": "✗", 
            "warning": "⚠",
            "info": "ℹ",
            "pending": "◦",
            "running": "▶",
            "completed": "✓",
            "failed": "✗"
        }
        return indicators.get(status.lower(), "•")

    @staticmethod
    def get_eval_result_color(eval_result) -> str:
        """Get appropriate color for eval result type based on validity."""
        if isinstance(eval_result, ValidEvalResult):
            return "success"  # Green for valid results
        elif isinstance(eval_result, InvalidEvalResult):
            return "error"    # Red for invalid results
        else:
            return "warning"  # Amber for unknown/base types

class LogEntry(BaseModel):
    objective_id: uuid.UUID

    eval_result: InstanceOf[EvalResult]
    evaluated_output: Dict[str, Any]

    timestamp: datetime
    metadata: Dict[str, Any]

class BenchmarkLog(BaseModel):
    benchmark_id: uuid.UUID
    objective_id: uuid.UUID

    time_started: datetime
    time_ended: datetime

    entries: List[LogEntry]
    metadata: Dict[str, Any]
    evaluator: Optional[BaseEvaluator] = None

    def eval(self, filter_results: bool = False) -> Dict[str, Any]:
        '''
        Evaluate the log entries and return a dictionary of the results.
        '''
        if self.evaluator is None:
            return {"error": "No evaluator available"}
        return self.evaluator.eval(self.entries, filter_results)  
    
    def model_dump_json(self, **kwargs) -> str:
        """
        Override Pydantic's JSON serialization to include all fields except 'evaluator',
        and instead add the evaluation results (from eval()) under the key 'evaluation'.
        """
        # Use Pydantic's dict() to get all fields except 'evaluator'
        data = self.model_dump(exclude={"evaluator"}, **kwargs)
        # Add the evaluation results
        data["evaluation"] = self.eval()
        # Use Pydantic's json encoder for serialization with default handling

        return json.dumps(data, default=str)

    def start(self) -> None:
        '''
        Start the benchmark.
        '''
        self.time_started = datetime.now()

    def end(self) -> None:
        '''
        End the benchmark.
        '''
        self.time_ended = datetime.now()

    def log(self, log_entry: LogEntry) -> None:
        '''
        Log a log entry.
        '''
        self.entries.append(log_entry)

    def __len__(self) -> int:
        '''
        Return the number of log entries.
        '''
        return len(self.entries)
    
    def __iter__(self) -> Iterator[LogEntry]:
        '''
        Iterate over the log entries.
        '''
        return iter(self.entries)
    
    def __getitem__(self, index: int) -> LogEntry:
        '''
        Get a log entry by index.
        '''
        return self.entries[index]
    
    def __setitem__(self, index: int, log_entry: LogEntry) -> None:
        '''
        Set a log entry by index.
        '''
        self.entries[index] = log_entry

    def __delitem__(self, index: int) -> None:
        '''
        Delete a log entry by index.
        '''
        del self.entries[index]

class BenchmarkLogger(BaseModel):
    '''
    Logger for benchmarks that manages multiple benchmark logs indexed by benchmark_id and objective_id.

    This class provides functionality to:
    - Store and retrieve benchmark logs using both benchmark_id and objective_id as keys
    - Filter logs by benchmark_id, objective_id, or both
    - Get statistics and summaries across multiple logs
    - Serialize/deserialize the entire logger state
    - Pretty printing with color support and professional formatting
    '''

    # Nested dictionary: {benchmark_id: {objective_id: BenchmarkLog}}
    logs: Dict[uuid.UUID, Dict[uuid.UUID, BenchmarkLog]] = {}
    metadata: Dict[str, Any] = {}
    





    def add_log(self, benchmark_log: BenchmarkLog) -> None:
        '''
        Add a benchmark log to the logger.

        Args:
            benchmark_log: The BenchmarkLog instance to add
        '''
        benchmark_id = benchmark_log.benchmark_id
        objective_id = benchmark_log.objective_id

        if benchmark_id not in self.logs:
            self.logs[benchmark_id] = {}

        self.logs[benchmark_id][objective_id] = benchmark_log

    def get_log(self, benchmark_id: uuid.UUID, objective_id: uuid.UUID) -> BenchmarkLog:
        '''
        Get a specific benchmark log by benchmark_id and objective_id.

        Args:
            benchmark_id: The benchmark ID
            objective_id: The objective ID

        Returns:
            The BenchmarkLog instance

        Raises:
            KeyError: If the log doesn't exist
        '''
        if benchmark_id not in self.logs:
            raise KeyError(f"Benchmark ID {benchmark_id} not found")
        if objective_id not in self.logs[benchmark_id]:
            raise KeyError(f"Objective ID {objective_id} not found for benchmark {benchmark_id}")

        return self.logs[benchmark_id][objective_id]

    def get_logs_by_benchmark(self, benchmark_id: uuid.UUID) -> Dict[uuid.UUID, BenchmarkLog]:
        '''
        Get all logs for a specific benchmark_id.

        Args:
            benchmark_id: The benchmark ID

        Returns:
            Dictionary of {objective_id: BenchmarkLog} for the benchmark

        Raises:
            KeyError: If the benchmark_id doesn't exist
        '''
        if benchmark_id not in self.logs:
            raise KeyError(f"Benchmark ID {benchmark_id} not found")

        return self.logs[benchmark_id].copy()

    def get_logs_by_objective(self, objective_id: uuid.UUID) -> Dict[uuid.UUID, BenchmarkLog]:
        '''
        Get all logs for a specific objective_id across all benchmarks.

        Args:
            objective_id: The objective ID

        Returns:
            Dictionary of {benchmark_id: BenchmarkLog} for the objective
        '''
        result = {}
        for benchmark_id, objectives in self.logs.items():
            if objective_id in objectives:
                result[benchmark_id] = objectives[objective_id]

        return result

    def get_all_benchmark_ids(self) -> List[uuid.UUID]:
        '''
        Get all unique benchmark IDs in the logger.

        Returns:
            List of benchmark IDs
        '''
        return list(self.logs.keys())

    def get_all_objective_ids(self) -> List[uuid.UUID]:
        '''
        Get all unique objective IDs across all benchmarks.

        Returns:
            List of objective IDs
        '''
        objective_ids = set()
        for objectives in self.logs.values():
            objective_ids.update(objectives.keys())
        return list(objective_ids)

    def get_objective_ids_for_benchmark(self, benchmark_id: uuid.UUID) -> List[uuid.UUID]:
        '''
        Get all objective IDs for a specific benchmark.

        Args:
            benchmark_id: The benchmark ID

        Returns:
            List of objective IDs for the benchmark

        Raises:
            KeyError: If the benchmark_id doesn't exist
        '''
        if benchmark_id not in self.logs:
            raise KeyError(f"Benchmark ID {benchmark_id} not found")

        return list(self.logs[benchmark_id].keys())

    def has_log(self, benchmark_id: uuid.UUID, objective_id: uuid.UUID) -> bool:
        '''
        Check if a log exists for the given benchmark_id and objective_id.

        Args:
            benchmark_id: The benchmark ID
            objective_id: The objective ID

        Returns:
            True if the log exists, False otherwise
        '''
        return (benchmark_id in self.logs and
                objective_id in self.logs.get(benchmark_id, {}))

    def remove_log(self, benchmark_id: uuid.UUID, objective_id: uuid.UUID) -> bool:
        '''
        Remove a specific log.

        Args:
            benchmark_id: The benchmark ID
            objective_id: The objective ID

        Returns:
            True if the log was removed, False if it didn't exist
        '''
        if self.has_log(benchmark_id, objective_id):
            del self.logs[benchmark_id][objective_id]
            # Clean up empty benchmark entries
            if not self.logs[benchmark_id]:
                del self.logs[benchmark_id]
            return True
        return False

    def clear_benchmark(self, benchmark_id: uuid.UUID) -> bool:
        '''
        Remove all logs for a specific benchmark.

        Args:
            benchmark_id: The benchmark ID

        Returns:
            True if the benchmark was removed, False if it didn't exist
        '''
        if benchmark_id in self.logs:
            del self.logs[benchmark_id]
            return True
        return False

    def get_all_logs(self) -> List[BenchmarkLog]:
        '''
        Get all benchmark logs as a flat list.

        Returns:
            List of all BenchmarkLog instances
        '''
        all_logs = []
        for objectives in self.logs.values():
            all_logs.extend(objectives.values())
        return all_logs

    def filter_logs(self,
                   benchmark_ids: List[uuid.UUID] = None,
                   objective_ids: List[uuid.UUID] = None) -> List[BenchmarkLog]:
        '''
        Filter logs by benchmark_ids and/or objective_ids.

        Args:
            benchmark_ids: List of benchmark IDs to include (None for all)
            objective_ids: List of objective IDs to include (None for all)

        Returns:
            List of filtered BenchmarkLog instances
        '''
        filtered_logs = []

        for benchmark_id, objectives in self.logs.items():
            if benchmark_ids is not None and benchmark_id not in benchmark_ids:
                continue

            for objective_id, log in objectives.items():
                if objective_ids is not None and objective_id not in objective_ids:
                    continue

                filtered_logs.append(log)

        return filtered_logs

    def get_statistics(self,
                      benchmark_ids: List[uuid.UUID] = None,
                      objective_ids: List[uuid.UUID] = None) -> Dict[str, Any]:
        '''
        Get statistics across multiple logs.

        Args:
            benchmark_ids: List of benchmark IDs to include (None for all)
            objective_ids: List of objective IDs to include (None for all)

        Returns:
            Dictionary with statistics including:
            - total_logs: Total number of logs
            - total_entries: Total number of log entries across all logs
            - benchmarks_count: Number of unique benchmarks
            - objectives_count: Number of unique objectives
            - avg_entries_per_log: Average entries per log
        '''
        filtered_logs = self.filter_logs(benchmark_ids, objective_ids)

        if not filtered_logs:
            return {
                'total_logs': 0,
                'total_entries': 0,
                'benchmarks_count': 0,
                'objectives_count': 0,
                'avg_entries_per_log': 0.0
            }

        total_entries = sum(len(log) for log in filtered_logs)
        benchmarks_in_filter = set()
        objectives_in_filter = set()

        for log in filtered_logs:
            benchmarks_in_filter.add(log.benchmark_id)
            objectives_in_filter.add(log.objective_id)

        return {
            'total_logs': len(filtered_logs),
            'total_entries': total_entries,
            'benchmarks_count': len(benchmarks_in_filter),
            'objectives_count': len(objectives_in_filter),
            'avg_entries_per_log': total_entries / len(filtered_logs) if filtered_logs else 0.0
        }

    def to_json(self, include_evaluations: bool = True) -> str:
        '''
        Serialize the logger to JSON.

        Args:
            include_evaluations: Whether to include evaluation results in the logs

        Returns:
            JSON string representation
        '''
        data = {
            'metadata': self.metadata,
            'logs': {}
        }

        for benchmark_id, objectives in self.logs.items():
            data['logs'][str(benchmark_id)] = {}
            for objective_id, log in objectives.items():
                if include_evaluations:
                    log_data = json.loads(log.model_dump_json())
                else:
                    # Exclude evaluator and evaluation for lighter serialization
                    log_data = log.model_dump(exclude={'evaluator'})
                    log_data = json.loads(json.dumps(log_data, default=str))
                data['logs'][str(benchmark_id)][str(objective_id)] = log_data

        return json.dumps(data, default=str, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'BenchmarkLogger':
        '''
        Deserialize a logger from JSON.

        Note: This creates BenchmarkLog instances without evaluators,
        as evaluators cannot be easily serialized/deserialized.

        Args:
            json_str: JSON string representation

        Returns:
            BenchmarkLogger instance
        '''
        data = json.loads(json_str)
        logger = cls(metadata=data.get('metadata', {}))

        # Note: This will create BenchmarkLog instances without evaluators
        # as evaluators cannot be easily reconstructed from JSON
        for benchmark_id_str, objectives_data in data.get('logs', {}).items():
            benchmark_id = uuid.UUID(benchmark_id_str)
            for objective_id_str, log_data in objectives_data.items():
                objective_id = uuid.UUID(objective_id_str)

                # Remove evaluation data if present (it's computed dynamically)
                if 'evaluation' in log_data:
                    del log_data['evaluation']

                # Create log without evaluator (will need to be set separately)
                log_data_copy = log_data.copy()
                log_data_copy['benchmark_id'] = benchmark_id
                log_data_copy['objective_id'] = objective_id

                # Convert string timestamps back to datetime
                if 'time_started' in log_data_copy:
                    log_data_copy['time_started'] = datetime.fromisoformat(log_data_copy['time_started'])
                if 'time_ended' in log_data_copy:
                    log_data_copy['time_ended'] = datetime.fromisoformat(log_data_copy['time_ended'])

                # Convert string UUIDs in entries back to UUID objects
                for entry in log_data_copy.get('entries', []):
                    entry['objective_id'] = uuid.UUID(entry['objective_id'])
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])

                # Create BenchmarkLog without evaluator
                benchmark_log = BenchmarkLog(**{k: v for k, v in log_data_copy.items() if k != 'evaluator'})
                logger.add_log(benchmark_log)

        return logger
    
    

    def __len__(self) -> int:
        '''
        Return the total number of logs in the logger.

        Returns:
            Total number of benchmark logs
        '''
        return sum(len(objectives) for objectives in self.logs.values())

    def __iter__(self) -> Iterator[BenchmarkLog]:
        '''
        Iterate over all benchmark logs.

        Returns:
            Iterator over all BenchmarkLog instances
        '''
        for objectives in self.logs.values():
            yield from objectives.values()

    def __contains__(self, item) -> bool:
        '''
        Check if a benchmark_id or (benchmark_id, objective_id) pair exists.

        Args:
            item: Either a benchmark_id (UUID) or a tuple (benchmark_id, objective_id)

        Returns:
            True if the item exists, False otherwise
        '''
        if isinstance(item, uuid.UUID):
            return item in self.logs
        elif isinstance(item, tuple) and len(item) == 2:
            benchmark_id, objective_id = item
            return self.has_log(benchmark_id, objective_id)
        return False

    def pretty_print(self,
                     benchmark_ids: List[uuid.UUID] = None,
                     objective_ids: List[uuid.UUID] = None,
                     detail_level: str = "summary",
                     include_evaluations: bool = True,
                     sort_by: str = "benchmark_id",
                     max_entries_per_log: int = 5,
                     use_colors: bool = None) -> None:
        '''
        Pretty print benchmark logs with filtering and formatting options.

        Args:
            benchmark_ids: List of benchmark IDs to include (None for all)
            objective_ids: List of objective IDs to include (None for all)
            detail_level: Level of detail - "summary", "detailed", or "full"
            include_evaluations: Whether to include evaluation results
            sort_by: Sort logs by - "benchmark_id", "objective_id", "time_started", "entries_count"
            max_entries_per_log: Maximum number of entries to show per log (for detailed view)
            use_colors: Whether to use colors (None=auto-detect, True=force colors, False=no colors)
        '''
        # Handle color control professionally
        original_color_state = Colors.are_colors_enabled()
        if use_colors is not None:
            if use_colors:
                Colors.enable_colors()
            else:
                Colors.disable_colors()
        elif use_colors is None and not Colors.auto_detect_color_support():
            Colors.disable_colors()
        
        try:
            filtered_logs = self.filter_logs(benchmark_ids, objective_ids)

            if not filtered_logs:
                print()
                print(Colors.warning("No benchmark logs found matching the specified criteria", bold=True))
                print(Colors.muted("Try adjusting your filters or run some benchmarks first"))
                print()
                return

            # Sort logs
            if sort_by == "benchmark_id":
                filtered_logs.sort(key=lambda x: str(x.benchmark_id))
            elif sort_by == "objective_id":
                filtered_logs.sort(key=lambda x: str(x.objective_id))
            elif sort_by == "time_started":
                filtered_logs.sort(key=lambda x: x.time_started)
            elif sort_by == "entries_count":
                filtered_logs.sort(key=lambda x: len(x.entries), reverse=True)

            # Print clean header
            print()
            title = f"Benchmark Logger ({len(filtered_logs)} logs)"
            print(Colors.primary(title, bold=True))
            print(Colors.muted(ConsoleFormatter.create_separator(len(title))))
            print()

            # Print summary statistics in a clean table format
            stats = self.get_statistics(benchmark_ids, objective_ids)
            self._print_statistics_table(stats)
            print()

            # Print each log
            if detail_level != "summary":
                print(Colors.info("Benchmark Logs", bold=True))
                print(Colors.muted(ConsoleFormatter.create_separator(14)))
                print()
                for i, log in enumerate(filtered_logs, 1):
                    self._print_single_log_clean(log, i, detail_level, include_evaluations, max_entries_per_log)
            else:
                self._print_logs_summary_table(filtered_logs)
        
        finally:
            # Always restore original color state
            if use_colors is not None:
                if original_color_state:
                    Colors.enable_colors()
                else:
                    Colors.disable_colors()

    def _print_statistics_table(self, stats: Dict[str, Any]) -> None:
        """Print statistics in a clean table format."""
        # Define table structure
        headers = ["Metric", "Value"]
        widths = [20, 15]
        
        # Print table header
        header_row = ConsoleFormatter.create_table_row(headers, widths)
        print(Colors.muted(header_row))
        separator = ConsoleFormatter.create_table_separator(widths, "light")
        print(Colors.muted(separator))
        
        # Print table rows
        rows = [
            ["Total Logs", ConsoleFormatter.format_count(stats['total_logs'])],
            ["Total Entries", ConsoleFormatter.format_count(stats['total_entries'])],
            ["Unique Benchmarks", str(stats['benchmarks_count'])],
            ["Unique Objectives", str(stats['objectives_count'])],
            ["Avg Entries/Log", f"{stats['avg_entries_per_log']:.1f}"]
        ]
        
        for row in rows:
            print(f"{Colors.info(row[0].ljust(widths[0]))} {Colors.success(row[1])}")

    def _print_logs_summary_table(self, logs: List[BenchmarkLog]) -> None:
        """Print logs in a summary table format."""
        if not logs:
            return
            
        print(Colors.info("Summary", bold=True))
        print(Colors.muted(ConsoleFormatter.create_separator(7)))
        print()
        
        # Define table structure
        headers = ["#", "Benchmark ID", "Objective ID", "Entries", "Duration", "Status"]
        widths = [3, 16, 16, 8, 10, 8]
        
        # Print table header
        header_row = ConsoleFormatter.create_table_row(headers, widths)
        print(Colors.muted(header_row))
        separator = ConsoleFormatter.create_table_separator(widths, "light")
        print(Colors.muted(separator))
        
        # Print table rows
        for i, log in enumerate(logs, 1):
            bench_id = ConsoleFormatter.truncate_uuid(log.benchmark_id, 14)
            obj_id = ConsoleFormatter.truncate_uuid(log.objective_id, 14)
            entries = str(len(log.entries))
            
            # Calculate duration
            duration = "N/A"
            if log.time_started and log.time_ended:
                delta = log.time_ended - log.time_started
                duration = ConsoleFormatter.format_duration(delta.total_seconds())
            
            # Determine status
            status = "completed" if log.time_ended else "running"
            status_indicator = ConsoleFormatter.create_status_indicator(status)
            
            row = [
                str(i),
                bench_id,
                obj_id,
                entries,
                duration,
                f"{status_indicator} {status}"
            ]
            
            formatted_row = ConsoleFormatter.create_table_row(row, widths)
            print(formatted_row)

    def _print_single_log_clean(self,
                               log: BenchmarkLog,
                               index: int,
                               detail_level: str,
                               include_evaluations: bool,
                               max_entries: int) -> None:
        """Print a single benchmark log with clean, modern formatting."""
        # Log header
        log_title = f"[{index}] Benchmark Log"
        print(Colors.primary(log_title, bold=True))
        
        # Basic info in two columns
        bench_id = ConsoleFormatter.truncate_uuid(log.benchmark_id, 12)
        obj_id = ConsoleFormatter.truncate_uuid(log.objective_id, 12)
        
        print(f"  {Colors.info('Benchmark:', bold=True)} {Colors.accent(bench_id)}")
        print(f"  {Colors.info('Objective:', bold=True)} {Colors.primary(obj_id)}")
        print(f"  {Colors.info('Entries:', bold=True)}   {Colors.success(str(len(log.entries)))}")
        
        # Timing information
        if log.time_started:
            time_str = log.time_started.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {Colors.info('Started:', bold=True)}   {Colors.accent(time_str)}")
            
        if log.time_ended:
            time_str = log.time_ended.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {Colors.info('Ended:', bold=True)}     {Colors.accent(time_str)}")
            
            if log.time_started:
                duration = log.time_ended - log.time_started
                duration_str = ConsoleFormatter.format_duration(duration.total_seconds())
                print(f"  {Colors.info('Duration:', bold=True)}  {Colors.warning(duration_str)}")

        # Metadata (if any)
        if log.metadata:
            print(f"  {Colors.info('Metadata:', bold=True)}")
            # Format metadata as indented JSON
            import json
            metadata_json = json.dumps(log.metadata, indent=2, default=str)
            # Indent each line with 4 spaces to align with other content
            indented_metadata = '\n'.join(f"    {line}" for line in metadata_json.split('\n'))
            print(f"{Colors.primary(indented_metadata)}")

        # Evaluation results
        if include_evaluations and hasattr(log, 'evaluator') and log.evaluator:
            try:
                eval_results = log.eval()
                print(f"  {Colors.info('Evaluation:', bold=True)} {Colors.success('✓')}")
                # Format evaluation results as indented JSON
                import json
                eval_json = json.dumps(eval_results, indent=2, default=str)
                indented_eval = '\n'.join(f"    {line}" for line in eval_json.split('\n'))
                print(f"{Colors.primary(indented_eval)}")
            except Exception as e:
                print(f"  {Colors.info('Evaluation:', bold=True)} {Colors.error('✗')} {Colors.error(str(e))}")

        # Show entries if detailed view
        if detail_level in ["detailed", "full"] and log.entries:
            print()
            entries_title = f"Recent Entries ({min(max_entries, len(log.entries))} of {len(log.entries)})"
            print(f"  {Colors.info(entries_title, bold=True)}")
            
            entries_to_show = log.entries[-max_entries:] if len(log.entries) > max_entries else log.entries
            
            for j, entry in enumerate(entries_to_show, 1):
                time_str = entry.timestamp.strftime('%H:%M:%S')
                result_type = type(entry.eval_result).__name__
                result_color = ConsoleFormatter.get_eval_result_color(entry.eval_result)
                
                # Color-code the result type: green for valid, red for invalid
                if result_color == "success":
                    colored_result_type = Colors.success(result_type, bold=True)
                elif result_color == "error":
                    colored_result_type = Colors.error(result_type, bold=True)
                else:
                    colored_result_type = Colors.warning(result_type, bold=True)
                
                print(f"    {Colors.primary(f'[{j}]')} {Colors.accent(time_str)} - {colored_result_type}")
                
                if detail_level == "detailed":
                    # Color the result content based on validity (same as result type)
                    result_color = ConsoleFormatter.get_eval_result_color(entry.eval_result)
                    if result_color == "success":
                        colored_result_content = Colors.success(str(entry.eval_result))
                    elif result_color == "error":
                        colored_result_content = Colors.error(str(entry.eval_result))
                    else:
                        colored_result_content = Colors.warning(str(entry.eval_result))
                    
                    print(f"        {Colors.info('Result:', bold=True)} {colored_result_content}")
                
                elif detail_level == "full":
                    # Color the result content based on validity (same as result type)
                    result_color = ConsoleFormatter.get_eval_result_color(entry.eval_result)
                    if result_color == "success":
                        colored_result_content = Colors.success(str(entry.eval_result))
                    elif result_color == "error":
                        colored_result_content = Colors.error(str(entry.eval_result))
                    else:
                        colored_result_content = Colors.warning(str(entry.eval_result))
                    
                    print(f"        {Colors.info('Result:', bold=True)} {colored_result_content}")
                    if entry.evaluated_output:
                        print(f"        {Colors.info('Output:', bold=True)}")
                        # Format output as indented JSON
                        import json
                        output_json = json.dumps(entry.evaluated_output, indent=2, default=str)
                        indented_output = '\n'.join(f"          {line}" for line in output_json.split('\n'))
                        print(f"{Colors.primary(indented_output)}")
                    if entry.metadata:
                        print(f"        {Colors.info('Metadata:', bold=True)}")
                        metadata_json = json.dumps(entry.metadata, indent=2, default=str)
                        indented_meta = '\n'.join(f"          {line}" for line in metadata_json.split('\n'))
                        print(f"{Colors.primary(indented_meta)}")
        
        print()  # Add spacing between logs



    def print_summary(self,
                     benchmark_ids: List[uuid.UUID] = None,
                     objective_ids: List[uuid.UUID] = None,
                     use_colors: bool = None) -> None:
        '''
        Print a concise summary of logs matching the filter criteria.

        Args:
            benchmark_ids: List of benchmark IDs to include (None for all)
            objective_ids: List of objective IDs to include (None for all)
            use_colors: Whether to use colors (None=auto-detect, True=force colors, False=no colors)
        '''
        # Handle color control professionally
        original_color_state = Colors.are_colors_enabled()
        if use_colors is not None:
            if use_colors:
                Colors.enable_colors()
            else:
                Colors.disable_colors()
        elif use_colors is None and not Colors.auto_detect_color_support():
            Colors.disable_colors()
        
        try:
            stats = self.get_statistics(benchmark_ids, objective_ids)

            print()
            title = "Benchmark Summary"
            print(Colors.primary(title, bold=True))
            print(Colors.muted(ConsoleFormatter.create_separator(len(title))))
            print()
            
            # Print statistics table
            self._print_statistics_table(stats)

            if stats['total_logs'] > 0:
                print()
                print(Colors.info("Top Benchmarks by Entry Count", bold=True))
                print(Colors.muted(ConsoleFormatter.create_separator(31)))
                print()
                
                benchmark_stats = {}
                filtered_logs = self.filter_logs(benchmark_ids, objective_ids)

                for log in filtered_logs:
                    bench_id = ConsoleFormatter.truncate_uuid(log.benchmark_id, 8)
                    if bench_id not in benchmark_stats:
                        benchmark_stats[bench_id] = 0
                    benchmark_stats[bench_id] += len(log.entries)

                # Sort by entry count
                sorted_benchmarks = sorted(benchmark_stats.items(), key=lambda x: x[1], reverse=True)

                for i, (bench_id, entry_count) in enumerate(sorted_benchmarks[:5], 1):
                    entries_text = ConsoleFormatter.format_count(entry_count)
                    print(f"  {Colors.muted(f'{i}.')} {Colors.info(bench_id)} {Colors.muted('•')} {Colors.success(entries_text)} entries")
            
            print()
        
        finally:
            # Always restore original color state
            if use_colors is not None:
                if original_color_state:
                    Colors.enable_colors()
                else:
                    Colors.disable_colors()

    def print_log_details(self,
                         benchmark_id: uuid.UUID,
                         objective_id: uuid.UUID,
                         show_entries: bool = True,
                         max_entries: int = 10,
                         use_colors: bool = None) -> None:
        '''
        Print detailed information about a specific log.

        Args:
            benchmark_id: The benchmark ID
            objective_id: The objective ID
            show_entries: Whether to show individual entries
            max_entries: Maximum number of entries to show
            use_colors: Whether to use colors (None=auto-detect, True=force colors, False=no colors)
        '''
        # Handle color control professionally
        original_color_state = Colors.are_colors_enabled()
        if use_colors is not None:
            if use_colors:
                Colors.enable_colors()
            else:
                Colors.disable_colors()
        elif use_colors is None and not Colors.auto_detect_color_support():
            Colors.disable_colors()
        
        try:
            log = self.get_log(benchmark_id, objective_id)

            print()
            title = "Benchmark Log Details"
            print(Colors.primary(title, bold=True))
            print(Colors.muted(ConsoleFormatter.create_separator(len(title))))
            print()
            
            # Basic information
            print(f"{Colors.muted('Benchmark ID:')} {Colors.info(str(log.benchmark_id))}")
            print(f"{Colors.muted('Objective ID:')} {Colors.accent(str(log.objective_id))}")
            print(f"{Colors.muted('Total Entries:')} {Colors.success(str(len(log.entries)))}")

            if log.time_started:
                time_str = log.time_started.strftime('%Y-%m-%d %H:%M:%S')
                print(f"{Colors.muted('Started:')} {time_str}")
            if log.time_ended:
                time_str = log.time_ended.strftime('%Y-%m-%d %H:%M:%S')
                print(f"{Colors.muted('Ended:')} {time_str}")

            if log.time_started and log.time_ended:
                duration = log.time_ended - log.time_started
                duration_str = ConsoleFormatter.format_duration(duration.total_seconds())
                print(f"{Colors.muted('Duration:')} {duration_str}")

            if log.metadata:
                print(f"{Colors.muted('Metadata:')} {log.metadata}")

            # Show evaluation if possible
            if hasattr(log, 'evaluator') and log.evaluator:
                try:
                    eval_results = log.eval()
                    print(f"{Colors.muted('Evaluation:')} {Colors.success('✓')} {eval_results}")
                except Exception as e:
                    print(f"{Colors.muted('Evaluation:')} {Colors.error('✗')} {str(e)}")

            # Show entries
            if show_entries and log.entries:
                print()
                entries_header = f"Entries (showing {min(max_entries, len(log.entries))} of {len(log.entries)})"
                print(Colors.info(entries_header, bold=True))
                print(Colors.muted(ConsoleFormatter.create_separator(len(entries_header))))
                print()

                entries_to_show = log.entries[-max_entries:] if len(log.entries) > max_entries else log.entries

                for i, entry in enumerate(entries_to_show, 1):
                    timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    result_type = type(entry.eval_result).__name__
                    
                    print(f"{Colors.muted(f'[{i}]')} {timestamp_str}")
                    print(f"  {Colors.muted('Type:')} {Colors.accent(result_type)}")
                    print(f"  {Colors.muted('Result:')} {entry.eval_result}")
                    
                    if entry.evaluated_output:
                        print(f"  {Colors.muted('Output:')} {entry.evaluated_output}")
                    if entry.metadata:
                        print(f"  {Colors.muted('Metadata:')} {entry.metadata}")
                    print()
            
            print()

        except KeyError as e:
            print()
            print(Colors.error(f"Error: {str(e)}", bold=True))
            print()        
        finally:
            # Always restore original color state
            if use_colors is not None:
                if original_color_state:
                    Colors.enable_colors()
                else:
                    Colors.disable_colors()
        
