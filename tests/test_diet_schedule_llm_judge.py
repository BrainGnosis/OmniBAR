#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Comprehensive test of OmniBarmarker with LangChain agents and LLM-as-a-judge objectives.
Tests diet schedule generation with OpenAI and Anthropic models, using LLM judges for evaluation.

This test demonstrates:
1. Loading environment variables from .env file
2. Creating LangChain agents with different LLM providers (OpenAI, Anthropic)
3. Using ONLY LLMJudgeObjective for all evaluation criteria (no simple string checks)
4. Combined objectives with multiple LLM judges for comprehensive evaluation
5. Auto-evaluator assignment with comprehensive logging
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    # Get the root directory of OmniBAR (parent of tests/)
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        print("Please ensure API keys are set in environment variables")
except ImportError:
    print("❌ python-dotenv not available. Install with: pip install python-dotenv")
    sys.exit(1)

# Check for required API keys
required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
missing_keys = []
for key in required_keys:
    if not os.getenv(key):
        missing_keys.append(key)

if missing_keys:
    print(f"❌ Missing required API keys: {missing_keys}")
    print("Please set these in your .env file")
    sys.exit(1)

print("✅ All required API keys found")

# Import required libraries
try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.output_parsers import JsonOutputParser
    from langchain.agents import create_openai_functions_agent, create_structured_chat_agent, AgentExecutor, tool
    print("✅ LangChain imports successful")
except ImportError as e:
    print(f"❌ LangChain import error: {e}")
    print("Install with: pip install langchain langchain-openai langchain-anthropic")
    sys.exit(1)

# Import our benchmarking components
from omnibar.core.benchmarker import OmniBarmarker, Benchmark
from omnibar.objectives.combined import CombinedBenchmarkObjective
from omnibar.objectives.llm_judge import (
    LLMJudgeObjective, 
    LLMBinaryOutputSchema
)
# Removed StringEqualityObjective - using only LLM judges
from omnibar.core.types import BoolEvalResult


# Create a simple diet schedule generation tool
@tool
def generate_diet_schedule(query: str) -> str:
    """
    Generate a detailed 1-day fruit-based diet schedule based on requirements.
    
    Args:
        query: The specific requirements for the diet schedule
        
    Returns:
        A detailed, structured diet plan
    """
    # This tool will be used by the agent, so it doesn't need LLM logic
    # The agent's LLM will handle the actual generation
    return f"""
    Create a detailed 1-day fruit-based diet schedule with the following requirements:
    - {query}
    - Focus on fruits with low sugar content
    - Include meal timing and portion sizes
    - Provide nutritional guidance
    - Ensure balanced nutrition throughout the day
    
    Please provide a comprehensive daily schedule that includes:
    1. Breakfast with timing and portions
    2. Mid-morning snack
    3. Lunch with timing and portions  
    4. Afternoon snack
    5. Dinner with timing and portions
    6. Evening snack (if appropriate)
    
    Also include:
    - Total estimated sugar content for the day
    - Key nutritional benefits
    - Any important notes or warnings
    
    Format your response as a detailed, structured plan.
    """


def create_openai_agent():
    """Create an OpenAI-based diet schedule agent using built-in LangChain patterns."""
    # Create LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create tools
    tools = [generate_diet_schedule]
    
    # Create prompt template for OpenAI functions agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional nutritionist specializing in fruit-based diets. "
                  "Use the diet schedule generation tool to create comprehensive, healthy meal plans. "
                  "Always provide detailed, practical advice with specific portions and timing."),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent using built-in OpenAI functions pattern
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        input_keys=["input"]  # Explicitly set input keys to fix LangChain compatibility
    )
    
    return agent_executor


