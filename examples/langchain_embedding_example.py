#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
FlashAttention Knowledge Benchmarking Example with LangChain and txtai

This example demonstrates benchmarking two different knowledge retrieval agents
on technical FlashAttention algorithm questions:
1. ArxivQueryAgent - Queries scientific papers from the txtai-arxiv embeddings
2. WikipediaQueryAgent - Queries general knowledge from the txtai-wikipedia embeddings

The benchmark compares how well each agent answers FlashAttention technical questions 
by using a specialized LLM judge to evaluate technical accuracy and completeness on a 0.0-1.0 scale.

BUILT-IN OMNIBAR LOGGING:
This example demonstrates pure usage of OmniBAR's built-in logging system:
- Creates a shared BenchmarkLogger instance for both benchmarkers
- All result tracking, analysis, and display handled by OmniBAR internally
- No custom logging code - relies entirely on built-in logger capabilities
- Automatic JSON export and advanced filtering through BenchmarkLogger

Architecture:
- 2 Agents: ArxivQueryAgent, WikipediaQueryAgent  
- 2 Benchmarkers: Individual OmniBarmarkers sharing one logger
- 1 Objective: FlashAttention Technical LLMJudgeObjective with FloatEvalResult (0.0-1.0)
- 1 Logger: Unified BenchmarkLogger handling all output and analysis

Requirements:
- pip install txtai
- pip install langchain langchain-openai
- Set OPENAI_API_KEY environment variable
- Internet connection to download embeddings from Hugging Face

Usage:
    python embedding_example_langchain.py
