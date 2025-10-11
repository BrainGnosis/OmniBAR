#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Document Extraction Prompt Engineering Evolution
==============================================

REAL-WORLD SCENARIO: You need to extract structured data from research papers
and must iteratively improve your prompts to get better results. This shows
the realistic journey of prompt engineering refinement.

This example demonstrates:
- Realistic prompt engineering evolution (4 iterations)
- Document extraction task complexity
- Measurable quality improvements through better prompting
- Real-world AI document processing scenario

Perfect for understanding:
- How prompts evolve through real-world iteration cycles
- Document extraction challenges and solutions
- Quality differences between prompt engineering approaches
- Practical prompt optimization for complex tasks

LEARNING VALUE:
✅ See realistic prompt engineering journey from naive to expert
✅ Understand how prompt quality dramatically affects extraction results
✅ Learn systematic approaches to complex document processing
✅ Data-driven prompt optimization for real business scenarios

Usage:
    python document_extraction_evolution.py
"""

import asyncio
from pathlib import Path


# Load environment variables for real AI agent API calls
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
        custom_env = os.getenv("OMNIBAR_ENV_PATH")
        if custom_env:
            custom_path = Path(custom_env)
            if custom_path.exists():
                load_dotenv(custom_path)
                print(f"✅ Loaded environment variables from {custom_path}")
                return

        # Option 2-4: Check standard locations
        potential_env_paths = [
            Path(".env"),  # Current directory
            Path("../.env"),  # Parent directory
            Path("../../.env"),  # Project root
        ]

        for env_path in potential_env_paths:
            if env_path.exists():
                load_dotenv(env_path.resolve())
                print(f"✅ Loaded environment variables from {env_path.resolve()}")
                return

        print("⚠️ No .env file found, using system environment variables")

    except ImportError:
        print("⚠️ python-dotenv not installed, using system environment variables")


# Load environment variables
load_environment_variables()

from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import RegexMatchObjective, LLMJudgeObjective, CombinedBenchmarkObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult
import random


class ResearchPaperExtractionAgent:
    """
    An AI agent that extracts structured data from research papers using different prompt strategies.

    This demonstrates the realistic evolution of prompt engineering:
    - Iteration 1: Naive first attempt (generic extraction)
    - Iteration 2: More structured after learning what's needed
    - Iteration 3: JSON output format after realizing structure matters
    - Iteration 4: Expert-level comprehensive extraction system
    """

    def __init__(self, prompt_iteration="iteration_1"):
        """Initialize agent with specified prompt iteration."""
        self.prompt_iteration = prompt_iteration

        # Realistic prompt engineering evolution
        self.prompts = {
            "iteration_1": "Extract information from this research paper.",
            "iteration_2": """Extract from this research paper:
                            - Title and authors
                            - Key findings  
                            - Important statistics or metrics
                            - Main conclusions""",
            "iteration_3": """Extract research data as JSON:
                        {
                            "title": "...",
                            "authors": [...],
                            "key_findings": [...],
                            "statistics": [...],
                            "methodology": "...",
                            "conclusions": [...]
                        }""",
            "iteration_4": """You are an expert research analyst. Extract comprehensive data from this academic paper with 100% accuracy.

                        EXTRACTION FRAMEWORK:
                        1. Bibliographic: Title, authors, publication details
                        2. Research Scope: Problem statement, objectives, hypotheses  
                        3. Methodology: Experimental design, datasets, evaluation metrics
                        4. Results: Key findings, statistical significance, performance numbers
                        5. Analysis: Insights, implications, limitations, future work

                        OUTPUT: Valid JSON with nested structure
                        VALIDATION: Cross-reference claims with evidence in text
                        QUALITY: Academic-grade precision and completeness
                        ERROR HANDLING: Use null for missing information, never hallucinate data""",
        }

    def invoke(self, paper_content: str, **kwargs) -> dict:
        """
        Extract structured data from research paper using the configured prompt iteration.

        Shows how different prompt engineering approaches affect extraction quality.
        """

        try:
            # Real API call to GPT-4 with the configured prompt iteration
            extraction = self._call_openai_api(paper_content, self.prompt_iteration)

            return {
                "extraction": extraction,
                "prompt_iteration": self.prompt_iteration,
                "paper_length": len(paper_content),
                "extraction_length": len(extraction),
                "status": "success",
            }

        except Exception as e:
            return {
                "extraction": "",
                "prompt_iteration": self.prompt_iteration,
                "error": str(e),
                "status": "failed",
            }

    def _call_openai_api(self, paper_content: str, iteration: str) -> str:
        """
        Call OpenAI API with different prompt iterations.

        Uses GPT-4 for better document extraction capabilities.
        """

        try:
            from openai import OpenAI
            import os

            # Get API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY not found!")

            client = OpenAI(api_key=api_key)

            # Get the appropriate prompt for this iteration
            prompt = self.prompts.get(iteration, self.prompts["iteration_1"])

            # Real API call to GPT-4 (better for document extraction)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": paper_content},
                ],
                temperature=0.1,  # Very low temperature for extraction accuracy
                max_tokens=800
                if iteration == "iteration_4"
                else 400,  # More tokens for expert extraction
            )

            return response.choices[0].message.content.strip()

        except ImportError:
            return "Error: OpenAI package not installed. Run: pip install openai"
        except Exception as e:
            return f"Error calling OpenAI API: {str(e)[:100]}..."


def create_iteration_1_agent():
    """Factory for iteration 1 (naive) prompt."""
    return ResearchPaperExtractionAgent("iteration_1")


def create_iteration_2_agent():
    """Factory for iteration 2 (structured) prompt."""
    return ResearchPaperExtractionAgent("iteration_2")


def create_iteration_3_agent():
    """Factory for iteration 3 (JSON format) prompt."""
    return ResearchPaperExtractionAgent("iteration_3")


def create_iteration_4_agent():
    """Factory for iteration 4 (expert-level) prompt."""
    return ResearchPaperExtractionAgent("iteration_4")


async def test_document_extraction_evolution():
    """
    Document extraction prompt engineering evolution demonstration.

    Tests 4 realistic prompt iterations:
    1. Naive first attempt (generic)
    2. Structured approach (specific fields)
    3. JSON format (structured output)
    4. Expert-level system (comprehensive extraction)
    """

    print("🔬 Document Extraction Prompt Engineering Evolution")
    print("=" * 55)
    print(
        "\n📋 SCENARIO: Extract structured data from OpenAI's hallucination research paper"
    )
    print(
        "🎯 GOAL: Show how prompt engineering iterations dramatically improve extraction quality"
    )
    print("📊 METHOD: Real GPT-4 extraction with 4 prompt evolution stages\n")

    # Simulated content from "Why Language Models Hallucinate" research paper
    research_paper_content = """
    Why Language Models Hallucinate and How to Mitigate It
    Authors: Sarah Chen, Michael Rodriguez, Dr. Amanda Kim
    OpenAI Research, 2024

    Abstract: This paper investigates the phenomenon of hallucination in large language models (LLMs), 
    where models generate plausible but factually incorrect information. We analyze 1,247 model outputs 
    across 15 different tasks and identify three primary causes of hallucination: training data inconsistencies, 
    attention mechanism limitations, and overconfident prediction patterns.

    Key Findings:
    - Hallucination rates vary significantly by task type: 12% for factual QA, 28% for creative writing, 45% for technical specifications
    - Models show 67% higher hallucination rates when generating content about events after their training cutoff
    - Temperature settings above 0.7 correlate with 34% increased hallucination frequency
    - Fine-tuning on domain-specific data reduces hallucination by an average of 23%

    Methodology: We evaluated GPT-4, Claude-3, and LLaMA-2 across standardized benchmarks including TruthfulQA, 
    HaluEval, and a custom technical accuracy dataset. Each model processed 415 prompts with systematic 
    fact-checking against verified sources.

    Results: Our proposed mitigation techniques - including confidence scoring, retrieval augmentation, 
    and multi-step verification - reduced hallucination rates by 41% on average while maintaining 
    response quality scores above 0.85.

    Limitations: This study focused primarily on English-language models and may not generalize to 
    multilingual contexts. Additionally, our fact-checking methodology may have missed subtle 
    inaccuracies in highly technical domains.

    Future Work: We plan to expand this research to include multimodal models and investigate 
    hallucination patterns in code generation tasks.
    """

    prompt_iterations = [
        {"name": "Iteration 1: Naive Attempt", "factory": create_iteration_1_agent},
        {"name": "Iteration 2: Structured Fields", "factory": create_iteration_2_agent},
        {"name": "Iteration 3: JSON Format", "factory": create_iteration_3_agent},
        {"name": "Iteration 4: Expert System", "factory": create_iteration_4_agent},
    ]

    print("🧪 TEST: Data Extraction Quality Assessment")
    print("-" * 50)
    print("Testing extraction completeness and accuracy across prompt iterations...")

    # Test extraction completeness - Do extractions contain key research elements?
    results = {}

    for iteration in prompt_iterations:
        print(f"\n📝 Testing: {iteration['name']}")

        # 1. Content Quality Score (0.0-1.0)
        content_quality_objective = LLMJudgeObjective(
            name="content_quality",
            description="Evaluate how well the extraction captures essential research paper information",
            goal="High-quality research paper extraction should capture key information including title, authors, abstract, methodology, findings, and conclusions with accuracy and completeness.",
            output_key="extraction",
            valid_eval_result_type=FloatEvalResult
        )
        
        # 2. Structure Quality Score (0.0-1.0) 
        structure_objective = LLMJudgeObjective(
            name="structure_quality",
            description="Evaluate organization and formatting quality of the extracted information",
            goal="Well-structured extraction should be clearly organized with proper formatting, logical flow, and easy readability. JSON format gets higher scores than narrative text.",
            output_key="extraction",
            valid_eval_result_type=FloatEvalResult
        )
        
        # 3. Completeness Score (0.0-1.0)
        completeness_objective = LLMJudgeObjective(
            name="completeness",
            description="Evaluate comprehensiveness of information extraction",
            goal="Complete extraction should include all major sections: title, authors, abstract, key findings, methodology, results, limitations, and future work from the research paper.",
            output_key="extraction", 
            valid_eval_result_type=FloatEvalResult
        )
        
        # 4. Technical Accuracy Score (0.0-1.0)
        accuracy_objective = LLMJudgeObjective(
            name="technical_accuracy",
            description="Evaluate factual accuracy and precision of extracted information",
            goal="Accurate extraction should contain precise facts, correct terminology, proper citations, and avoid hallucinated or incorrect information about the research paper.",
            output_key="extraction",
            valid_eval_result_type=FloatEvalResult
        )
        
        # Combine all scoring objectives
        combined_objective = CombinedBenchmarkObjective(
            name=f"comprehensive_extraction_evaluation_{iteration['name'].lower().replace(' ', '_')}",
            description="Multi-dimensional evaluation of document extraction quality",
            objectives=[content_quality_objective, structure_objective, completeness_objective, accuracy_objective]
        )

        benchmark = Benchmark(
            name=f"{iteration['name']} - Research Paper Extraction",
            input_kwargs={"paper_content": research_paper_content},
            objective=combined_objective,
            iterations=2,
        )

        benchmarker = OmniBarmarker(
            executor_fn=iteration["factory"],
            executor_kwargs={},
            initial_input=[benchmark],
            enable_logging=True,
        )

        benchmark_results = await benchmarker.benchmark_async()
        results[iteration["name"]] = benchmarker.logger

        print(f"📊 {iteration['name']} Results:")
        benchmarker.print_logger_summary()

    # Display comparison results
    print("\n" + "=" * 80)
    print("📊 PROMPT ENGINEERING EVOLUTION COMPARISON")
    print("=" * 80)

    print("\n🏆 RESULTS SUMMARY:")
    print("-" * 40)

    all_scores = {}  # Store scores for final table

    for iteration_name, logger in results.items():
        # Extract real numerical scores and lengths from actual LLM judge results
        scores = {
            "content_quality": [],
            "structure_quality": [],  
            "completeness": [],
            "technical_accuracy": []
        }
        extraction_lengths = []
        
        # Map objective names to score categories 
        objective_names_to_categories = {
            "content_quality": "content_quality",
            "structure_quality": "structure_quality",
            "completeness": "completeness", 
            "technical_accuracy": "technical_accuracy"
        }
        
        # Collect real scores and lengths from benchmark results
        for log in logger:
            for entry in log.entries:
                # Extract real numerical scores from LLM judge results
                if hasattr(entry, 'eval_result') and hasattr(entry.eval_result, 'result') and entry.eval_result.result is not None:
                    try:
                        score = float(entry.eval_result.result)
                        
                        # Assign score to appropriate category based on objective in the log
                        # Since we have 4 objectives per iteration, distribute them cyclically
                        obj_index = len([s for s in scores.values() for s in s]) % 4
                        score_categories = list(scores.keys())
                        category = score_categories[obj_index]
                        scores[category].append(score)
                    except (ValueError, TypeError):
                        # Skip invalid scores
                        continue
                
                # Extract real extraction lengths from multiple possible locations
                length_found = False
                
                # Method 1: Check evaluated_output
                if hasattr(entry, 'evaluated_output') and entry.evaluated_output and not length_found:
                    if isinstance(entry.evaluated_output, dict) and 'extraction' in entry.evaluated_output:
                        extraction = str(entry.evaluated_output['extraction'])
                        extraction_lengths.append(len(extraction))
                        length_found = True
                    elif isinstance(entry.evaluated_output, str):
                        extraction_lengths.append(len(entry.evaluated_output))
                        length_found = True
                
                # Method 2: Check if there's a different output field 
                if not length_found and hasattr(entry, 'metadata') and entry.metadata:
                    if isinstance(entry.metadata, dict) and 'output' in entry.metadata:
                        output = entry.metadata['output']
                        if isinstance(output, dict) and 'extraction' in output:
                            extraction = str(output['extraction'])
                            extraction_lengths.append(len(extraction))
                            length_found = True
        
        # Calculate average scores across all dimensions
        avg_scores = {}
        for dimension, score_list in scores.items():
            avg_scores[dimension] = sum(score_list) / len(score_list) if score_list else 0.0
        
        overall_score = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0.0
        avg_length = sum(extraction_lengths) / len(extraction_lengths) if extraction_lengths else 0
        
        # Store for final table
        all_scores[iteration_name] = {
            **avg_scores,
            "overall_score": overall_score,
            "avg_length": avg_length
        }
        
        print(f"📊 {iteration_name}:")
        print(f"   🎯 Content Quality: {avg_scores.get('content_quality', 0):.2f}")
        print(f"   🏗️  Structure Quality: {avg_scores.get('structure_quality', 0):.2f}") 
        print(f"   📋 Completeness: {avg_scores.get('completeness', 0):.2f}")
        print(f"   ✅ Technical Accuracy: {avg_scores.get('technical_accuracy', 0):.2f}")
        print(f"   🏆 Overall Score: {overall_score:.2f}")
        print(f"   📏 Avg Length: {int(avg_length)} characters")
        print()

    # Display final numerical comparison table
    print("\n" + "=" * 90)
    print("📈 QUANTITATIVE COMPARISON TABLE")
    print("=" * 90)
    print(f"{'Iteration':<25} {'Content':<8} {'Structure':<9} {'Complete':<9} {'Accuracy':<9} {'Overall':<8} {'Length':<8}")
    print("-" * 90)
    
    for iteration_name, metrics in all_scores.items():
        print(f"{iteration_name:<25} {metrics.get('content_quality', 0):<8.2f} {metrics.get('structure_quality', 0):<9.2f} {metrics.get('completeness', 0):<9.2f} {metrics.get('technical_accuracy', 0):<9.2f} {metrics.get('overall_score', 0):<8.2f} {int(metrics.get('avg_length', 0)):<8}")
    
    print("\n💡 SCORING INSIGHTS:")
    print("  • Each dimension scored 0.0-1.0 by GPT-4 LLM judge")
    print("  • Higher scores = better prompt engineering quality") 
    print("  • Clear quantitative progression should be visible")
    print("  • Expert iteration should score highest overall")
    
    # Store scores for documentation update
    globals()['final_scores'] = all_scores

    return results


def main():
    """Main function demonstrating document extraction prompt evolution."""

    print("🎯 REAL-WORLD SCENARIO: Document Extraction Optimization")
    print("=" * 55)
    print("You need to extract structured data from research papers and must")
    print("iteratively improve your prompts. Which engineering approach works best?")
    print("Instead of guessing, let's systematically improve through iteration!")
    print()
    print("💡 ITERATIVE PROMPT ENGINEERING:")
    print("   1. Start with naive approach (generic prompt)")
    print("   2. Add structure (specific fields)")
    print("   3. Enforce format (JSON output)")
    print("   4. Expert-level system (comprehensive extraction)")
    print()

    # Run comprehensive document extraction testing
    results = asyncio.run(test_document_extraction_evolution())

    print("\n🏆 CONGRATULATIONS!")
    print("You now understand how prompt engineering evolution")
    print("dramatically improves document extraction quality!")

    return results


if __name__ == "__main__":
    main()
