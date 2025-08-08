#!/usr/bin/env python3
"""
Script de test pour la commande ask.

Usage:
    python test_ask.py
"""

import sys
import os

# Ajouter le projet au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.cli.ask import ask_app

if __name__ == "__main__":
    # Tester la commande ask
    print("Testing the ask command...")
    print("Usage: llm ask \"Your question\" --model openai/gpt-4o-mini")
    print("\nTo test with a real question, set your OPENROUTER_API_KEY environment variable and run:")
    print("python -m llm.cli.ask \"What is 2+2?\" --model openai/gpt-4o-mini")
    
    # Afficher l'aide
    try:
        ask_app(["--help"])
    except SystemExit:
        pass  # C'est normal pour --help