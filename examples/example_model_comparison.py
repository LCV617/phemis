#!/usr/bin/env python3
"""
Model Comparison Example - Compare different models on the same tasks.

This example demonstrates:
- Comparing multiple models on identical tasks
- Cost vs. quality analysis
- Performance benchmarking
- Response time comparison
- Creating detailed comparison reports

Usage:
    python3 example_model_comparison.py
"""

import os
import json
import time
import subprocess
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ModelResult:
    """Structure for storing model evaluation results."""
    model: str
    question: str
    response: Optional[str]
    success: bool
    tokens_used: int
    cost: float
    response_time: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class ModelStats:
    """Statistics for a model across multiple tasks."""
    model: str
    total_questions: int
    successful_questions: int
    total_cost: float
    total_tokens: int
    avg_response_time: float
    success_rate: float
    cost_per_question: float
    tokens_per_question: float
    cost_per_token: float

class ModelComparator:
    """Compare different models on the same set of tasks."""
    
    def __init__(self):
        """Initialize the model comparator."""
        self.results: List[ModelResult] = []
        self.model_stats: Dict[str, ModelStats] = {}
        
        # Verify CLI is available
        if not self._check_cli():
            raise RuntimeError("LLM CLI not available")
    
    def _check_cli(self) -> bool:
        """Check if LLM CLI is available."""
        try:
            subprocess.run(['llm', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def ask_question(
        self, 
        question: str, 
        model: str,
        system: Optional[str] = None,
        timeout: int = 60
    ) -> ModelResult:
        """
        Ask a question to a specific model and return structured result.
        
        Args:
            question: The question to ask
            model: Model identifier
            system: Optional system prompt
            timeout: Request timeout in seconds
            
        Returns:
            ModelResult with response and metadata
        """
        
        cmd = ['llm', 'ask', question, '--model', model, '--json']
        
        if system:
            cmd.extend(['--system', system])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Parse JSON response
            data = json.loads(result.stdout)
            
            return ModelResult(
                model=model,
                question=question,
                response=data.get('response'),
                success=True,
                tokens_used=data.get('usage', {}).get('total_tokens', 0),
                cost=data.get('estimated_cost_usd', 0.0),
                response_time=response_time
            )
            
        except subprocess.CalledProcessError as e:
            return ModelResult(
                model=model,
                question=question,
                response=None,
                success=False,
                tokens_used=0,
                cost=0.0,
                response_time=time.time() - start_time,
                error=f"Command failed: {e.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ModelResult(
                model=model,
                question=question,
                response=None,
                success=False,
                tokens_used=0,
                cost=0.0,
                response_time=timeout,
                error=f"Timeout after {timeout}s"
            )
        except json.JSONDecodeError as e:
            return ModelResult(
                model=model,
                question=question,
                response=None,
                success=False,
                tokens_used=0,
                cost=0.0,
                response_time=time.time() - start_time,
                error=f"JSON decode error: {e}"
            )
    
    def compare_models(
        self,
        questions: List[str],
        models: List[str],
        system: Optional[str] = None,
        show_progress: bool = True
    ) -> List[ModelResult]:
        """
        Compare multiple models on the same set of questions.
        
        Args:
            questions: List of questions to ask
            models: List of model identifiers
            system: Optional system prompt
            show_progress: Show progress during processing
            
        Returns:
            List of ModelResult objects
        """
        
        results = []
        total_tasks = len(questions) * len(models)
        completed = 0
        
        if show_progress:
            print(f"🏁 Starting comparison: {len(models)} models × {len(questions)} questions = {total_tasks} tasks")
            print(f"Models: {', '.join(models)}")
            if system:
                print(f"System: {system[:50]}..." if len(system) > 50 else f"System: {system}")
            print()
        
        for question_idx, question in enumerate(questions):
            if show_progress:
                print(f"📝 Question {question_idx + 1}/{len(questions)}: {question[:60]}...")
            
            for model in models:
                if show_progress:
                    print(f"   🤖 Testing {model}...", end=" ", flush=True)
                
                result = self.ask_question(question, model, system)
                results.append(result)
                completed += 1
                
                if show_progress:
                    if result.success:
                        print(f"✅ {result.tokens_used} tokens, ${result.cost:.6f}, {result.response_time:.1f}s")
                    else:
                        print(f"❌ {result.error}")
                
                # Small delay to be respectful to the API
                time.sleep(0.5)
        
        self.results = results
        self._calculate_stats()
        
        return results
    
    def _calculate_stats(self):
        """Calculate statistics for each model."""
        
        model_data: Dict[str, List[ModelResult]] = {}
        
        # Group results by model
        for result in self.results:
            if result.model not in model_data:
                model_data[result.model] = []
            model_data[result.model].append(result)
        
        # Calculate stats for each model
        for model, results in model_data.items():
            successful_results = [r for r in results if r.success]
            
            total_questions = len(results)
            successful_questions = len(successful_results)
            total_cost = sum(r.cost for r in successful_results)
            total_tokens = sum(r.tokens_used for r in successful_results)
            avg_response_time = sum(r.response_time for r in results) / len(results) if results else 0
            success_rate = successful_questions / total_questions if total_questions > 0 else 0
            cost_per_question = total_cost / successful_questions if successful_questions > 0 else 0
            tokens_per_question = total_tokens / successful_questions if successful_questions > 0 else 0
            cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            
            self.model_stats[model] = ModelStats(
                model=model,
                total_questions=total_questions,
                successful_questions=successful_questions,
                total_cost=total_cost,
                total_tokens=total_tokens,
                avg_response_time=avg_response_time,
                success_rate=success_rate,
                cost_per_question=cost_per_question,
                tokens_per_question=tokens_per_question,
                cost_per_token=cost_per_token
            )
    
    def print_comparison_table(self):
        """Print a detailed comparison table."""
        
        if not self.model_stats:
            print("❌ No stats available. Run comparison first.")
            return
        
        print("\n📊 Model Comparison Results")
        print("=" * 100)
        
        # Header
        header = f"{'Model':<25} {'Success':<8} {'Avg Cost':<10} {'Avg Tokens':<11} {'Avg Time':<9} {'Cost/Token':<12}"
        print(header)
        print("-" * len(header))
        
        # Sort by success rate, then by cost
        sorted_models = sorted(
            self.model_stats.items(),
            key=lambda x: (-x[1].success_rate, x[1].cost_per_question)
        )
        
        for model, stats in sorted_models:
            print(f"{model:<25} "
                  f"{stats.success_rate*100:>6.1f}% "
                  f"${stats.cost_per_question:>8.4f} "
                  f"{stats.tokens_per_question:>9.0f} "
                  f"{stats.avg_response_time:>7.1f}s "
                  f"${stats.cost_per_token:>10.6f}")
        
        print()
    
    def print_detailed_analysis(self):
        """Print detailed analysis of model performance."""
        
        print("🔍 Detailed Model Analysis")
        print("=" * 50)
        
        for model, stats in self.model_stats.items():
            print(f"\n🤖 {model}")
            print(f"   Questions answered: {stats.successful_questions}/{stats.total_questions}")
            print(f"   Success rate: {stats.success_rate*100:.1f}%")
            print(f"   Total cost: ${stats.total_cost:.6f}")
            print(f"   Total tokens: {stats.total_tokens:,}")
            print(f"   Average response time: {stats.avg_response_time:.2f}s")
            print(f"   Cost efficiency: ${stats.cost_per_token:.8f} per token")
            
            # Find the model's results for quality analysis
            model_results = [r for r in self.results if r.model == model and r.success]
            
            if model_results:
                # Response length analysis
                response_lengths = [len(r.response) for r in model_results if r.response]
                if response_lengths:
                    avg_length = sum(response_lengths) / len(response_lengths)
                    print(f"   Avg response length: {avg_length:.0f} characters")
                
                # Token efficiency
                token_costs = [r.cost / r.tokens_used for r in model_results if r.tokens_used > 0]
                if token_costs:
                    avg_token_cost = sum(token_costs) / len(token_costs)
                    print(f"   Token cost consistency: ${avg_token_cost:.8f} ± ${max(token_costs) - min(token_costs):.8f}")
    
    def print_quality_comparison(self, question_idx: int = 0):
        """Print side-by-side quality comparison for a specific question."""
        
        if question_idx >= len(set(r.question for r in self.results)):
            print("❌ Invalid question index")
            return
        
        # Get all results for the specified question
        question_results = []
        target_question = None
        
        for result in self.results:
            if target_question is None:
                target_question = result.question
                question_results.append(result)
            elif result.question == target_question:
                question_results.append(result)
            elif len(question_results) > question_idx:
                break
        
        # Skip to the requested question index
        questions_seen = set()
        target_question = None
        question_results = []
        
        for result in self.results:
            if result.question not in questions_seen:
                questions_seen.add(result.question)
                if len(questions_seen) - 1 == question_idx:
                    target_question = result.question
            
            if result.question == target_question:
                question_results.append(result)
        
        if not question_results:
            print("❌ No results found for the specified question")
            return
        
        print(f"\n🔍 Quality Comparison for Question {question_idx + 1}")
        print(f"Question: {target_question}")
        print("=" * 80)
        
        for result in question_results:
            print(f"\n🤖 {result.model}")
            print(f"   Status: {'✅ Success' if result.success else '❌ Failed'}")
            
            if result.success:
                print(f"   Cost: ${result.cost:.6f}")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.response_time:.1f}s")
                print(f"   Response:")
                
                # Format response nicely
                response = result.response or "No response"
                lines = response.split('\\n')
                for line in lines[:10]:  # Show first 10 lines
                    print(f"     {line}")
                
                if len(lines) > 10:
                    print(f"     ... ({len(lines) - 10} more lines)")
            else:
                print(f"   Error: {result.error}")
            
            print("-" * 40)
    
    def save_results(self, filename: str):
        """Save comparison results to JSON file."""
        
        output_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'models_compared': list(self.model_stats.keys()),
            'total_questions': len(set(r.question for r in self.results)),
            'total_tasks': len(self.results),
            'model_stats': {model: asdict(stats) for model, stats in self.model_stats.items()},
            'detailed_results': [r.to_dict() for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")

def create_test_questions() -> List[str]:
    """Create a set of test questions for model comparison."""
    
    return [
        "Explain the concept of machine learning in simple terms.",
        "What are the key differences between Python lists and tuples?",
        "How does recursion work? Provide a simple example.",
        "What is the purpose of version control systems like Git?",
        "Explain the difference between synchronous and asynchronous programming."
    ]

def demo_basic_comparison():
    """Demonstrate basic model comparison."""
    
    print("🏆 Basic Model Comparison Demo")
    print("=" * 50)
    
    comparator = ModelComparator()
    
    # Use budget-friendly models for demo
    models = [
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku"
    ]
    
    questions = create_test_questions()[:3]  # Use first 3 questions
    
    results = comparator.compare_models(
        questions=questions,
        models=models,
        system="Provide clear, concise explanations suitable for beginners."
    )
    
    comparator.print_comparison_table()
    comparator.print_detailed_analysis()
    
    return comparator

def demo_performance_comparison():
    """Demonstrate performance-focused comparison."""
    
    print("\n⚡ Performance Comparison Demo")
    print("=" * 50)
    
    comparator = ModelComparator()
    
    # Compare models with different performance characteristics
    models = [
        "openai/gpt-4o-mini",        # Fast and cheap
        "anthropic/claude-3-sonnet"  # More capable but expensive
    ]
    
    # Use questions that test different capabilities
    questions = [
        "Write a Python function to calculate Fibonacci numbers.",
        "Explain the time complexity of bubble sort algorithm.",
    ]
    
    results = comparator.compare_models(
        questions=questions,
        models=models,
        system="Provide accurate, detailed technical explanations with code examples."
    )
    
    comparator.print_comparison_table()
    
    # Show quality comparison for first question
    comparator.print_quality_comparison(0)
    
    return comparator

def demo_cost_analysis():
    """Demonstrate cost-focused analysis."""
    
    print("\n💰 Cost Analysis Demo")
    print("=" * 50)
    
    comparator = ModelComparator()
    
    # Compare models across different price points
    models = [
        "openai/gpt-4o-mini",      # Budget option
        "anthropic/claude-3-haiku", # Budget option
        "openai/gpt-4o"            # Premium option (if budget allows)
    ]
    
    # Use identical simple questions to focus on cost differences
    questions = [
        "What is Python?",
        "How do you create a list in Python?",
        "What is a function in programming?"
    ]
    
    results = comparator.compare_models(
        questions=questions,
        models=models,
        system="Answer in 1-2 sentences."
    )
    
    print("\\n💸 Cost Efficiency Analysis")
    print("-" * 30)
    
    for model, stats in comparator.model_stats.items():
        efficiency = stats.tokens_per_question / stats.cost_per_question if stats.cost_per_question > 0 else 0
        print(f"{model}:")
        print(f"  Cost per question: ${stats.cost_per_question:.6f}")
        print(f"  Tokens per question: {stats.tokens_per_question:.0f}")
        print(f"  Tokens per dollar: {efficiency:.0f}")
        print()
    
    return comparator

def main():
    """Main demonstration function."""
    
    print("🏆 LLM Model Comparison Examples")
    print("Compare different models on the same tasks to find the best fit.")
    print("Make sure you have set your OPENROUTER_API_KEY environment variable.")
    print()
    
    # Check environment
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ Error: OPENROUTER_API_KEY not set")
        print("Please set your API key:")
        print("export OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        sys.exit(1)
    
    # Interactive choice
    print("🎯 Choose a comparison demo:")
    print("1. Basic model comparison (2 models, 3 questions)")
    print("2. Performance comparison (technical questions)")
    print("3. Cost efficiency analysis")
    print("4. Custom comparison (choose your own models and questions)")
    print("0. Exit")
    
    choice = input("\\nEnter your choice (0-4): ").strip()
    
    comparator = None
    
    if choice == "1":
        comparator = demo_basic_comparison()
    elif choice == "2":
        comparator = demo_performance_comparison()
    elif choice == "3":
        comparator = demo_cost_analysis()
    elif choice == "4":
        print("\\n🛠️  Custom Comparison")
        print("This would allow you to specify custom models and questions.")
        print("For now, running basic comparison as example...")
        comparator = demo_basic_comparison()
    elif choice == "0":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    # Save results
    if comparator:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"model_comparison_{timestamp}.json"
        comparator.save_results(filename)
        
        print(f"\\n📊 Summary:")
        print(f"   Models compared: {len(comparator.model_stats)}")
        print(f"   Questions tested: {len(set(r.question for r in comparator.results))}")
        print(f"   Total tasks: {len(comparator.results)}")
        print(f"   Results saved to: {filename}")
    
    print("\\n🎉 Comparison completed!")
    print("\\n📖 Next steps:")
    print("• Analyze the saved results for detailed insights")
    print("• Try different models based on your specific needs")
    print("• Consider cost vs. quality trade-offs")
    print("• Use the best-performing model for your use case")

if __name__ == "__main__":
    main()