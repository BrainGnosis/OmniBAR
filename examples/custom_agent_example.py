#!/usr/bin/env python3
# © 2023 BrainGnosis Inc. All rights reserved.

"""
Custom Agent Example (Framework-Agnostic)
========================================

REAL-WORLD SCENARIO: You built custom Python agents and need to test them
without any framework dependencies. This shows pure Python agent benchmarking.

This example shows how to use OmniBAR with any custom Python agent,
regardless of framework (no LangChain, Pydantic AI, or other dependencies).

Perfect for:
- Testing your own custom agent implementations
- Learning OmniBAR fundamentals without framework complexity
- Understanding the core benchmarking pattern
- Building agents from scratch

Key Concepts Demonstrated:
- Custom agent classes with any invoke method name
- Framework-agnostic benchmarking
- Simple evaluation objectives
- Error handling and validation

LEARNING VALUE:
✅ Test any Python class as an agent
✅ Use custom method names (not just 'invoke')
✅ Framework-independent benchmarking
✅ Error handling and edge case testing

Usage:
    python basic/custom_agent_example.py
"""

# No environment variables needed for this example!
# This example uses only custom Python agents - no external APIs required.

from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import StringEqualityObjective, RegexMatchObjective
from omnibar.core.types import BoolEvalResult


class WeatherAgent:
    """
    A custom weather information agent.
    
    This demonstrates how any Python class can serve as an agent
    for OmniBAR evaluation, regardless of the framework used.
    """
    
    def __init__(self):
        """Initialize with some mock weather data."""
        self.weather_data = {
            "new_york": {"temp": 72, "condition": "sunny", "humidity": 45},
            "london": {"temp": 65, "condition": "cloudy", "humidity": 78},
            "tokyo": {"temp": 78, "condition": "rainy", "humidity": 82},
            "paris": {"temp": 68, "condition": "partly_cloudy", "humidity": 52}
        }
    
    def get_weather(self, city: str) -> dict:
        """
        Custom method name (not 'invoke') to show flexibility.
        
        OmniBAR can work with any method name by specifying
        agent_invoke_method_name in the benchmarker.
        """
        city_lower = city.lower().replace(" ", "_")
        
        if city_lower in self.weather_data:
            data = self.weather_data[city_lower]
            return {
                "city": city,
                "temperature": data["temp"],
                "condition": data["condition"], 
                "humidity": data["humidity"],
                "response": f"The weather in {city} is {data['condition']} with a temperature of {data['temp']}°F",
                "status": "found"
            }
        else:
            return {
                "city": city,
                "temperature": None,
                "condition": "unknown",
                "humidity": None,
                "response": f"Weather data for {city} is not available",
                "status": "not_found"
            }


class SimpleTranslatorAgent:
    """
    Another custom agent example showing different patterns.
    
    This agent uses the standard 'invoke' method name and demonstrates
    basic translation functionality with validation.
    """
    
    def __init__(self):
        """Initialize with a simple translation dictionary."""
        self.translations = {
            "hello": {"spanish": "hola", "french": "bonjour", "german": "hallo"},
            "goodbye": {"spanish": "adiós", "french": "au revoir", "german": "auf wiedersehen"},
            "thank_you": {"spanish": "gracias", "french": "merci", "german": "danke"}
        }
    
    def invoke(self, word: str, target_language: str) -> dict:
        """Standard invoke method that OmniBAR recognizes by default."""
        word_key = word.lower().replace(" ", "_")
        target_lang = target_language.lower()
        
        if word_key in self.translations and target_lang in self.translations[word_key]:
            translation = self.translations[word_key][target_lang]
            return {
                "original_word": word,
                "target_language": target_language,
                "translation": translation,
                "confidence": "high",
                "result": f"'{word}' in {target_language} is '{translation}'"
            }
        else:
            return {
                "original_word": word,
                "target_language": target_language,
                "translation": "unknown",
                "confidence": "none",
                "result": f"Cannot translate '{word}' to {target_language}"
            }


def create_weather_agent():
    """Factory function for the weather agent."""
    return WeatherAgent()


def create_translator_agent():
    """Factory function for the translator agent."""
    return SimpleTranslatorAgent()


def main():
    """Demonstrate custom agent benchmarking with different patterns."""
    
    print("🌤️  Custom Agent Benchmarking Example")
    print("=" * 50)
    
    # =============================================================================
    # Example 1: Custom Method Name Agent (Weather Agent)
    # =============================================================================
    print("\n📋 Example 1: Custom Method Name Agent")
    print("-" * 38)
    
    # Test if the weather agent correctly identifies sunny weather in New York
    sunny_objective = RegexMatchObjective(
        name="sunny_weather_check",
        output_key="response",
        goal=r".*sunny.*",  # Should mention "sunny" in the response
        valid_eval_result_type=BoolEvalResult
    )
    
    weather_benchmark = Benchmark(
        name="New York Weather Check", 
        input_kwargs={"city": "New York"},
        objective=sunny_objective,
        iterations=1
    )
    
    # Note: Using agent_invoke_method_name to specify custom method
    weather_benchmarker = OmniBarmarker(
        executor_fn=create_weather_agent,
        executor_kwargs={},
        agent_invoke_method_name="get_weather",  # Custom method name!
        initial_input=[weather_benchmark]
    )
    
    results = weather_benchmarker.benchmark()
    weather_benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 2: Standard Invoke Method Agent (Translator Agent)
    # =============================================================================
    print("\n📋 Example 2: Standard Invoke Method Agent")
    print("-" * 40)
    
    # Test if the translator correctly translates "hello" to Spanish
    translation_objective = StringEqualityObjective(
        name="spanish_translation",
        output_key="translation",
        goal="hola",  # Expected Spanish translation
        valid_eval_result_type=BoolEvalResult
    )
    
    translation_benchmark = Benchmark(
        name="Spanish Translation Test",
        input_kwargs={"word": "hello", "target_language": "spanish"},
        objective=translation_objective,
        iterations=1
    )
    
    # No need to specify method name - uses default 'invoke'
    translator_benchmarker = OmniBarmarker(
        executor_fn=create_translator_agent,
        executor_kwargs={},
        initial_input=[translation_benchmark]
    )
    
    results = translator_benchmarker.benchmark()
    translator_benchmarker.print_logger_summary()
    
    # =============================================================================
    # Example 3: Error Handling and Edge Cases  
    # =============================================================================
    print("\n📋 Example 3: Error Handling and Edge Cases")
    print("-" * 44)
    
    # Test how agents handle invalid inputs
    not_found_objective = StringEqualityObjective(
        name="handles_unknown_city",
        output_key="status",
        goal="not_found",  # Should return not_found status
        valid_eval_result_type=BoolEvalResult
    )
    
    error_benchmark = Benchmark(
        name="Unknown City Handling",
        input_kwargs={"city": "Atlantis"},  # Non-existent city
        objective=not_found_objective,
        iterations=1
    )
    
    error_benchmarker = OmniBarmarker(
        executor_fn=create_weather_agent,
        executor_kwargs={},
        agent_invoke_method_name="get_weather",
        initial_input=[error_benchmark]
    )
    
    results = error_benchmarker.benchmark()
    error_benchmarker.print_logger_summary()
    
    print("\n" + "=" * 50)
    print("✅ Custom Agent Examples Complete!")
    print("\n🎓 Key Learnings:")
    print("   • Any Python class can be an agent")
    print("   • Use agent_invoke_method_name for custom method names")
    print("   • Framework-agnostic benchmarking")
    print("   • Error handling and edge case testing")
    print("   • Factory functions for agent creation")


if __name__ == "__main__":
    main()
