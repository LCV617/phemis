#!/usr/bin/env python3
"""
Exemple d'utilisation de la commande ask programmatiquement.

Ce fichier montre comment utiliser la commande ask à la fois via CLI et programmatiquement.
"""

import os
import sys
import json
from typing import Optional

# Ajouter le projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.cli.ask import ask_question
from llm.core.provider_openrouter import OpenRouterProvider, OpenRouterError
from llm.core.session import ChatSession
from llm.core.schema import Message, MessageRole, Usage


def example_ask_programmatic():
    """Exemple d'utilisation programmatique de la logique ask."""
    print("=== Exemple d'utilisation programmatique ===")
    
    try:
        # Vérifier la clé API
        if not os.getenv("OPENROUTER_API_KEY"):
            print("⚠️ OPENROUTER_API_KEY non définie. Définissez-la pour tester l'API réelle.")
            return
        
        # Initialiser le provider
        provider = OpenRouterProvider()
        
        # Question et modèle
        question = "Explain what is Python in one sentence."
        model = "openai/gpt-4o-mini"
        
        print(f"Question: {question}")
        print(f"Model: {model}")
        print("\nResponse:")
        print("-" * 50)
        
        # Créer une session temporaire
        session = ChatSession(model=model)
        session.append_user(question)
        
        # Préparer les messages
        api_messages = []
        for msg_dict in session.get_messages_for_api():
            api_messages.append(Message(
                role=MessageRole(msg_dict['role']),
                content=msg_dict['content']
            ))
        
        # Faire l'appel API (mode non-streaming pour cet exemple)
        response = provider.chat_completion(
            messages=api_messages,
            model=model,
            stream=False
        )
        
        # Extraire la réponse
        choices = response.get('choices', [])
        if choices:
            content = choices[0].get('message', {}).get('content', '')
            usage_data = response.get('usage', {})
            
            print(content)
            print("-" * 50)
            
            if usage_data:
                print(f"Usage: {usage_data.get('prompt_tokens', 0)} → {usage_data.get('completion_tokens', 0)} tokens")
        
    except OpenRouterError as e:
        print(f"Erreur OpenRouter: {e}")
    except Exception as e:
        print(f"Erreur: {e}")


def example_json_output():
    """Exemple de sortie JSON."""
    print("\n=== Exemple de sortie JSON ===")
    
    # Simuler une réponse JSON
    json_response = {
        "question": "What is the capital of France?",
        "response": "The capital of France is Paris.",
        "model": "openai/gpt-4o-mini",
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20
        },
        "latency_ms": 1250.5,
        "estimated_cost_usd": 0.0002
    }
    
    print(json.dumps(json_response, indent=2, ensure_ascii=False))


def show_cli_examples():
    """Affiche des exemples d'utilisation CLI."""
    print("\n=== Exemples d'utilisation CLI ===")
    
    examples = [
        {
            "description": "Question simple",
            "command": 'python -m llm.cli.ask "What is 2+2?" --model openai/gpt-4o-mini'
        },
        {
            "description": "Avec prompt système",
            "command": 'python -m llm.cli.ask "Explain AI" --model openai/gpt-4o-mini --system "You are a helpful teacher"'
        },
        {
            "description": "Sortie JSON pour scripts",
            "command": 'python -m llm.cli.ask "Hello world" --model openai/gpt-4o-mini --json'
        },
        {
            "description": "Question longue avec échappement",
            "command": 'python -m llm.cli.ask "Can you write a Python function to calculate fibonacci numbers?" --model anthropic/claude-3-haiku'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}:")
        print(f"   {example['command']}")
        print()


def show_integration_examples():
    """Montre des exemples d'intégration dans des scripts."""
    print("=== Exemples d'intégration dans des scripts ===")
    
    bash_example = '''#!/bin/bash
# Exemple d'intégration Bash
RESPONSE=$(python -m llm.cli.ask "What's the weather like?" --model openai/gpt-4o-mini --json)
echo "Response: $RESPONSE"
'''
    
    python_example = '''# Exemple d'intégration Python
import subprocess
import json

def ask_llm(question, model="openai/gpt-4o-mini"):
    cmd = [
        "python", "-m", "llm.cli.ask",
        question,
        "--model", model,
        "--json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Error: {result.stderr}")

# Usage
response = ask_llm("Explain quantum computing")
print(f"Answer: {response['response']}")
print(f"Cost: ${response['estimated_cost_usd']:.4f}")
'''
    
    print("Bash integration:")
    print(bash_example)
    print("\nPython integration:")
    print(python_example)


if __name__ == "__main__":
    print("🚀 Exemples d'utilisation de la commande ask")
    print("=" * 60)
    
    # Exemples CLI
    show_cli_examples()
    
    # Exemple JSON
    example_json_output()
    
    # Usage programmatique (nécessite une clé API)
    example_ask_programmatic()
    
    # Exemples d'intégration
    show_integration_examples()
    
    print("\n✅ Pour tester avec une vraie API, définissez OPENROUTER_API_KEY et exécutez :")
    print("export OPENROUTER_API_KEY='your-key-here'")
    print('python -m llm.cli.ask "Hello, how are you?" --model openai/gpt-4o-mini')