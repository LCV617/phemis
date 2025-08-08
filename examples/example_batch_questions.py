#!/usr/bin/env python3
"""
Batch Questions Example - Process multiple questions efficiently.

This example demonstrates:
- Processing multiple questions in batch
- Cost optimization strategies
- Different output formats
- Error handling and retries
- Progress tracking

Usage:
    python3 example_batch_questions.py
"""

import os
import json
import time
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional

class LLMBatchProcessor:
    """Handles batch processing of LLM questions."""
    
    def __init__(self, model: str = "openai/gpt-4o-mini", max_workers: int = 3):
        """
        Initialize batch processor.
        
        Args:
            model: Default model to use
            max_workers: Maximum concurrent requests
        """
        self.model = model
        self.max_workers = max_workers
        self.total_cost = 0.0
        self.results = []
        
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
    
    def ask_single_question(
        self, 
        question: str, 
        model: Optional[str] = None,
        system: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Ask a single question and return structured result.
        
        Args:
            question: The question to ask
            model: Model to use (defaults to self.model)
            system: Optional system prompt
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with question, response, and metadata
        """
        
        model = model or self.model
        cmd = ['llm', 'ask', question, '--model', model, '--json']
        
        if system:
            cmd.extend(['--system', system])
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )\n            end_time = time.time()
            
            # Parse JSON response
            response_data = json.loads(result.stdout)
            
            # Add timing information
            response_data['processing_time'] = end_time - start_time
            response_data['success'] = True
            response_data['error'] = None
            
            # Track total cost
            if 'estimated_cost_usd' in response_data:
                self.total_cost += response_data['estimated_cost_usd']
            
            return response_data
            
        except subprocess.CalledProcessError as e:
            return {
                'question': question,
                'response': None,
                'model': model,
                'success': False,
                'error': f"Command failed with exit code {e.returncode}",
                'stderr': e.stderr if e.stderr else "No error details"
            }
        except subprocess.TimeoutExpired:
            return {
                'question': question,
                'response': None,
                'model': model,
                'success': False,
                'error': f"Request timed out after {timeout} seconds"
            }
        except json.JSONDecodeError as e:
            return {
                'question': question,
                'response': None,
                'model': model,
                'success': False,
                'error': f"Failed to parse JSON response: {e}"
            }
    
    def process_questions_sequential(
        self, 
        questions: List[str], 
        model: Optional[str] = None,
        system: Optional[str] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process questions sequentially (one at a time).
        
        Args:
            questions: List of questions to process
            model: Model to use for all questions
            system: Optional system prompt for all questions
            show_progress: Whether to show progress information
            
        Returns:
            List of results
        """
        
        results = []
        model = model or self.model
        
        print(f"🔄 Processing {len(questions)} questions sequentially...")
        print(f"📱 Model: {model}")
        if system:
            print(f"⚙️  System: {system[:50]}..." if len(system) > 50 else f"⚙️  System: {system}")
        print()
        
        for i, question in enumerate(questions, 1):
            if show_progress:
                print(f"[{i}/{len(questions)}] Processing: {question[:60]}...")
            
            result = self.ask_single_question(question, model, system)
            results.append(result)
            
            if result['success'] and show_progress:
                cost = result.get('estimated_cost_usd', 0)
                tokens = result.get('usage', {}).get('total_tokens', 0)
                print(f"   ✅ Success: {tokens} tokens, ${cost:.6f}")
            elif not result['success'] and show_progress:
                print(f"   ❌ Failed: {result['error']}")
            
            # Small delay to be respectful to the API
            time.sleep(0.5)
        
        return results
    
    def process_questions_parallel(
        self, 
        questions: List[str], 
        model: Optional[str] = None,
        system: Optional[str] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process questions in parallel (multiple concurrent requests).
        
        Args:
            questions: List of questions to process
            model: Model to use for all questions
            system: Optional system prompt for all questions
            show_progress: Whether to show progress information
            
        Returns:
            List of results
        """
        
        model = model or self.model
        
        print(f"🚀 Processing {len(questions)} questions in parallel...")
        print(f"📱 Model: {model}")
        print(f"🔧 Max workers: {self.max_workers}")
        if system:
            print(f"⚙️  System: {system[:50]}..." if len(system) > 50 else f"⚙️  System: {system}")
        print()
        
        results = [None] * len(questions)  # Maintain order
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all questions
            future_to_index = {
                executor.submit(self.ask_single_question, question, model, system): i
                for i, question in enumerate(questions)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                result = future.result()
                results[index] = result
                completed += 1
                
                if show_progress:
                    question = questions[index]
                    if result['success']:
                        cost = result.get('estimated_cost_usd', 0)
                        tokens = result.get('usage', {}).get('total_tokens', 0)
                        print(f"[{completed}/{len(questions)}] ✅ {question[:40]}... ({tokens} tokens, ${cost:.6f})")
                    else:
                        print(f"[{completed}/{len(questions)}] ❌ {question[:40]}... ({result['error']})")
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """Save results to JSON file."""
        
        output_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'model': self.model,
            'total_questions': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'total_cost': self.total_cost,
            'results': results
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print summary of batch processing results."""
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        total_tokens = sum(
            r.get('usage', {}).get('total_tokens', 0) 
            for r in successful
        )
        
        print("\n📊 Batch Processing Summary")
        print("=" * 40)
        print(f"Total questions: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Total cost: ${self.total_cost:.6f}")
        print(f"Average cost per question: ${self.total_cost/len(successful) if successful else 0:.6f}")
        
        if failed:
            print(f"\n❌ Failed Questions:")
            for result in failed[:5]:  # Show first 5 failures
                print(f"   • {result['question'][:60]}...")
                print(f"     Error: {result['error']}")
            if len(failed) > 5:
                print(f"   ... and {len(failed) - 5} more")

def create_sample_questions() -> List[str]:
    """Create a set of sample questions for demonstration."""
    
    return [
        "What is the difference between a list and a tuple in Python?",
        "Explain the concept of recursion with a simple example.",
        "How does garbage collection work in Python?",
        "What are Python decorators and when should I use them?",
        "Explain the difference between '==' and 'is' in Python.",
        "What is a lambda function and how is it different from a regular function?",
        "How do you handle exceptions in Python?",
        "What is the purpose of __init__ method in Python classes?",
        "Explain list comprehensions with examples.",
        "What is the difference between deep copy and shallow copy?",
        "How do you work with files in Python?",
        "What are generators and why are they useful?",
        "Explain the concept of inheritance in object-oriented programming.",
        "What is the Global Interpreter Lock (GIL) in Python?",
        "How do you create and use virtual environments in Python?"
    ]

def demo_sequential_processing():
    """Demonstrate sequential processing of questions."""
    
    print("🔄 Sequential Processing Demo")
    print("=" * 50)
    
    processor = LLMBatchProcessor(model="openai/gpt-4o-mini")
    questions = create_sample_questions()[:5]  # Use first 5 for demo
    
    start_time = time.time()
    results = processor.process_questions_sequential(
        questions,
        system="Answer concisely in 1-2 sentences."
    )
    end_time = time.time()
    
    print(f"\n⏱️  Total processing time: {end_time - start_time:.2f} seconds")
    processor.print_summary(results)
    
    return results

def demo_parallel_processing():
    """Demonstrate parallel processing of questions."""
    
    print("\n🚀 Parallel Processing Demo")
    print("=" * 50)
    
    processor = LLMBatchProcessor(model="openai/gpt-4o-mini", max_workers=3)
    questions = create_sample_questions()[:5]  # Use first 5 for demo
    
    start_time = time.time()
    results = processor.process_questions_parallel(
        questions,
        system="Answer concisely in 1-2 sentences."
    )
    end_time = time.time()
    
    print(f"\n⏱️  Total processing time: {end_time - start_time:.2f} seconds")
    processor.print_summary(results)
    
    return results

def demo_model_comparison():
    """Demonstrate comparing different models on the same questions."""
    
    print("\n🆚 Model Comparison Demo")
    print("=" * 50)
    
    questions = [
        "Explain machine learning in simple terms.",
        "What are the benefits of using Python for data science?"
    ]
    
    models = [
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku"
    ]
    
    all_results = {}
    
    for model in models:
        print(f"\n🤖 Testing model: {model}")
        processor = LLMBatchProcessor(model=model)
        
        results = processor.process_questions_sequential(
            questions,
            system="Provide a clear, educational explanation."
        )
        
        all_results[model] = {
            'results': results,
            'total_cost': processor.total_cost,
            'successful': sum(1 for r in results if r['success'])
        }
    
    # Compare results
    print("\n📊 Model Comparison Results")
    print("=" * 50)
    
    for model, data in all_results.items():
        print(f"\n🤖 {model}:")
        print(f"   Successful: {data['successful']}/{len(questions)}")
        print(f"   Total cost: ${data['total_cost']:.6f}")
        print(f"   Avg cost per question: ${data['total_cost']/data['successful'] if data['successful'] > 0 else 0:.6f}")
        
        # Show first response as sample
        if data['results'] and data['results'][0]['success']:
            sample_response = data['results'][0]['response'][:100]
            print(f"   Sample response: {sample_response}...")

def demo_error_handling():
    """Demonstrate error handling in batch processing."""
    
    print("\n🛡️  Error Handling Demo")
    print("=" * 50)
    
    # Include some problematic questions to trigger errors
    questions = [
        "What is Python?",  # Normal question
        "",  # Empty question (might cause error)
        "A" * 10000,  # Very long question (might cause error)
        "What is machine learning?",  # Normal question
    ]
    
    processor = LLMBatchProcessor(model="openai/gpt-4o-mini")
    
    results = processor.process_questions_sequential(
        questions,
        show_progress=True
    )
    
    processor.print_summary(results)
    
    return results

def main():
    """Main demonstration function."""
    
    print("🔄 LLM CLI Batch Processing Examples")
    print("This script demonstrates batch processing capabilities.")
    print("Make sure you have set your OPENROUTER_API_KEY environment variable.")
    print()
    
    # Check environment
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ Error: OPENROUTER_API_KEY not set")
        print("Please set your API key:")
        print("export OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        sys.exit(1)
    
    # Interactive choice
    print("🎯 Choose a demo to run:")
    print("1. Sequential processing (5 questions)")
    print("2. Parallel processing (5 questions)")
    print("3. Model comparison (2 questions, 2 models)")
    print("4. Error handling demo")
    print("5. Full batch example (15 questions)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    results = None
    
    if choice == "1":
        results = demo_sequential_processing()
    elif choice == "2":
        results = demo_parallel_processing()
    elif choice == "3":
        demo_model_comparison()
    elif choice == "4":
        results = demo_error_handling()
    elif choice == "5":
        print("🚀 Full Batch Example")
        print("=" * 50)
        processor = LLMBatchProcessor(model="openai/gpt-4o-mini")
        questions = create_sample_questions()
        results = processor.process_questions_parallel(questions)
        processor.print_summary(results)
    elif choice == "0":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    # Save results if available
    if results:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"batch_results_{timestamp}.json"
        
        processor = LLMBatchProcessor()  # Create processor to use save method
        processor.save_results(results, filename)
        
        print(f"\n💾 Results saved to: {filename}")
        print("You can analyze these results later or use them for further processing.")
    
    print("\n🎉 Demo completed!")
    print("\n📖 Next steps:")
    print("• Modify the questions list for your specific use case")
    print("• Experiment with different models and system prompts")
    print("• Implement retry logic for failed requests")
    print("• Add custom processing for the results")

if __name__ == "__main__":
    main()