def create_anthropic_agent():
    """Create an Anthropic-based diet schedule agent using built-in LangChain patterns."""
    # Create LLM
    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create tools
    tools = [generate_diet_schedule]
    
    # Create prompt template for structured chat agent (works better with Anthropic)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional nutritionist specializing in fruit-based diets. "
                  "Use the available tools to create comprehensive, healthy meal plans. "
                  "Always provide detailed, practical advice with specific portions and timing.\n\n"
                  "You have access to the following tools:\n{tools}\n\n"
                  "Use a json blob to specify a tool by providing an action key (tool name) "
                  "and an action_input key (tool input).\n\n"
                  "Valid \"action\" values: \"Final Answer\" or {tool_names}\n\n"
                  "For the generate_diet_schedule tool, use this format:\n\n"
                  "```\n{{\n  \"action\": \"generate_diet_schedule\",\n  \"action_input\": {{\"query\": \"your diet requirements here\"}}\n}}\n```\n\n"
                  "Follow this format:\n\n"
                  "Question: input question to answer\n"
                  "Thought: consider previous and subsequent steps\n"
                  "Action:\n```\n$JSON_BLOB\n```\n"
                  "Observation: action result\n"
                  "... (repeat Thought/Action/Observation as needed)\n"
                  "Thought: I now know the final answer\n"
                  "Action:\n```\n{{\n  \"action\": \"Final Answer\",\n  \"action_input\": \"Final response to human\"\n}}\n```"),
        ("human", "{input}\n\n{agent_scratchpad}"),
    ])
    
    # Create agent using built-in structured chat pattern  
    agent = create_structured_chat_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        input_keys=["input"],  # Explicitly set input keys to fix LangChain compatibility
        handle_parsing_errors=True  # Handle output parsing errors for Anthropic agents
    )
    
    return agent_executor


def create_diet_quality_judge(judge_llm_provider: str = "openai") -> LLMJudgeObjective:
    """Create an LLM judge for evaluating diet schedule quality."""
    
    # Custom prompt for diet schedule evaluation
    diet_evaluation_prompt = """
    You are an expert nutritionist evaluating a fruit-based diet schedule. 
    
    Evaluate the following diet schedule based on these criteria:
    - Nutritional balance and completeness
    - Appropriate portion sizes
    - Low sugar content as requested
    - Meal timing appropriateness
    - Overall healthiness and practicality
    - Adherence to fruit-based diet requirements
    
    The diet schedule to evaluate is:
    {input}
    
    Expected quality standard:
    {expected_output}
    
    Provide your evaluation in the following format:
    {format_instructions}
    
    Consider whether this diet schedule would be safe, healthy, and effective for someone following a low-sugar fruit-based diet.
    """
    
    # Create the LLM for judging
    if judge_llm_provider.lower() == "openai":
        judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        judge_llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
    
    # Create output parser
    parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
    
    # Create prompt template
    prompt_template = PromptTemplate(
        template=diet_evaluation_prompt,
        input_variables=["input"],
        partial_variables={
            "expected_output": "A comprehensive, safe, and nutritionally balanced fruit-based diet schedule with low sugar content, appropriate portions, and clear timing",
            "format_instructions": parser.get_format_instructions()
        }
    )
    
    # Create the chain
    chain = prompt_template | judge_llm | parser
    
    return LLMJudgeObjective(
        name=f"DietQualityJudge_{judge_llm_provider}",
        goal="A comprehensive, safe, and nutritionally balanced fruit-based diet schedule with low sugar content",
        output_key="output",  # Standard LangChain AgentExecutor output key
        invoke_method=chain.invoke,
        valid_eval_result_type=BoolEvalResult
    )


def create_completeness_judge(judge_llm_provider: str = "openai") -> LLMJudgeObjective:
    """Create an LLM judge for evaluating diet schedule completeness and structure."""
    
    completeness_prompt = """
    You are evaluating a fruit-based diet schedule for completeness and structure.
    
    Evaluate the following diet schedule based on these criteria:
    - Contains all major meals (breakfast, lunch, dinner)
    - Includes appropriate snacks
    - Has clear timing information
    - Specifies portion sizes
    - Provides nutritional information
    - Is well-structured and easy to follow
    
    The diet schedule to evaluate is:
    {input}
    
    Expected standard:
    {expected_output}
    
    Format your response as:
    {format_instructions}
    
    Return true if the schedule is complete and well-structured, false if it's missing key components.
    """
    
    # Create the LLM for judging
    if judge_llm_provider.lower() == "openai":
        judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        judge_llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
    
    parser = JsonOutputParser(pydantic_object=LLMBinaryOutputSchema)
    
    prompt_template = PromptTemplate(
        template=completeness_prompt,
        input_variables=["input"],
        partial_variables={
            "expected_output": "A complete, well-structured diet schedule with all meals, timing, portions, and nutritional information",
            "format_instructions": parser.get_format_instructions()
        }
    )
    
    chain = prompt_template | judge_llm | parser
    
    return LLMJudgeObjective(
        name=f"CompletenessJudge_{judge_llm_provider}",
        goal="A complete, well-structured diet schedule with all required components",
        output_key="output",  # Standard LangChain AgentExecutor output key
        invoke_method=chain.invoke,
        valid_eval_result_type=BoolEvalResult
    )