"""

import asyncio
import os
from typing import Dict, Any, List
from pathlib import Path

# Flexible environment variable loading
def load_environment_variables():
    """
    Load environment variables from various possible locations.
    
    Priority order:
    1. OMNIBAR_ENV_PATH environment variable (if set)
    2. .env in current directory  
    3. .env in parent directory (examples/)
    4. .env in project root (../../)
    5. Skip if none found
    """
    try:
        from dotenv import load_dotenv
        import os
        
        # Option 1: Check for custom env path
        custom_env = os.getenv('OMNIBAR_ENV_PATH')
        if custom_env:
            custom_path = Path(custom_env)
            if custom_path.exists():
                load_dotenv(custom_path)
                print(f"✅ Loaded environment variables from custom path: {custom_path}")
                return True
            else:
                print(f"⚠️  Custom env path not found: {custom_path}")
        
        # Option 2-4: Check common locations
        current_dir = Path(__file__).parent
        search_paths = [
            current_dir / '.env',                    # ./env
            current_dir.parent / '.env',             # ../env  
            current_dir.parent.parent / '.env'       # ../../.env (project root)
        ]
        
        for env_path in search_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded environment variables from {env_path}")
                return True
        
        print("⚠️  No .env file found in common locations")
        print("💡 To specify a custom location, set OMNIBAR_ENV_PATH environment variable")
        return False
        
    except ImportError:
        print("⚠️  python-dotenv not available, environment variables should be set manually")
        return False

# Load environment variables
load_environment_variables()

# Import OmniBAR components
from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import LLMJudgeObjective
from omnibar.core.types import FloatEvalResult
from omnibar.logging.logger import BenchmarkLogger

# LangChain imports
try:
    from langchain_core.tools import Tool
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# txtai imports
try:
    from txtai.embeddings import Embeddings
    TXTAI_AVAILABLE = True
except ImportError:
    TXTAI_AVAILABLE = False


class ArxivQueryAgent:
    """
    Agent that queries the txtai-arxiv embeddings for scientific paper information.
    
    This agent specializes in answering questions about academic research,
    scientific papers, and technical topics using the arXiv dataset.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        if not LANGCHAIN_AVAILABLE or not TXTAI_AVAILABLE:
            raise ImportError("LangChain and txtai are required")
        
        # Load the arXiv embeddings index from Hugging Face Hub
        self.embeddings = Embeddings()
        self.embeddings.load(provider="huggingface-hub", container="neuml/txtai-arxiv")
        
        # Create LangChain tool for arXiv search
        arxiv_tool = Tool(
            name="arxiv_search",
            description=(
                "Search academic papers and research from arXiv database. "
                "Use this for questions about scientific research, academic papers, "
                "technical concepts, and scholarly information. "
                "Input should be a clear search query related to research topics."
            ),
            func=self._search_arxiv
        )
        
        # Create the LangChain agent
        llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        prompt = PromptTemplate.from_template("""
You are a scientific research assistant with access to the arXiv database.
Answer questions using the most relevant academic papers and research.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
""")
        
        agent = create_react_agent(llm, [arxiv_tool], prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=[arxiv_tool],
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def _search_arxiv(self, query: str) -> str:
        """Search the arXiv embeddings and return formatted results."""
        try:
            # Search for top 3 most relevant papers
            results = self.embeddings.search(query, limit=3)
            
            if not results:
                return f"No relevant arXiv papers found for query: {query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                # Extract title and content from the result
                text = result.get('text', 'No content available')
                score = result.get('score', 0.0)
                
                formatted_results.append(f"{i}. (Relevance: {score:.3f})\n{text}\n")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Error searching arXiv: {str(e)}"
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke the arXiv agent with a query.
        
        Args:
            query: The question to answer using arXiv data
            
        Returns:
            Dict containing the agent's response and metadata
        """
        try:
            result = self.agent_executor.invoke({"input": query})
            return {
                "response": result.get("output", "No response generated"),
                "source": "arxiv",
                "query": query,
                "agent_type": "ArxivQueryAgent"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "source": "arxiv",
                "query": query,
                "agent_type": "ArxivQueryAgent"
            }


class WikipediaQueryAgent:
    """
    Agent that queries the txtai-wikipedia embeddings for general knowledge.
    
    This agent specializes in answering general knowledge questions using
    Wikipedia data, providing broad context and background information.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        if not LANGCHAIN_AVAILABLE or not TXTAI_AVAILABLE:
            raise ImportError("LangChain and txtai are required")
        
        # Load the Wikipedia embeddings index from Hugging Face Hub
        self.embeddings = Embeddings()
        self.embeddings.load(provider="huggingface-hub", container="neuml/txtai-wikipedia")
        
        # Create LangChain tool for Wikipedia search
        wiki_tool = Tool(
            name="wikipedia_search",
            description=(
                "Search general knowledge and encyclopedia information from Wikipedia. "
                "Use this for questions about people, places, events, concepts, "
                "historical information, and general background knowledge. "
                "Input should be a clear search query."
            ),
            func=self._search_wikipedia
        )
        
        # Create the LangChain agent
        llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        prompt = PromptTemplate.from_template("""
You are a knowledgeable encyclopedia assistant with access to Wikipedia.
Answer questions using the most relevant general knowledge and background information.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
""")
        
        agent = create_react_agent(llm, [wiki_tool], prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=[wiki_tool],
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def _search_wikipedia(self, query: str) -> str:
        """Search the Wikipedia embeddings and return formatted results."""
        try:
            # Search for top 3 most relevant articles
            results = self.embeddings.search(query, limit=3)
            
            if not results:
                return f"No relevant Wikipedia articles found for query: {query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                # Extract title and content from the result
                text = result.get('text', 'No content available')
                score = result.get('score', 0.0)
                
                formatted_results.append(f"{i}. (Relevance: {score:.3f})\n{text}\n")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke the Wikipedia agent with a query.
        
        Args:
            query: The question to answer using Wikipedia data
            
        Returns:
            Dict containing the agent's response and metadata
        """
        try:
            result = self.agent_executor.invoke({"input": query})
            return {
                "response": result.get("output", "No response generated"),
                "source": "wikipedia", 
                "query": query,
                "agent_type": "WikipediaQueryAgent"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "source": "wikipedia",
                "query": query,
                "agent_type": "WikipediaQueryAgent"
            }


def create_arxiv_agent() -> ArxivQueryAgent:
    """Factory function to create ArxivQueryAgent instances for OmniBAR."""
    return ArxivQueryAgent()


def create_wikipedia_agent() -> WikipediaQueryAgent:
    """Factory function to create WikipediaQueryAgent instances for OmniBAR."""
    return WikipediaQueryAgent()


def create_agent_comparison_table(shared_logger):
    """
    Generate a clean, minimal comparison table between ArXiv and Wikipedia agents.
    
    This function creates a well-formatted table showing the performance comparison
    between different knowledge source agents with real benchmark results.
    """
    # Extract results from shared logger - get evaluation summaries directly
    all_logs = shared_logger.get_all_logs()
    
    # Separate results by agent type based on benchmark metadata
    arxiv_scores = []
    wikipedia_scores = []
    
    for log in all_logs:
        if hasattr(log, 'evaluation_summary') and log.evaluation_summary:
            # Check if this is ArXiv agent based on benchmark name
            if hasattr(log, 'metadata') and log.metadata:
                benchmark_name = log.metadata.get('benchmark_name', '')
                if 'ArXiv Agent' in benchmark_name:
                    arxiv_scores.append(log.evaluation_summary.get('mean', 0.0))
                elif 'Wikipedia Agent' in benchmark_name:
                    wikipedia_scores.append(log.evaluation_summary.get('mean', 0.0))
    
    # If scores not found through metadata, try alternative extraction
    if not arxiv_scores and not wikipedia_scores:
        print("Extracting scores from log entries...")
        for log in all_logs:
            if hasattr(log, 'entries') and log.entries:
                # Get all result scores from entries
                log_scores = []
                for entry in log.entries:
                    if hasattr(entry, 'eval_result') and hasattr(entry.eval_result, 'result'):
                        log_scores.append(float(entry.eval_result.result))
                
                if log_scores:
                    mean_score = sum(log_scores) / len(log_scores)
                    # Use log order to determine agent type (first log = one agent, second = other)
                    if len(arxiv_scores) == 0:
                        arxiv_scores = [mean_score]  # Assume first log is ArXiv
                    else:
                        wikipedia_scores = [mean_score]  # Second log is Wikipedia
    
    # Calculate averages
    arxiv_avg = sum(arxiv_scores) / len(arxiv_scores) if arxiv_scores else 0.0
    wikipedia_avg = sum(wikipedia_scores) / len(wikipedia_scores) if wikipedia_scores else 0.0
    
    # Performance categories
    def get_performance_category(score):
        if score >= 0.9: return "Excellent"
        elif score >= 0.7: return "Good" 
        elif score >= 0.5: return "Average"
        elif score >= 0.3: return "Poor"
        else: return "Very Poor"
    
    def get_key_strength(agent_type, score):
        if agent_type == "ArXiv" and score > 0.5:
            return "Deep technical details, research-grade accuracy"
        elif agent_type == "ArXiv":
            return "Access to scientific papers (limited coverage)"
        elif agent_type == "Wikipedia" and score > 0.5:
            return "Broad context, accessible explanations"
        else:
            return "General knowledge (limited for specialized topics)"
    
    # Create clean formatted table
    print("\nAGENT COMPARISON RESULTS")
    print("=" * 80)
    
    # Table header
    print(f"{'Agent':<25} {'Knowledge Source':<25} {'Score':<15} {'Performance':<15}")
    print("-" * 80)
    
    # ArXiv agent row
    arxiv_category = get_performance_category(arxiv_avg)
    print(f"{'ArxivQueryAgent':<25} {'Scientific Papers':<25} {f'{arxiv_avg:.2f}':<15} {arxiv_category:<15}")
    
    # Wikipedia agent row  
    wiki_category = get_performance_category(wikipedia_avg)
    print(f"{'WikipediaQueryAgent':<25} {'General Knowledge':<25} {f'{wikipedia_avg:.2f}':<15} {wiki_category:<15}")
    
    print("-" * 80)
    
    # Winner determination
    if arxiv_avg > wikipedia_avg + 0.1:  # Significant difference threshold
        if wikipedia_avg > 0:
            diff_pct = int(((arxiv_avg - wikipedia_avg) / wikipedia_avg * 100))
            winner_text = f"ArXiv (+{diff_pct}%)"
        else:
            winner_text = "ArXiv (Complete Victory)"
    elif wikipedia_avg > arxiv_avg + 0.1:
        diff_pct = int(((wikipedia_avg - arxiv_avg) / arxiv_avg * 100)) if arxiv_avg > 0 else "∞"
        winner_text = f"Wikipedia (+{diff_pct}%)"
    else:
        winner_text = "Tie - Context Dependent"
    
    print(f"{'Winner: ' + winner_text:<80}")
    print("=" * 80)
    
    # Performance summary
    print(f"\nPerformance Summary:")
    print(f"  ArXiv Agent:     {arxiv_avg:.3f} ({len(arxiv_scores)} iterations)")
    print(f"  Wikipedia Agent: {wikipedia_avg:.3f} ({len(wikipedia_scores)} iterations)")
    
    if arxiv_avg > 0 and wikipedia_avg > 0:
        performance_gap = abs(arxiv_avg - wikipedia_avg)
        print(f"  Performance Gap: {performance_gap:.3f} points")
    
    # Key insights
    print(f"\nKey Insights:")
    if wikipedia_avg < 0.1:
        print("  - Wikipedia agent failed because FlashAttention is highly specialized")
        print("  - Demonstrates importance of matching knowledge source to domain")
    
    if arxiv_avg > 0.5:
        print("  - ArXiv agent succeeded with access to scientific papers")
        print("  - Technical concepts properly explained from research sources")
    
    print(f"\nNote: Results may vary due to LLM non-deterministic behavior and embedding updates.")
    print("=" * 80)


async def run_embedding_benchmark():
    """
    Run a comprehensive benchmark comparing arXiv and Wikipedia agents on FlashAttention.
    
    This benchmark evaluates how well each agent answers technical questions about 
    FlashAttention algorithms by using a specialized LLM judge to score technical 
    accuracy and completeness on a 0.0-1.0 scale.
    """
    
    if not LANGCHAIN_AVAILABLE or not TXTAI_AVAILABLE:
        raise ImportError("LangChain and txtai are required. Install with: pip install txtai langchain langchain-openai")
    
    # Test question focusing on FlashAttention technical details
    test_questions = [
        "What are the key algorithmic changes in FlashAttention 2 compared to FlashAttention, and how do they reduce memory traffic during attention, include the specific tiling strategy and complexity claims"
    ]
    
    # Create FlashAttention-specific evaluation objective using LLM judge
    response_quality_objective = LLMJudgeObjective(
        name="flashattention_technical_evaluation",
        description="Evaluates the technical accuracy and completeness of FlashAttention algorithm explanations",
        output_key="response",
        goal="Provide technically accurate, comprehensive explanations of FlashAttention algorithmic improvements and memory optimization techniques",
        prompt="""
        You are an expert in attention mechanisms and memory-efficient deep learning algorithms. Your task is to evaluate the technical accuracy and completeness of responses about FlashAttention.
        
        Question: {expected_output}
        Agent Response: {input}
        
        Evaluate the response specifically on FlashAttention technical details using these criteria:
        
        1. **Algorithmic Accuracy** (30%): Does the response correctly explain the key algorithmic differences between FlashAttention and FlashAttention-2? Are the technical details accurate?
        
        2. **Memory Optimization Understanding** (25%): Does the response demonstrate understanding of how FlashAttention reduces memory traffic during attention computation? Are the memory complexity improvements explained correctly?
        
        3. **Tiling Strategy Explanation** (20%): Does the response accurately describe the specific tiling strategies used in FlashAttention? Are the block-wise computation details correct?
        
        4. **Complexity Claims** (15%): Does the response include accurate complexity claims (time/memory) for FlashAttention vs standard attention? Are the O-notation claims correct?
        
        5. **Technical Depth** (10%): Does the response show deep understanding of the underlying computational optimizations and hardware considerations?
        
        Expected key technical points for a complete answer:
        - FlashAttention-2: Improved parallelization across sequence length dimension
        - Reduced memory reads/writes through block-wise computation
        - Tiling strategy that keeps intermediate results in SRAM
        - Linear memory complexity O(N) vs quadratic O(N²) for standard attention
        - Forward and backward pass optimizations
        - Hardware-aware algorithm design considerations
        
        Score the response from 0.0 to 1.0:
        - 0.0-0.2: Very poor (major technical inaccuracies, missing core concepts)
        - 0.3-0.4: Poor (some correct points but significant gaps or errors)
        - 0.5-0.6: Average (generally correct but missing important technical details)
        - 0.7-0.8: Good (accurate technical content with most key points covered)
        - 0.9-1.0: Excellent (comprehensive, technically precise, includes all key algorithmic details)
        
        {format_instructions}
        """,
        valid_eval_result_type=FloatEvalResult
    )
    
    # Create benchmarks for both agents
    arxiv_benchmarks = []
    wikipedia_benchmarks = []
    
    for i, question in enumerate(test_questions, 1):
        # ArXiv agent benchmark
        arxiv_benchmarks.append(
            Benchmark(
                name=f"ArXiv Agent - FlashAttention Query {i}",
                input_kwargs={"query": question},
                objective=response_quality_objective,
                iterations=4,  # Run FlashAttention question multiple times for consistency
                verbose=True,
                invoke_method="invoke"
            )
        )
        
        # Wikipedia agent benchmark
        wikipedia_benchmarks.append(
            Benchmark(
                name=f"Wikipedia Agent - FlashAttention Query {i}",
                input_kwargs={"query": question},
                objective=response_quality_objective,
                iterations=4,  # Run FlashAttention question multiple times for consistency
                verbose=True,
                invoke_method="invoke"
            )
        )
    
    # Create a shared logger for both benchmarkers to enable unified logging and comparison
    shared_logger = BenchmarkLogger(
        metadata={
            "experiment_name": "FlashAttention Knowledge Comparison",
            "agents_compared": ["ArxivQueryAgent", "WikipediaQueryAgent"],
            "test_question": "FlashAttention algorithmic improvements and memory optimization",
            "iterations_per_agent": sum(b.iterations for b in arxiv_benchmarks),
            "evaluation_type": "FlashAttention Technical LLM Judge (Float 0.0-1.0)"
        }
    )
    
    # Create the first benchmarker for ArXiv agent
    arxiv_benchmarker = OmniBarmarker(
        executor_fn=create_arxiv_agent,
        executor_kwargs={},
        initial_input=arxiv_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True
    )
    
    # Create the second benchmarker for Wikipedia agent
    wikipedia_benchmarker = OmniBarmarker(
        executor_fn=create_wikipedia_agent,
        executor_kwargs={},
        initial_input=wikipedia_benchmarks,
        enable_logging=True,
        auto_assign_evaluators=True
    )
    
    # Assign the shared logger to both benchmarkers for unified logging
    arxiv_benchmarker._logger = shared_logger
    wikipedia_benchmarker._logger = shared_logger
    
    # Run both benchmarks concurrently - let OmniBAR handle the logging
    print("🚀 Starting benchmarks (OmniBAR will handle all logging)...")
    
    arxiv_task = arxiv_benchmarker.benchmark_async(max_concurrent=2)
    wikipedia_task = wikipedia_benchmarker.benchmark_async(max_concurrent=2)
    
    # Wait for both to complete
    arxiv_results, wikipedia_results = await asyncio.gather(arxiv_task, wikipedia_task)
    
    # Use the built-in OmniBAR logging system exclusively
    print("\n" + "🚀 BENCHMARK COMPLETED - Using Built-in OmniBAR Logging")
    print("=" * 80)
    
    # Overall summary using built-in logger
    shared_logger.print_summary()
    
    # Detailed results using built-in pretty print
    print("\n📊 ArXiv Agent Performance:")
    shared_logger.pretty_print(
        detail_level="full",
        include_evaluations=True
    )
    
    print("\n📊 Wikipedia Agent Performance:")
    shared_logger.pretty_print(
        detail_level="full",
        include_evaluations=True
    )
    
    # Generate and display comparison table with real results
    print("\n📊 AGENT COMPARISON TABLE")
    print("=" * 80)
    create_agent_comparison_table(shared_logger)
    
    # Export results using built-in functionality
    print("\n💾 Exporting results using built-in logger functionality...")
    try:
        unified_json = shared_logger.to_json(include_evaluations=True)
        export_path = Path(__file__).parent / "embedding_benchmark_results.json"
        with open(export_path, 'w') as f:
            f.write(unified_json)
        print(f"✅ Results exported to: {export_path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
    
    return {
        "arxiv_results": arxiv_results,
        "wikipedia_results": wikipedia_results,
        "shared_logger": shared_logger  # Return the logger for further analysis
    }


def main():
    """Main function to run the embedding benchmark comparison."""
    
    if not LANGCHAIN_AVAILABLE or not TXTAI_AVAILABLE:
        raise ImportError("Missing dependencies! Install with: pip install txtai langchain langchain-openai")
    
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY environment variable not set! Please set your OpenAI API key to run the LLM judge evaluation")
    
    # Run the async benchmark - let OmniBAR handle all logging and errors
    results = asyncio.run(run_embedding_benchmark())
    return results


if __name__ == "__main__":
    main()
