#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Boolean vs Float Results Example
===============================

REAL-WORLD SCENARIO: You need to test a knowledge quiz agent and want to understand
when to use pass/fail testing vs scored evaluation.

This example demonstrates the difference between BoolEvalResult and FloatEvalResult
in OmniBAR evaluation objectives, helping you choose the right result type for your needs.

Key Concepts:
- BoolEvalResult: Pass/Fail (True/False) evaluation
- FloatEvalResult: Scored evaluation (0.0 to 1.0) with LLM Judge
- When to use each result type
- How result types affect logging and analysis

Perfect for understanding:
- Evaluation result types in OmniBAR
- Binary vs scored assessment
- Choosing appropriate evaluation methods

LEARNING VALUE:
✅ Understand when to use boolean vs float evaluation
✅ See practical examples of both approaches
✅ Learn how result types affect analysis and reporting

Usage:
    python basic/bool_vs_float_results.py
"""

# No environment variables needed for this example!
# This example uses only local evaluations - no external APIs required.

from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import StringEqualityObjective, RegexMatchObjective, CombinedBenchmarkObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult


class QuizAgent:
    """
    A simple quiz-answering agent for demonstrating different result types.
    
    This agent answers basic questions with varying levels of correctness,
    making it perfect for showing the difference between boolean (pass/fail)
    and float (scored) evaluation approaches.
    """
    
    def __init__(self):
        """Initialize with knowledge base."""
        self.knowledge = {
            "capital_france": "Paris",
            "largest_planet": "Jupiter", 
            "python_creator": "Guido van Rossum",
            "squares": {2: 4, 3: 9, 4: 16, 5: 25}
        }
    
    def invoke(self, question_type: str, **kwargs) -> dict:
        """Answer different types of questions with varying accuracy."""
        
        if question_type == "capital":
            country = kwargs.get("country", "").lower()
            if country == "france":
                return {
                    "answer": "Paris",
                    "confidence": "high",
                    "explanation": "Paris is the capital and largest city of France"
                }
        
        elif question_type == "planet":
            return {
                "answer": "Jupiter",
                "confidence": "high", 
                "explanation": "Jupiter is the largest planet in our solar system"
            }
        
        elif question_type == "python":
            return {
                "answer": "Guido van Rossum",
                "confidence": "medium",
                "explanation": "The creator of Python programming language"
            }
        
        elif question_type == "math":
            number = kwargs.get("number", 0)
            if number in self.knowledge["squares"]:
                correct_answer = self.knowledge["squares"][number]
                # Simulate sometimes giving close but wrong answers
                if number == 4:  # Deliberately wrong for demonstration
                    return {
                        "answer": "15",  # Wrong! Should be 16
                        "confidence": "medium",
                        "explanation": f"I think {number} squared is 15"
                    }
                else:
                    return {
                        "answer": str(correct_answer),
                        "confidence": "high",
                        "explanation": f"{number} squared equals {correct_answer}"
                    }
        
        # Default fallback
        return {
            "answer": "I don't know",
            "confidence": "none",
            "explanation": "This question is outside my knowledge base"
        }


def create_quiz_agent():
    """Factory function for the quiz agent."""
    return QuizAgent()


def main():
    """Demonstrate the difference between BoolEvalResult and FloatEvalResult."""
    
    print("🎯 Boolean vs Float Results Example")
    print("=" * 50)
    
    # =============================================================================
    # Example 1: BoolEvalResult - Pass/Fail Evaluation
    # =============================================================================
    print("\n📋 Example 1: BoolEvalResult (Pass/Fail)")
    print("-" * 37)
    print("BoolEvalResult gives binary True/False results - either correct or not.")
    
    # Create boolean objectives that return True/False
    bool_france_objective = StringEqualityObjective(
        name="france_capital_bool",
        output_key="answer",
        goal="Paris",
        valid_eval_result_type=BoolEvalResult  # Returns True/False
    )
    
    bool_math_objective = StringEqualityObjective(
        name="math_answer_bool", 
        output_key="answer",
        goal="16",  # 4 squared = 16, but our agent will say 15
        valid_eval_result_type=BoolEvalResult
    )
    
    # Combine boolean objectives
    bool_combined = CombinedBenchmarkObjective(
        name="boolean_quiz_evaluation",
        objectives=[bool_france_objective, bool_math_objective]
    )
    
    # Create benchmarks
    bool_benchmarks = [
        Benchmark(
            name="France Capital (Boolean)",
            input_kwargs={"question_type": "capital", "country": "france"},
            objective=bool_france_objective,
            iterations=1
        ),
        Benchmark(
            name="Math Question (Boolean)",
            input_kwargs={"question_type": "math", "number": 4},
            objective=bool_math_objective,
            iterations=1
        ),
        Benchmark(
            name="Combined Boolean Quiz",
            input_kwargs={"question_type": "capital", "country": "france"},  # This will pass
            objective=bool_combined,
            iterations=1
        )
    ]
    
    # Run boolean evaluation
    bool_benchmarker = OmniBarmarker(
        executor_fn=create_quiz_agent,
        executor_kwargs={},
        initial_input=bool_benchmarks
    )
    
    results = bool_benchmarker.benchmark()
    bool_benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 2: FloatEvalResult - Scored Evaluation (Simulated)
    # =============================================================================
    print("\n📋 Example 2: FloatEvalResult (Scored 0.0-1.0)")
    print("-" * 42)
    print("FloatEvalResult gives scored results from 0.0 (worst) to 1.0 (best).")
    print("Note: For this demo, we'll use RegexMatchObjective which can provide partial scoring.")
    
    # Create objectives that can provide graduated scoring
    # RegexMatchObjective with partial matching can give float-like behavior
    confidence_pattern_objective = RegexMatchObjective(
        name="confidence_pattern_float",
        output_key="confidence",
        goal=r"(high|medium|low)",  # Matches different confidence levels
        valid_eval_result_type=BoolEvalResult  # Still bool, but demonstrates concept
    )
    
    explanation_quality_objective = RegexMatchObjective(
        name="explanation_quality_float", 
        output_key="explanation",
        goal=r".{10,}",  # At least 10 characters in explanation
        valid_eval_result_type=BoolEvalResult
    )
    
    # Note: True FloatEvalResult is typically used with LLMJudgeObjective
    # which requires API keys. This example shows the concept with bool objectives.
    
    float_combined = CombinedBenchmarkObjective(
        name="quality_assessment",
        objectives=[confidence_pattern_objective, explanation_quality_objective]
    )
    
    # Create benchmarks for different scenarios
    float_benchmarks = [
        Benchmark(
            name="High Confidence Answer",
            input_kwargs={"question_type": "planet"},  # Should give high confidence
            objective=float_combined,
            iterations=1
        ),
        Benchmark(
            name="Unknown Question", 
            input_kwargs={"question_type": "unknown"},  # Should give low confidence
            objective=float_combined,
            iterations=1
        )
    ]
    
    # Run scored evaluation
    float_benchmarker = OmniBarmarker(
        executor_fn=create_quiz_agent,
        executor_kwargs={},
        initial_input=float_benchmarks
    )
    
    results = float_benchmarker.benchmark()
    float_benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 3: Comparison and Use Cases
    # =============================================================================
    print("\n📋 Example 3: When to Use Each Result Type")
    print("-" * 44)
    
    print("🔵 BoolEvalResult (True/False) - Best for:")
    print("   • Pass/fail testing")
    print("   • Exact requirement validation") 
    print("   • Binary decision making")
    print("   • Simple correctness checks")
    print("   • Unit test-style evaluation")
    
    print("\n🟡 FloatEvalResult (0.0-1.0) - Best for:")
    print("   • Quality assessment")
    print("   • Partial credit evaluation")
    print("   • Graduated scoring")
    print("   • AI-judged responses (with LLMJudgeObjective)")
    print("   • Performance benchmarking with nuanced results")
    
    print("\n📊 Result Analysis:")
    print("   • Boolean results are aggregated as pass rates")
    print("   • Float results can be averaged for overall scores")
    print("   • Combined objectives can mix both types")
    print("   • Choose based on your evaluation needs")
    
    print("\n" + "=" * 50)
    print("✅ Result Types Example Complete!")
    print("\n🎓 Key Learnings:")
    print("   • BoolEvalResult for binary pass/fail evaluation")
    print("   • FloatEvalResult for scored 0.0-1.0 assessment") 
    print("   • Choose result type based on evaluation goals")
    print("   • Both types can be combined in CombinedBenchmarkObjective")
    print("   • Result type affects how data is analyzed and reported")


if __name__ == "__main__":
    main()