def test_diet_schedule_benchmarking():
    """Main test function for diet schedule benchmarking with LLM judges."""
    
    print("🍎 Starting Diet Schedule Benchmarking with LLM Judges")
    print("=" * 60)
    
    # Test queries for diet schedules
    test_queries = [
        "Create a low-sugar fruit diet for a diabetic person",
        "Design a fruit-based diet for weight loss with minimal sugar",
        "Plan a fruit diet for an athlete with low glycemic index fruits"
    ]
    
    # Create objectives
    print("📋 Creating Evaluation Objectives...")
    
    # LLM judges using different models for different criteria
    quality_judge_openai = create_diet_quality_judge("openai")
    quality_judge_anthropic = create_diet_quality_judge("anthropic") 
    completeness_judge = create_completeness_judge("openai")
    
    # Combined objective with multiple LLM evaluation criteria
    combined_objective = CombinedBenchmarkObjective(
        name="ComprehensiveDietEvaluation",
        description="Multi-faceted LLM-based evaluation of diet schedule quality",
        objectives=[
            completeness_judge,         # Structure and completeness evaluation
            quality_judge_openai,       # OpenAI-based quality evaluation
            quality_judge_anthropic     # Anthropic-based quality evaluation (cross-validation)
        ]
    )
    
    print(f"   ✅ Created combined objective with {len(combined_objective.objectives)} sub-objectives")
    for i, obj in enumerate(combined_objective.objectives, 1):
        print(f"      {i}. {obj.name}")
    
    # Create benchmarks for different agent-query combinations
    print("\n📊 Creating Benchmarks...")
    benchmarks = []
    
    # OpenAI agent benchmarks
    for i, query in enumerate(test_queries, 1):
        benchmark = Benchmark(
            name=f"OpenAI_Query_{i}",
            # LangChain AgentExecutor.invoke() expects a single dict argument
            # OmniBarmarker unpacks kwargs, so we pass the dict as a single kwarg
            input_kwargs={"input": {"input": query}},
            objective=combined_objective,
            iterations=1,  # Single iteration per query for this demo
            verbose=True
        )
        benchmarks.append(benchmark)
    
    # Anthropic agent benchmarks  
    for i, query in enumerate(test_queries, 1):
        benchmark = Benchmark(
            name=f"Anthropic_Query_{i}",
            # LangChain AgentExecutor.invoke() expects a single dict argument
            # OmniBarmarker unpacks kwargs, so we pass the dict as a single kwarg
            input_kwargs={"input": {"input": query}},
            objective=combined_objective,
            iterations=1,
            verbose=True
        )
        benchmarks.append(benchmark)
    
    print(f"   ✅ Created {len(benchmarks)} benchmarks")
    print(f"      - {len(test_queries)} OpenAI agent benchmarks")
    print(f"      - {len(test_queries)} Anthropic agent benchmarks")
    
    # Create benchmarkers for each agent type
    print("\n🤖 Setting up Benchmarkers...")
    
    # OpenAI agent benchmarker
    openai_benchmarker = OmniBarmarker(
        executor_fn=create_openai_agent,
        executor_kwargs={},
        initial_input=benchmarks[:len(test_queries)],  # First half for OpenAI
        enable_logging=True,
        auto_assign_evaluators=True,
        notebook=False
    )
    
    # Anthropic agent benchmarker
    anthropic_benchmarker = OmniBarmarker(
        executor_fn=create_anthropic_agent,
        executor_kwargs={},
        initial_input=benchmarks[len(test_queries):],  # Second half for Anthropic
        enable_logging=True,
        auto_assign_evaluators=True,
        notebook=False
    )
    
    print("   ✅ Created benchmarkers for both OpenAI and Anthropic agents")
    
    # Run benchmarks
    print("\n🚀 Running Benchmarks...")
    print("=" * 40)
    
    print("\n📈 Running OpenAI Agent Benchmarks...")
    print("-" * 35)
    openai_results = openai_benchmarker.benchmark()
    print(f"OpenAI Results: {openai_results}")
    
    print("\n📈 Running Anthropic Agent Benchmarks...")
    print("-" * 38)
    anthropic_results = anthropic_benchmarker.benchmark()
    print(f"Anthropic Results: {anthropic_results}")
    
    # Use built-in analysis methods - much cleaner and more comprehensive
    print("\n📊 OpenAI Agent Results:")
    openai_benchmarker.print_logger_summary()
    
    print("\n📊 Anthropic Agent Results:")
    anthropic_benchmarker.print_logger_summary()
    
    # Detailed evaluation results using built-in methods
    print("\n🧑‍⚖️ OpenAI Agent - Detailed LLM Judge Results:")
    openai_benchmarker.print_logger_details(detail_level="full")
    
    print("\n🧑‍⚖️ Anthropic Agent - Detailed LLM Judge Results:")
    anthropic_benchmarker.print_logger_details(detail_level="full")
    
    # Simple comparison using built-in properties
    openai_rate = openai_benchmarker.success_rate
    anthropic_rate = anthropic_benchmarker.success_rate
    
    print("\n🏆 QUICK COMPARISON:")
    print(f"   OpenAI:    {openai_rate:.1f}% success rate")
    print(f"   Anthropic: {anthropic_rate:.1f}% success rate")
    
    if openai_rate > anthropic_rate:
        print(f"   🏅 Winner: OpenAI (+{openai_rate - anthropic_rate:.1f} points)")
    elif anthropic_rate > openai_rate:
        print(f"   🏅 Winner: Anthropic (+{anthropic_rate - openai_rate:.1f} points)")
    else:
        print("   🤝 Result: Tie")
    
    return openai_benchmarker, anthropic_benchmarker


