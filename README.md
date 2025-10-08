<!-- @format -->

# OmniBAR

<p align="center">
  <img src="https://raw.githubusercontent.com/BrainGnosis/OmniBAR/main/assets/OmniBAR_Logo.png" alt="OmniBAR Logo" width="400">
</p>

<p align="center">
  <em>A Customizable, Multi-Objective AI Agent Benchmarking Framework for Agentic Reliability and Mediation (ARM)</em>
</p>

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/omnibar.svg)](https://pypi.org/project/omnibar/)

> **🚀 Quick Start in 2 minutes:** Clone → Install → Run → Get comprehensive agent evaluation results!

**Agentic Reliability and Mediation (ARM)** is a research and development area at BrainGnosis. We study how to measure and improve the reliability of AI agents and how they mediate conflicts during autonomous decision making. Our goal is to establish clear principles, metrics, and evaluation protocols that transfer across domains, so agents remain dependable, aligned, and resilient under varied operating conditions.

From this work we are releasing **OmniBAR** (**B**enchmarking **A**gentic **R**eliability), an open source, flexible, multi-objective benchmarking framework for evaluating AI agents across both standard suites and highly customized use cases. OmniBAR looks beyond output-only checks: it assesses decision quality, adaptability, conflict handling, and reliability in single-agent and multi-agent settings. Its modular design lets teams add scenarios, metrics, reward and constraint definitions, and integrations with tools and simulators. The result is domain-relevant testing with reproducible reports that reflect the demands of real-world applications.

> **⚠️ Development Version Notice**  
> OmniBAR is currently in active development. While we strive for stability, you may encounter bugs, breaking changes, or incomplete features. We recommend thorough testing in your specific use case and welcome bug reports and feedback to help us improve the framework.

## Table of Contents

- [About Us: BrainGnosis](#about-us-braingnosis)
- [Why OmniBAR?](#why-omnibar)
- [Why OmniBAR is Different](#why-omnibar-is-different)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [30-Second Demo](#30-second-demo)
- [Quick Start](#quick-start)
- [Common Use Cases](#common-use-cases)
- [Core Concepts](#core-concepts)
- [Examples](#examples)
- [Framework Integrations](#framework-integrations)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [Contributing](#contributing)
- [FAQ](#faq)
- [License](#license)
- [Support](#support)

## About Us: BrainGnosis

<div align="left">
  <img src="https://raw.githubusercontent.com/BrainGnosis/OmniBAR/main/assets/BrainGnosis.png" alt="BrainGnosis" width="400">
</div>

<br>

[**BrainGnosis**](https://www.braingnosis.com) is dedicated to making AI smarter for humans through structured intelligence and reliable AI systems. We are developing **AgentOS**, an enterprise operating system for intelligent AI agents that think, adapt, and collaborate to enhance organizational performance.

**Our Mission:** Build reliable, adaptable, and deeply human-aligned AI that transforms how businesses operate.

**🔗 Learn more:** [www.braingnosis.com](https://www.braingnosis.com)

---

## Why OmniBAR?

Traditional benchmarking approaches evaluate AI systems through simple input-output comparisons, missing the complex decision-making processes that modern AI agents employ.

<p align="center">
  <img src="https://raw.githubusercontent.com/BrainGnosis/OmniBAR/main/assets/General%20Benchmarking%20Process.png" alt="General Benchmarking Process" width="500">
</p>

**OmniBAR's Comprehensive Approach**  
OmniBAR captures the full spectrum of agentic behavior by evaluating multiple dimensions simultaneously - from reasoning chains to action sequences to system state changes.

<p align="center">
  <img src="https://raw.githubusercontent.com/BrainGnosis/OmniBAR/main/assets/OmniBAR%20Benchmarking%20Process.png" alt="OmniBAR Benchmarking Process" width="500">
</p>

## Why OmniBAR is Different

- **📊 Multi-Dimensional Evaluation**: Assess outputs, reasoning, actions, and states simultaneously with native support for output-based, path-based, state-based, and llm-as-a-judge evaluations
- **🔄 Agentic Loop Awareness**: Understands iterative thought-action-observation cycles that modern AI agents employ
- **🎯 Objective-Specific Analysis**: Different aspects evaluated by specialized objectives with comprehensive evaluation criteria
- **🔗 Comprehensive Coverage**: No blind spots in agent behavior assessment - captures the full decision-making process
- **⚡ High-Performance Execution**: Async-support enables rapid concurrent evaluation for faster benchmarking cycles
- **📊 Advanced Analytics**: Built-in AI summarization and customizable evaluation metrics for actionable insights
- **🔧 Extensible Architecture**: Modular design allowing custom objectives, evaluation criteria, and result types
- **🔄 Framework Agnostic**: Works seamlessly with any Python-based agent framework (LangChain, Pydantic AI, custom agents)

## How It Works

OmniBAR follows a clean, modular architecture that makes it easy to understand and extend:

```text
omnibar/
├── core/                     # Core benchmarking engine
│   ├── benchmarker.py       # Main OmniBARmarker class
│   └── types.py             # Type definitions and result classes
├── objectives/              # Evaluation objectives
│   ├── base.py             # Base objective class
│   ├── llm_judge.py        # LLM-based evaluation
│   ├── output.py           # Output comparison objectives
│   ├── path.py             # Path/action sequence evaluation
│   ├── state.py            # State-based evaluation
│   └── combined.py         # Multi-objective evaluation
├── integrations/            # Framework-specific integrations
│   └── pydantic_ai/        # Pydantic AI integration
└── logging/                # Logging and analytics
    ├── logger.py           # Comprehensive logging system
    └── evaluator.py        # Auto-evaluation and analysis
```

**Evaluation Flow:**

1. **Agent Execution**: Your agent processes input and generates output
2. **Multi-Objective Assessment**: Different objectives evaluate different aspects
3. **Comprehensive Logging**: Results are logged with detailed analytics
4. **Performance Insights**: Get actionable feedback on agent behavior

## Installation

### Prerequisites

- **Python 3.10+** (Required)
- **"API Keys"**: OpenAI, Anthropic (for LLM Judge objectives)
- **5 minutes** for setup and first benchmark

### Core Package

**Recommended Installation (Most Reliable):**

```bash
# Clone the repository
git clone https://github.com/BrainGnosis/OmniBAR.git
cd OmniBAR

# Install dependencies
pip install -r omnibar/requirements.txt

# Install in development mode
pip install -e .
```

**Alternative: PyPI Installation (Beta)**

> **⚠️ Beta Notice:** PyPI installation is available but currently in beta testing. Cross-platform compatibility is being actively improved. For the most reliable experience, we recommend the git installation above.

```bash
# Install from PyPI (beta - may have platform-specific issues)
pip install omnibar
```

### Environment Setup

Create a `.env` file in your project root with your API keys:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**✅ That's it!** OmniBAR automatically loads environment variables when you import it.

### Requirements

Core dependencies:

```txt
python==3.10+
langchain==0.3.27
langchain_core==0.3.75
langchain_openai==0.3.32
pydantic==2.11.7
rich==14.1.0
numpy==2.3.2
tqdm==4.67.1
```

## 30-Second Demo

Want to see OmniBAR in action immediately? Here's the minimal example:

```python
from omnibar import OmniBARmarker, Benchmark
from omnibar.objectives import StringEqualityObjective

# 1. Define a simple agent
class SimpleAgent:
    def invoke(self, query: str) -> dict:
        return {"answer": "Paris"}

def create_agent():
    return SimpleAgent()

# 2. Create benchmark
benchmark = Benchmark(
    name="Geography Test",
    input_kwargs={"query": "What's the capital of France?"},
    objective=StringEqualityObjective(name="exact_match", output_key="answer", goal="Paris"),
    iterations=1
)

# 3. Run evaluation
benchmarker = OmniBARmarker(
    executor_fn=create_agent,
    executor_kwargs={},
    initial_input=[benchmark]
)
results = benchmarker.benchmark()

# 4. View results
benchmarker.print_logger_summary()
```

**Output:**

```
✅ Geography Test: PASSED (100% accuracy)
📊 1/1 benchmarks passed | Runtime: 0.1s
```

## Quick Start

### OmniBrew – Prompt Trace Scoring with OmniBAR

OmniBrew is a lightweight full-stack experience built on top of OmniBAR to experiment with prompt executions, store their history, and review OmniBAR-derived scores.

**Backend**

1. Install dependencies (the backend can be run in isolation from the rest of the repo):

   ```bash
   pip install -r backend/requirements.txt
   ```

2. Copy `backend/.env.example` to `backend/.env` and provide any overrides. With `MOCK_MODE=true` (default) the server uses deterministic mock completions and OmniBAR scoring, so you can explore the full flow without spending API credits. Set an `OPENAI_API_KEY` and flip `MOCK_MODE=false` once you are ready for live calls.

3. Start the API:

   ```bash
   uvicorn backend.app:app --reload
   ```

   Swagger docs are available at `http://localhost:8000/docs`.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The UI lets you brew new “lattes” by providing system/user prompts and model settings, view OmniBAR scores with Barista’s Notes, and inspect historical rollups.

Run the lightweight backend checks with:

```bash
pytest tests/latte_lab -q
```

Here's a complete example demonstrating OmniBAR's core capabilities:

```python
import asyncio
from dotenv import load_dotenv
from omnibar import OmniBARmarker, Benchmark
from omnibar.objectives import LLMJudgeObjective, StringEqualityObjective, CombinedBenchmarkObjective
from omnibar.core.types import BoolEvalResult, FloatEvalResult

# Load environment variables
load_dotenv()

# Define your agent (works with any Python callable)
class SimpleAgent:
    def invoke(self, query: str) -> dict:
        if "capital" in query.lower() and "france" in query.lower():
            return {"response": "The capital of France is Paris."}
        return {"response": "I'm not sure about that."}

def create_agent():
    return SimpleAgent()

# Create evaluation objectives
accuracy_objective = StringEqualityObjective(
    name="exact_accuracy",
    output_key="response",
    goal="The capital of France is Paris."
)

quality_objective = LLMJudgeObjective(
    name="response_quality",
    output_key="response",
    goal="The agent identified the capital of France correctly",
    valid_eval_result_type=FloatEvalResult  # 0.0-1.0 scoring
)

# Combine multiple objectives
combined_objective = CombinedBenchmarkObjective(
    name="comprehensive_evaluation",
    objectives=[accuracy_objective, quality_objective]
)

# Create and run benchmark
async def main():
    benchmark = Benchmark(
        name="Geography Knowledge Test",
        input_kwargs={"query": "What is the capital of France?"},
        objective=combined_objective,
        iterations=5
    )

    benchmarker = OmniBARmarker(
        executor_fn=create_agent,
        executor_kwargs={},
        initial_input=[benchmark]
    )

    # Execute with concurrency control
    results = await benchmarker.benchmark_async(max_concurrent=3)

    # View results
    benchmarker.print_logger_summary()
    return results

# Run the benchmark
if __name__ == "__main__":
    results = asyncio.run(main())
```

### 🎯 **Next Steps**

**Got the basic example working?** Here's your learning path:

1. **🔍 Explore Examples:** Check out `examples/` directory for real-world use cases
2. **🎛️ Try Different Objectives:** Experiment with LLM Judge and Combined objectives
3. **⚡ Scale Up:** Use async benchmarking with `benchmark_async()` for faster evaluation
4. **🔧 Customize:** Create your own evaluation objectives for domain-specific needs
5. **📊 Analyze:** Dive deeper with `print_logger_details()` for comprehensive insights

**Need help?** Check our [FAQ](#faq) or join the [community discussions](https://github.com/BrainGnosis/OmniBAR/discussions)!

## Common Use Cases

Here are real-world scenarios where OmniBAR excels:

### 🏢 **Enterprise AI Validation**

**Scenario:** Validating customer service chatbots before deployment

- **Objectives:** LLM Judge for helpfulness + StringEquality for policy compliance
- **Benefit:** Ensure agents are both helpful AND follow company guidelines

### 🔬 **Research & Development**

**Scenario:** Comparing different agent architectures or prompting strategies

- **Objectives:** Combined objectives measuring accuracy, reasoning quality, and efficiency
- **Benefit:** Rigorous A/B testing with statistical significance

### 🚀 **Production Monitoring**

**Scenario:** Continuous evaluation of deployed agents

- **Objectives:** State-based objectives tracking system changes + output quality
- **Benefit:** Early detection of performance degradation

### 🎓 **Educational AI Assessment**

**Scenario:** Evaluating AI tutoring systems

- **Objectives:** Path-based objectives tracking learning progression + content accuracy
- **Benefit:** Comprehensive assessment of both teaching method and content quality

### 🤖 **Multi-Agent System Testing**

**Scenario:** Testing collaborative agent teams

- **Objectives:** State-based objectives for system coordination + individual agent performance
- **Benefit:** Holistic evaluation of complex agent interactions

### 💡 **When to Choose Each Objective Type**

| Objective Type   | Best For              | Example Use Case                 | Key Benefit           |
| ---------------- | --------------------- | -------------------------------- | --------------------- |
| **LLM Judge**    | Subjective qualities  | "Is this explanation clear?"     | Human-like evaluation |
| **Output-Based** | Exact requirements    | "Does output match format?"      | Precise validation    |
| **Path-Based**   | Process evaluation    | "Did agent use tools correctly?" | Workflow assessment   |
| **State-Based**  | System changes        | "Was database updated properly?" | State verification    |
| **Combined**     | Comprehensive testing | "All of the above"               | Complete coverage     |

## Core Concepts

### Evaluation Objectives

OmniBAR provides multiple evaluation objective types, each designed to address different evaluation challenges:

#### LLM Judge Objective

**When to use:** _"How do I evaluate subjective qualities like helpfulness, creativity, or nuanced correctness that can't be captured by exact matching?"_

Perfect for assessing complex, subjective criteria where human-like judgment is needed.

```python
# Boolean evaluation (pass/fail)
binary_objective = LLMJudgeObjective(
    name="correctness_check",
    output_key="response",
    goal="Provide a factually correct answer"
)

# Numerical evaluation (0.0-1.0 scoring)
scoring_objective = LLMJudgeObjective(
    name="quality_score",
    output_key="response",
    goal="Provide comprehensive and helpful information",
    valid_eval_result_type=FloatEvalResult
)
```

#### Output-Based Objectives

**When to use:** _"How do I verify that my agent produces the exact output I expect, or matches specific patterns?"_

Ideal for deterministic evaluations where you need precise output matching or format validation.

```python
# Exact string matching
exact_objective = StringEqualityObjective(
    name="exact_match",
    output_key="answer",
    goal="Paris"
)

# Regex pattern matching
pattern_objective = RegexMatchObjective(
    name="pattern_match",
    output_key="response",
    goal=r"Paris|paris"
)
```

#### Path-Based and State-Based Objectives

**When to use:** _"How do I evaluate not just what my agent outputs, but HOW it gets there and what changes it makes?"_

Essential for evaluating agent reasoning processes, tool usage sequences, and system state modifications.

```python
# Evaluate action sequences
path_objective = PathEqualityObjective(
    name="tool_usage",
    output_key="agent_path",
    goal=[[("search", SearchTool), ("summarize", None)]]
)

# Evaluate state changes
state_objective = StateEqualityObjective(
    name="final_state",
    output_key="agent_state",
    goal=ExpectedState
)
```

## Examples

> **📝 AI-Generated Content Notice**  
> The examples and tests in this repository were developed with assistance from AI coding tools and IDEs. While we have reviewed and tested the code, please validate the examples thoroughly in your own environment and adapt them to your specific needs.

### Complete Example Files

The `examples/` directory contains comprehensive examples:

- **`pydantic_ai_example.py`** - Model parity comparison (Claude 3.5 vs GPT-4)
- **`document_extraction_evolution.py`** - Document extraction prompt evolution (4 iterative improvements)
- **`langchain_embedding_example.py`** - LangChain embedding benchmarks
- **`inventory_management_example.py`** - Complex inventory management agent evaluation

**📋 Full Example List:**

- `output_evaluation.py` - Basic string/regex evaluation (no API keys needed)
- `custom_agent_example.py` - Framework-agnostic agent patterns
- `bool_vs_float_results.py` - Boolean vs scored result comparison
- `document_extraction_evolution.py` - Document extraction prompt evolution

See `examples/README.md` for detailed descriptions and setup instructions.

### Logging and Analytics

```python
# Print summary with key metrics
benchmarker.print_logger_summary()

# Detailed results with full evaluation data
benchmarker.print_logger_details(detail_level="detailed")

# Access raw logs for custom processing
logs = benchmarker.logger.get_all_logs()
```

## Framework Integrations

OmniBAR works seamlessly with popular AI agent frameworks:

<details>
<summary><strong>LangChain Integration</strong></summary>

```python
from langchain.agents import create_openai_functions_agent
from langchain_openai import ChatOpenAI

def create_langchain_agent():
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    tools = []  # Add your tools here
    agent = create_openai_functions_agent(llm, tools, prompt=None)
    return agent

benchmarker = OmniBARmarker(
    executor_fn=create_langchain_agent,
    executor_kwargs={},
    agent_invoke_method_name="invoke",
    initial_input=[benchmark]
)
```

</details>

<details>
<summary><strong>Pydantic AI Integration</strong></summary>

```python
from omnibar.integrations.pydantic_ai import PydanticAIOmniBARmarker
from pydantic_ai import Agent

def create_pydantic_agent():
    return Agent(model="openai:gpt-4", result_type=str)

benchmarker = PydanticAIOmniBARmarker(
    executor_fn=create_pydantic_agent,
    initial_input=[benchmark]
)
```

</details>

<details>
<summary><strong>Custom Agent Integration</strong></summary>

```python
class MyCustomAgent:
    def run(self, input_data: dict) -> dict:
        # Your custom agent logic
        return {"response": "Custom agent response"}

def create_custom_agent():
    return MyCustomAgent()

benchmarker = OmniBARmarker(
    executor_fn=create_custom_agent,
    executor_kwargs={},
    agent_invoke_method_name="run",  # Specify your agent's method
    initial_input=[benchmark]
)
```

</details>

## Advanced Usage

### Custom LLM Judge Prompts

```python
custom_objective = LLMJudgeObjective(
    name="factual_correctness",
    output_key="response",
    goal="Correctly identify the author",
    prompt="""
    Evaluate this response for factual correctness.

    Expected: {expected_output}
    Agent Response: {input}

    Return true if the information is factually correct.
    {format_instructions}
    """,
    valid_eval_result_type=BoolEvalResult
)
```

**Required Placeholders:** `{input}`, `{expected_output}`, `{format_instructions}`

### Custom Evaluation Functions

```python
def custom_evaluation_function(input_dict: dict) -> dict:
    agent_output = input_dict["input"]

    # Your custom logic here
    if "paris" in agent_output.lower():
        score = 0.9
        message = "Correctly identified Paris"
    else:
        score = 0.1
        message = "Failed to identify correct answer"

    return {"result": score, "message": message}

custom_objective = LLMJudgeObjective(
    name="custom_evaluation",
    output_key="response",
    invoke_method=custom_evaluation_function,
    valid_eval_result_type=FloatEvalResult
)
```

### Custom Objectives and Result Types

```python
from omnibar.core.types import ValidEvalResult
from omnibar.objectives.base import BaseBenchmarkObjective

class ScoreWithReason(ValidEvalResult):
    result: float
    reason: str

class CustomObjective(BaseBenchmarkObjective):
    valid_eval_result_type = ScoreWithReason

    def _eval_fn(self, goal, formatted_output, **kwargs):
        # Your evaluation logic
        score = 0.8
        reason = "Custom evaluation completed"
        return ScoreWithReason(result=score, reason=reason)
```

## Development

### Development Setup

```bash
git clone https://github.com/BrainGnosis/OmniBAR.git
cd OmniBAR

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
cd tests/

# Quick development tests
python run_tests.py fast        # ~4s, fast tests only
python run_tests.py imports     # ~1s, smoke test

# Run by category
python run_tests.py logging     # Test logging components
python run_tests.py core        # Core benchmarker tests
python run_tests.py objectives  # Evaluation objectives

# Comprehensive testing with rich output
python test_all.py --fast       # Skip slow tests
python test_all.py              # Everything (~5min)
python test_all.py --verbose    # Detailed failure info
```

See `tests/README.md` for detailed information about the test suite structure and available options.

## Contributing

We welcome contributions to OmniBAR! Here's how you can help:

### Ways to Contribute

- 🐛 **Bug Reports**: Found an issue? [Open an issue](https://github.com/BrainGnosis/OmniBAR/issues)
- 💡 **Feature Requests**: Have an idea? [Start a discussion](https://github.com/BrainGnosis/OmniBAR/discussions)
- 🔧 **Code Contributions**: Submit pull requests for bug fixes and new features
- 📚 **Documentation**: Help improve our docs and examples
- 🧪 **Testing**: Add test cases and improve test coverage

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run tests and ensure they pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for public functions and classes
- Run `pre-commit install` to enable automatic formatting

## FAQ

### General Questions

**Q: What makes OmniBAR different from other benchmarking tools?**
A: OmniBAR evaluates the full agentic loop (reasoning, actions, state changes) rather than just input-output comparisons. It supports multi-objective evaluation and works with any Python-based agent framework.

**Q: Can I use OmniBAR with my existing agent framework?**
A: Yes! OmniBAR is framework-agnostic and works with LangChain, Pydantic AI, AutoGen, or custom agents. Just provide a callable that takes input and returns output.

**Q: How do I create custom evaluation objectives?**
A: Extend `BaseBenchmarkObjective` and implement the `_eval_fn` method. See the [Custom Objectives examples](#custom-objectives-and-result-types) for details.

### Technical Questions

**Q: Does OmniBAR support async execution?**
A: Yes! Use `benchmarker.benchmark_async()` with concurrency control via the `max_concurrent` parameter.

**Q: How do I integrate with different LLM providers?**
A: OmniBAR uses your agent's LLM configuration. For LLM Judge objectives, set your API keys in the `.env` file and they'll be loaded automatically.

**Q: Can I benchmark multi-agent systems?**
A: Absolutely! Create benchmarks for each agent or use Combined objectives to evaluate multi-agent interactions.

### Troubleshooting

**Q: I'm getting import errors when using OmniBAR**
A: Ensure you've installed all dependencies: `pip install -r omnibar/requirements.txt`. Check that your Python version is 3.10+.

**Q: My custom evaluation isn't working**
A: Verify your `_eval_fn` returns the correct result type (BoolEvalResult, FloatEvalResult, etc.) and that required placeholders are included in custom prompts.

**Q: How do I debug failed benchmarks?**
A: Use `benchmarker.print_logger_details(detail_level="detailed")` to see full evaluation traces and error messages.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/BrainGnosis/OmniBAR/issues)
<!-- - **Discussions**: [GitHub Discussions](https://github.com/BrainGnosis/OmniBAR/discussions) -->
- **Email**: [dev@braingnosis.ai](mailto:dev@braingnosis.ai)

---

<div align="center">

**Built with ❤️ by** [**BrainGnosis**](https://www.braingnosis.com)

<a href="https://www.braingnosis.com">
  <img src="https://raw.githubusercontent.com/BrainGnosis/OmniBAR/main/assets/BrainGnosis.png" alt="BrainGnosis" width="220">
</a>

_Making AI Smarter for Humans_

</div>
