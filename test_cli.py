#!/usr/bin/env python3
"""
Script de test pour le CLI LLM.

Ce script permet de tester les fonctionnalités du CLI en simulation,
sans nécessiter de vraie clé API OpenRouter.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.core.schema import ModelInfo
from llm.cli.main import app


def create_mock_models():
    """Crée des modèles de test pour la démonstration."""
    return [
        ModelInfo(
            id="openai/gpt-4o-mini",
            context_length=128000,
            pricing_prompt=0.000000015,  # $0.15/1M tokens
            pricing_completion=0.000000600,  # $0.60/1M tokens
            description="Latest GPT-4o mini model with improved efficiency and reasoning capabilities"
        ),
        ModelInfo(
            id="anthropic/claude-3-sonnet",
            context_length=200000,
            pricing_prompt=0.000003000,  # $3.00/1M tokens
            pricing_completion=0.000015000,  # $15.00/1M tokens
            description="Claude 3 Sonnet offers the ideal balance of intelligence and speed for enterprise workloads"
        ),
        ModelInfo(
            id="google/gemini-pro",
            context_length=32000,
            pricing_prompt=0.000001000,  # $1.00/1M tokens
            pricing_completion=0.000003000,  # $3.00/1M tokens
            description="Google's most capable AI model for complex reasoning and code generation"
        ),
        ModelInfo(
            id="meta/llama-3.1-70b",
            context_length=131072,
            pricing_prompt=0.000000900,  # $0.90/1M tokens
            pricing_completion=0.000000900,  # $0.90/1M tokens
            description="Meta's Llama 3.1 70B model - open-source excellence for various tasks"
        ),
    ]


def test_models_list():
    """Test de la commande 'llm models list' avec des données simulées."""
    print("=== Test: llm models list ===")
    
    # Mock de l'environnement et du provider
    mock_models = create_mock_models()
    
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        with patch("llm.cli.models.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.list_models.return_value = mock_models
            mock_provider_class.return_value = mock_provider
            
            # Simuler l'appel CLI
            import typer.testing
            runner = typer.testing.CliRunner()
            
            # Test basique
            result = runner.invoke(app, ["models", "list"])
            print(f"Exit code: {result.exit_code}")
            print("Output:")
            print(result.stdout)
            print()
            
            # Test avec filtre
            result = runner.invoke(app, ["models", "list", "--filter", "gpt"])
            print("=== Test avec filtre 'gpt' ===")
            print(f"Exit code: {result.exit_code}")
            print("Output:")
            print(result.stdout)
            print()


def test_models_info():
    """Test de la commande 'llm models info' avec des données simulées."""
    print("=== Test: llm models info ===")
    
    mock_models = create_mock_models()
    
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        with patch("llm.cli.models.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.list_models.return_value = mock_models
            mock_provider_class.return_value = mock_provider
            
            import typer.testing
            runner = typer.testing.CliRunner()
            
            # Test info d'un modèle existant
            result = runner.invoke(app, ["models", "info", "openai/gpt-4o-mini"])
            print(f"Exit code: {result.exit_code}")
            print("Output:")
            print(result.stdout)
            print()
            
            # Test info d'un modèle inexistant
            result = runner.invoke(app, ["models", "info", "nonexistent/model"])
            print("=== Test modèle inexistant ===")
            print(f"Exit code: {result.exit_code}")
            print("Output:")
            print(result.stdout)
            print()


def test_error_handling():
    """Test de la gestion d'erreurs."""
    print("=== Test: Gestion d'erreurs ===")
    
    import typer.testing
    runner = typer.testing.CliRunner()
    
    # Test sans clé API
    with patch.dict(os.environ, {}, clear=True):  # Clear all env vars
        result = runner.invoke(app, ["models", "list"])
        print("Test sans clé API:")
        print(f"Exit code: {result.exit_code}")
        print("Output:")
        print(result.stdout)
        print()


def test_version():
    """Test de la commande --version."""
    print("=== Test: --version ===")
    
    import typer.testing
    runner = typer.testing.CliRunner()
    
    result = runner.invoke(app, ["--version"])
    print(f"Exit code: {result.exit_code}")
    print("Output:")
    print(result.stdout)
    print()


if __name__ == "__main__":
    print("🧪 Tests du CLI LLM\n")
    print("=" * 50)
    
    try:
        test_version()
        test_error_handling()
        test_models_list()
        test_models_info()
        
        print("✅ Tous les tests sont terminés!")
        
    except Exception as e:
        print(f"❌ Erreur pendant les tests: {e}")
        sys.exit(1)