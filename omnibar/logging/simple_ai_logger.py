# © 2023 BrainGnosis Inc. All rights reserved.

"""
Simple AI Logger Module

A streamlined AI-powered logger that focuses on the essential task of comparing
benchmark evaluation results against their intended objectives. This provides
minimally sufficient but highly useful insights to users.

Key Features:
- Individual objective vs result analysis
- Summary of overall benchmark performance  
- Focus on explaining differences between expected and actual results
- Clean, simple implementation without over-engineering

Classes:
- SimpleAILogger: Extends BenchmarkLogger with focused AI analysis

Usage Example:
    from omnibar.logging.simple_ai_logger import SimpleAILogger
    
    logger = SimpleAILogger()
    logger.configure_ai()  # Use default OpenAI
    
    # Get focused analysis
    result = logger.ai_analyze()
    logger.print_ai_analysis()
"""

import uuid
import json
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from pydantic import PrivateAttr
from omnibar.logging.logger import BenchmarkLogger, BenchmarkLog, Colors, ConsoleFormatter
from omnibar.core.types import ValidEvalResult, InvalidEvalResult

# Optional AI dependencies
try:
    from langchain_openai import OpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class SimpleAILogger(BenchmarkLogger):
    """
    Simple AI-powered logger focused on objective vs result analysis.
    
    Provides clear, actionable insights about benchmark performance without
    over-engineering or unnecessary complexity.
    """
    
    # AI Configuration
    _llm: Optional[Any] = PrivateAttr(default=None)
    _custom_invoke: Optional[Callable[[str], str]] = PrivateAttr(default=None)
    _ai_enabled: bool = PrivateAttr(default=False)
    
    # Simple prompts focused on the core task
    _individual_analysis_prompt: str = PrivateAttr(default="""
Analyze this benchmark evaluation result against its intended objective.

OBJECTIVE:
- Name: {objective_name}
- Goal: {objective_goal}
- Expected: {objective_description}

ACTUAL RESULT:
- Result Type: {result_type}
- Result Value: {result_value}
- Valid: {is_valid}
- Error (if any): {error_message}

EVALUATION CONTEXT:
- Total Entries: {total_entries}
- Success Rate: {success_rate}%

Provide a focused analysis:

1. **Objective vs Result Gap**: What specific differences exist between what was expected and what was delivered?

2. **Performance Assessment**: How well did this evaluation meet the objective? Be specific about scores/values.

3. **Key Issues**: What are the main problems or failures identified? 

4. **Recommendation**: One specific action to improve this evaluation.

Keep the analysis concise but actionable. Focus on practical insights that help improve the benchmark.
""")
    
    _summary_prompt: str = PrivateAttr(default="""
Provide a comprehensive summary of these benchmark evaluation analyses.

INDIVIDUAL ANALYSES:
{individual_analyses}

OVERALL STATISTICS:
- Total Logs: {total_logs}
- Total Entries: {total_entries}
- Average Success Rate: {avg_success_rate}%

Create a summary that helps the user understand their benchmark performance:

## PERFORMANCE OVERVIEW
Summarize the overall performance across all evaluations. What patterns emerge?

## KEY FINDINGS
List 3-5 most important insights about objective vs result differences:
• [Finding 1]
• [Finding 2]  
• [Finding 3]

## CRITICAL ISSUES
What are the most serious problems that need attention?

## RECOMMENDED ACTIONS
Provide 2-3 specific, actionable recommendations to improve benchmark results.

## SUCCESS PATTERNS
What worked well? What should be maintained or expanded?

Focus on practical, actionable insights rather than generic observations.
""")
    
    def configure_ai(self, 
                    llm: Optional[Any] = None,
                    custom_invoke: Optional[Callable[[str], str]] = None) -> None:
        """
        Configure AI analysis with simple options.
        
        Args:
            llm: LangChain LLM instance (defaults to OpenAI)
            custom_invoke: Custom function that takes a prompt and returns analysis
        """
        if custom_invoke:
            self._custom_invoke = custom_invoke
            self._ai_enabled = True
        elif llm:
            self._llm = llm
            self._ai_enabled = True
        elif LANGCHAIN_AVAILABLE:
            try:
                self._llm = OpenAI(temperature=0.3, max_tokens=1500)
                self._ai_enabled = True
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI: {e}")
                self._ai_enabled = False
        else:
            raise ImportError("Install langchain and openai, or provide custom_invoke function")
    
    def _invoke_ai(self, prompt: str) -> str:
        """Simple AI invocation."""
        if self._custom_invoke:
            return self._custom_invoke(prompt)
        elif self._llm:
            return self._llm.invoke(prompt)
        else:
            return "AI not configured"
    
    def _analyze_individual_log(self, log: BenchmarkLog) -> str:
        """Analyze a single benchmark log against its objective."""
        
        # Extract objective information from metadata
        objective_name = log.metadata.get('objective_name', 'Unknown')
        objective_goal = log.metadata.get('objective_goal', 'Not specified')
        objective_description = log.metadata.get('objective_description', 'Not specified')
        
        # Calculate basic statistics
        total_entries = len(log.entries)
        valid_count = sum(1 for e in log.entries if isinstance(e.eval_result, ValidEvalResult))
        success_rate = (valid_count / total_entries * 100) if total_entries > 0 else 0
        
        # Get a representative result (latest entry)
        if log.entries:
            latest_entry = log.entries[-1]
            result_type = type(latest_entry.eval_result).__name__
            result_value = getattr(latest_entry.eval_result, 'value', 'No value')
            is_valid = isinstance(latest_entry.eval_result, ValidEvalResult)
            error_message = getattr(latest_entry.eval_result, 'error', 'None') if hasattr(latest_entry.eval_result, 'error') else 'None'
        else:
            result_type = "No results"
            result_value = "No results"
            is_valid = False
            error_message = "No entries found"
        
        # Format the prompt
        prompt = self._individual_analysis_prompt.format(
            objective_name=objective_name,
            objective_goal=objective_goal,
            objective_description=objective_description,
            result_type=result_type,
            result_value=result_value,
            is_valid=is_valid,
            error_message=error_message,
            total_entries=total_entries,
            success_rate=success_rate
        )
        
        try:
            return self._invoke_ai(prompt)
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def ai_analyze(self, 
                  benchmark_ids: Optional[List[uuid.UUID]] = None,
                  objective_ids: Optional[List[uuid.UUID]] = None) -> Dict[str, Any]:
        """
        Perform focused AI analysis of benchmark results.
        
        Args:
            benchmark_ids: Filter by benchmark IDs  
            objective_ids: Filter by objective IDs
            
        Returns:
            Dictionary with individual_analyses, summary, and statistics
        """
        if not self._ai_enabled:
            return {
                "error": "AI not configured. Call configure_ai() first.",
                "individual_analyses": [],
                "summary": "",
                "statistics": {}
            }
        
        # Get filtered logs
        filtered_logs = self.filter_logs(benchmark_ids, objective_ids)
        
        if not filtered_logs:
            return {
                "error": None,
                "individual_analyses": [],
                "summary": "No logs found matching criteria.",
                "statistics": {"total_logs": 0, "total_entries": 0}
            }
        
        try:
            # Analyze each log individually
            individual_analyses = []
            total_entries = 0
            total_valid = 0
            
            print("🔍 Analyzing individual benchmark results...")
            for i, log in enumerate(filtered_logs, 1):
                print(f"   Processing log {i}/{len(filtered_logs)}...")
                analysis = self._analyze_individual_log(log)
                individual_analyses.append({
                    "benchmark_id": str(log.benchmark_id)[:8],
                    "objective_id": str(log.objective_id)[:8], 
                    "objective_name": log.metadata.get('objective_name', 'Unknown'),
                    "analysis": analysis
                })
                
                # Update statistics
                total_entries += len(log.entries)
                total_valid += sum(1 for e in log.entries if isinstance(e.eval_result, ValidEvalResult))
            
            # Calculate overall statistics
            avg_success_rate = (total_valid / total_entries * 100) if total_entries > 0 else 0
            
            # Generate summary
            print("📊 Generating overall summary...")
            analyses_text = "\n\n".join([
                f"**{a['objective_name']}**: {a['analysis']}" 
                for a in individual_analyses
            ])
            
            summary_prompt = self._summary_prompt.format(
                individual_analyses=analyses_text,
                total_logs=len(filtered_logs),
                total_entries=total_entries,
                avg_success_rate=avg_success_rate
            )
            
            summary = self._invoke_ai(summary_prompt)
            
            return {
                "error": None,
                "individual_analyses": individual_analyses,
                "summary": summary,
                "statistics": {
                    "total_logs": len(filtered_logs),
                    "total_entries": total_entries,
                    "avg_success_rate": avg_success_rate,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "individual_analyses": [],
                "summary": "",
                "statistics": {}
            }
    
    def print_ai_analysis(self, 
                         benchmark_ids: Optional[List[uuid.UUID]] = None,
                         objective_ids: Optional[List[uuid.UUID]] = None,
                         use_colors: bool = None) -> None:
        """
        Print AI analysis with clean formatting.
        
        Args:
            benchmark_ids: Filter by benchmark IDs
            objective_ids: Filter by objective IDs  
            use_colors: Enable/disable colored output
        """
        # Handle colors
        original_colors = Colors.are_colors_enabled()
        if use_colors is not None:
            if use_colors:
                Colors.enable_colors()
            else:
                Colors.disable_colors()
        
        try:
            result = self.ai_analyze(benchmark_ids, objective_ids)
            
            if result.get("error"):
                print()
                print(Colors.error(f"❌ AI Analysis Error: {result['error']}", bold=True))
                print()
                return
            
            # Header
            print()
            print(Colors.primary("🤖 AI Benchmark Analysis", bold=True))
            print(Colors.muted("=" * 50))
            print()
            
            # Statistics
            stats = result.get("statistics", {})
            if stats:
                print(Colors.info("📊 Analysis Statistics", bold=True))
                print(f"  • Logs Analyzed: {Colors.success(str(stats.get('total_logs', 0)))}")
                print(f"  • Total Entries: {Colors.success(str(stats.get('total_entries', 0)))}")
                success_rate = stats.get('avg_success_rate', 0)
                print(f"  • Average Success Rate: {Colors.success(f'{success_rate:.1f}%')}")
                print()
            
            # Individual analyses
            individual = result.get("individual_analyses", [])
            if individual:
                print(Colors.info("🔍 Individual Objective Analysis", bold=True))
                print(Colors.muted("-" * 35))
                print()
                
                for i, analysis in enumerate(individual, 1):
                    obj_name = analysis.get("objective_name", "Unknown")
                    print(f"{Colors.accent(f'[{i}]')} {Colors.primary(obj_name, bold=True)}")
                    print(f"    {Colors.muted('Benchmark:')} {analysis.get('benchmark_id', 'Unknown')}")
                    print(f"    {Colors.muted('Objective:')} {analysis.get('objective_id', 'Unknown')}")
                    print()
                    
                    # Format the analysis with proper indentation
                    analysis_text = analysis.get("analysis", "No analysis available")
                    for line in analysis_text.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                    print()
            
            # Overall summary
            summary = result.get("summary", "")
            if summary:
                print(Colors.info("📋 Overall Summary", bold=True))
                print(Colors.muted("-" * 16))
                print()
                
                # Format summary sections
                for line in summary.split('\n'):
                    line = line.strip()
                    if line.startswith('##'):
                        # Section headers
                        section_title = line.replace('##', '').strip()
                        print(Colors.accent(f"▸ {section_title}", bold=True))
                    elif line.startswith('•') or line.startswith('-'):
                        # Bullet points
                        print(f"  {Colors.success('•')} {line[1:].strip()}")
                    elif line:
                        # Regular content
                        print(f"  {line}")
                print()
        
        finally:
            # Restore original color state
            if use_colors is not None:
                if original_colors:
                    Colors.enable_colors()
                else:
                    Colors.disable_colors()


# Export the main class
__all__ = ['SimpleAILogger']
