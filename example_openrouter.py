#!/usr/bin/env python3
"""
Exemple d'utilisation du provider OpenRouter.

Ce script démontre comment utiliser le provider OpenRouter pour:
- Lister les modèles disponibles
- Effectuer des complétions de chat (synchrone et streaming)
- Gérer les erreurs et calculer les coûts
"""

import os
from llm.core import (
    OpenRouterProvider, 
    Message, 
    MessageRole,
    OpenRouterError,
    OpenRouterAuthError
)


def example_list_models():
    """Exemple de liste des modèles disponibles."""
    print("=== Exemple: Liste des modèles ===")
    
    try:
        # Initialiser le provider (utilise OPENROUTER_API_KEY de l'environnement)
        provider = OpenRouterProvider()
        
        # Récupérer la liste des modèles
        models = provider.list_models()
        
        print(f"Nombre de modèles disponibles: {len(models)}")
        print("\nPremiers 5 modèles:")
        
        for model in models[:5]:
            print(f"- ID: {model.id}")
            print(f"  Contexte: {model.context_length} tokens")
            print(f"  Prix prompt: ${model.pricing_prompt}")
            print(f"  Prix completion: ${model.pricing_completion}")
            print(f"  Description: {model.description}")
            print()
            
    except OpenRouterAuthError:
        print("❌ Erreur d'authentification: Vérifiez votre OPENROUTER_API_KEY")
    except OpenRouterError as e:
        print(f"❌ Erreur OpenRouter: {e}")


def example_chat_completion_sync():
    """Exemple de complétion de chat synchrone."""
    print("=== Exemple: Chat completion synchrone ===")
    
    try:
        provider = OpenRouterProvider()
        
        # Préparer les messages
        messages = [
            Message(role=MessageRole.USER, content="Bonjour! Peux-tu m'expliquer brièvement ce qu'est l'IA?")
        ]
        
        print("Envoi de la requête...")
        
        # Effectuer la complétion (non-streaming)
        response = provider.chat_completion(
            messages=messages,
            model="openai/gpt-3.5-turbo",  # Modèle exemple
            stream=False
        )
        
        # Extraire la réponse
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"Réponse: {content}")
            
            # Afficher l'usage si disponible
            if "usage" in response:
                usage = response["usage"]
                print(f"Usage: {usage['prompt_tokens']} + {usage['completion_tokens']} = {usage['total_tokens']} tokens")
        
    except OpenRouterError as e:
        print(f"❌ Erreur: {e}")


def example_chat_completion_streaming():
    """Exemple de complétion de chat en streaming."""
    print("=== Exemple: Chat completion streaming ===")
    
    try:
        provider = OpenRouterProvider()
        
        messages = [
            Message(role=MessageRole.USER, content="Raconte-moi une histoire courte sur les robots.")
        ]
        
        print("Streaming en cours...")
        print("Réponse: ", end="", flush=True)
        
        # Effectuer la complétion en streaming
        stream = provider.chat_completion(
            messages=messages,
            model="openai/gpt-3.5-turbo",
            stream=True
        )
        
        full_content = ""
        for chunk in stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    content = delta["content"]
                    print(content, end="", flush=True)
                    full_content += content
                    
        print("\n")
        print(f"Réponse complète reçue ({len(full_content)} caractères)")
        
    except OpenRouterError as e:
        print(f"❌ Erreur: {e}")


def example_error_handling():
    """Exemple de gestion d'erreurs."""
    print("=== Exemple: Gestion d'erreurs ===")
    
    try:
        # Initialiser avec une fausse clé API
        provider = OpenRouterProvider(api_key="fake-key")
        models = provider.list_models()
        
    except OpenRouterAuthError:
        print("✅ Erreur d'authentification correctement détectée")
    except OpenRouterError as e:
        print(f"✅ Erreur OpenRouter: {e}")


def main():
    """Fonction principale pour exécuter tous les exemples."""
    # Vérifier que la clé API est configurée
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Attention: OPENROUTER_API_KEY n'est pas définie dans l'environnement")
        print("Les exemples ne fonctionneront pas sans une clé API valide.")
        print()
    
    # Exécuter les exemples
    example_list_models()
    print("\n" + "="*50 + "\n")
    
    example_chat_completion_sync()
    print("\n" + "="*50 + "\n")
    
    example_chat_completion_streaming()
    print("\n" + "="*50 + "\n")
    
    example_error_handling()


if __name__ == "__main__":
    main()