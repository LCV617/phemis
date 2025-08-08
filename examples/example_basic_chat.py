#!/usr/bin/env python3
"""
Basic Chat Example - Simple conversation with LLM CLI.

This example demonstrates:
- Launching a basic chat session
- Using environment variables for configuration
- Basic error handling
- Session management

Usage:
    python3 example_basic_chat.py
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Ensure API key is configured."""
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not set")
        print("Please set your API key:")
        print("export OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        sys.exit(1)
    
    # Verify API key format
    if not api_key.startswith('sk-or-v1-'):
        print("⚠️  Warning: API key doesn't look like OpenRouter format")
        print("Expected format: sk-or-v1-...")
        
    print(f"✅ API key configured: {api_key[:15]}...")

def check_cli_available():
    """Check if LLM CLI is available."""
    
    try:
        result = subprocess.run(
            ['llm', '--version'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ LLM CLI available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ LLM CLI not found")
        print("Please install it first:")
        print("pip install -e .")
        return False

def demonstrate_basic_chat():
    """Demonstrate basic chat functionality."""
    
    print("\n🤖 Starting Basic Chat Example")
    print("=" * 50)
    
    # Use a budget-friendly model for the example
    model = "openai/gpt-4o-mini"
    budget = "0.25"  # 25 cents limit for safety
    
    print(f"Model: {model}")
    print(f"Budget: ${budget}")
    print("Type ':exit' to end the session")
    print("Type ':help' to see available commands")
    print("-" * 50)
    
    try:
        # Start interactive chat
        subprocess.run([
            'llm', 'chat',
            '--model', model,
            '--budget', budget,
            '--save-dir', './runs'
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Chat failed with exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Chat interrupted by user")
        return True
    
    print("✅ Chat completed successfully")
    return True

def demonstrate_single_question():
    """Demonstrate single question/answer."""
    
    print("\n❓ Single Question Example")
    print("=" * 50)
    
    question = "What is the difference between a list and a tuple in Python?"
    model = "openai/gpt-4o-mini"
    
    print(f"Question: {question}")
    print(f"Model: {model}")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'llm', 'ask',
            question,
            '--model', model
        ], check=True)
        
        print("✅ Question answered successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Question failed with exit code: {e.returncode}")
        return False

def demonstrate_model_exploration():
    """Demonstrate model exploration features."""
    
    print("\n🔍 Model Exploration Example")
    print("=" * 50)
    
    try:
        # List available models
        print("📋 Listing available models...")
        subprocess.run([
            'llm', 'models', 'list', 
            '--filter', 'openai'
        ], check=True)
        
        print("\n📊 Getting detailed model information...")
        subprocess.run([
            'llm', 'models', 'info', 
            'openai/gpt-4o-mini'
        ], check=True)
        
        print("✅ Model exploration completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Model exploration failed: {e.returncode}")
        return False

def demonstrate_json_output():
    """Demonstrate JSON output for automation."""
    
    print("\n🤖 JSON Output Example")
    print("=" * 50)
    
    question = "Calculate 15% of 240"
    model = "openai/gpt-4o-mini"
    
    try:
        result = subprocess.run([
            'llm', 'ask',
            question,
            '--model', model,
            '--json'
        ], capture_output=True, text=True, check=True)
        
        # Parse and display JSON response
        import json
        response_data = json.loads(result.stdout)
        
        print("Raw JSON Response:")
        print(json.dumps(response_data, indent=2))
        
        print(f"\n📊 Extracted Information:")
        print(f"Question: {response_data['question']}")
        print(f"Answer: {response_data['response']}")
        print(f"Model: {response_data['model']}")
        print(f"Tokens: {response_data['usage']['total_tokens']}")
        print(f"Cost: ${response_data['estimated_cost_usd']:.6f}")
        
        print("✅ JSON output demonstration completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ JSON example failed: {e.returncode}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return False

def check_sessions():
    """Check if any sessions were created."""
    
    runs_dir = Path('./runs')
    if runs_dir.exists():
        session_files = list(runs_dir.glob('*.json'))
        if session_files:
            print(f"\n💾 {len(session_files)} session(s) created in ./runs/")
            print("You can view them with:")
            print("llm sessions list")
            print("\nOr resume a session with:")
            print(f"llm sessions resume {session_files[-1]}")
        else:
            print("\n💾 No session files found (sessions may not have been saved)")
    else:
        print("\n💾 No runs directory found")

def main():
    """Main demonstration function."""
    
    print("🚀 LLM CLI Basic Examples")
    print("This script demonstrates basic usage of the LLM CLI tool.")
    print("Make sure you have set your OPENROUTER_API_KEY environment variable.")
    print()
    
    # Setup and validation
    setup_environment()
    if not check_cli_available():
        sys.exit(1)
    
    # Interactive choice
    print("\n🎯 Choose an example to run:")
    print("1. Basic interactive chat")
    print("2. Single question/answer")
    print("3. Model exploration")
    print("4. JSON output for automation")
    print("5. All examples (non-interactive)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    if choice == "1":
        demonstrate_basic_chat()
    elif choice == "2":
        demonstrate_single_question()
    elif choice == "3":
        demonstrate_model_exploration()
    elif choice == "4":
        demonstrate_json_output()
    elif choice == "5":
        print("🚀 Running all non-interactive examples...")
        demonstrate_single_question()
        demonstrate_model_exploration()
        demonstrate_json_output()
        print("\n🎉 All examples completed!")
    elif choice == "0":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    # Check for created sessions
    check_sessions()
    
    print("\n🎉 Example completed!")
    print("\n📖 Next steps:")
    print("• Try the interactive chat for longer conversations")
    print("• Explore different models with 'llm models list'")
    print("• Check your session history with 'llm sessions list'")
    print("• Read the full documentation in ./docs/")

if __name__ == "__main__":
    main()