def main():
    """Main function to run the comprehensive diet schedule benchmarking test."""
    
    print("🚀 Diet Schedule LLM Benchmarking Test Suite")
    print("=" * 70)
    print()
    print("This test demonstrates:")
    print("  • LangChain agents with OpenAI and Anthropic models")
    print("  • LLM-as-a-judge evaluation with multiple judges")  
    print("  • Combined objectives with different evaluation criteria")
    print("  • Auto-evaluator assignment and comprehensive logging")
    print("  • Cross-model performance comparison")
    print()
    
    try:
        openai_benchmarker, anthropic_benchmarker = test_diet_schedule_benchmarking()
        
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ All components working correctly:")
        print("   • Environment loading")
        print("   • LangChain agent creation")
        print("   • LLM judge objectives")
        print("   • Combined objectives")
        print("   • Auto-evaluator assignment")
        print("   • Comprehensive logging")
        print("   • Cross-model comparison")
        
        # Final detailed view option using built-in methods
        print("\n📋 Additional Analysis Methods Available:")
        print("   • benchmarker.print_logger_summary() - Quick statistics overview")
        print("   • benchmarker.print_logger_details(detail_level='full') - Complete results")
        print("   • benchmarker.logger.pretty_print(detail_level='summary') - Formatted table view")
        print("   • benchmarker.logger.print_log_details(benchmark_id, objective_id) - Specific log details")
        
        return True, (openai_benchmarker, anthropic_benchmarker)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


if __name__ == "__main__":
    success, results = main()
    
    if success:
        print("\n✅ All tests passed! Results available in returned benchmarkers.")
        # Keep results available for interactive exploration
        openai_benchmarker, anthropic_benchmarker = results
    else:
        print("\n❌ Tests failed. Check error messages above.")
        sys.exit(1)
