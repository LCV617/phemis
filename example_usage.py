#!/usr/bin/env python3
"""
Exemple d'utilisation des modèles Pydantic pour l'outil CLI LLM.
"""

from llm.core.schema import (
    Message, MessageRole, Usage, ModelInfo, Turn, Session, ChatConfig
)
from datetime import datetime
import json

def demo_conversation():
    """Démontre une conversation complète avec calculs de métriques."""
    print("=== Démonstration d'une conversation complète ===\n")
    
    # Configuration initiale
    config = ChatConfig(
        model="gpt-4",
        system="Tu es un assistant expert en Python qui aide les développeurs.",
        budget_max=5.0
    )
    
    # Création d'une session depuis la configuration
    session = config.to_session()
    print(f"Session créée avec le modèle: {session.model}")
    print(f"Message système: {session.system}")
    print(f"Budget max: ${config.budget_max}\n")
    
    # Tour 1: Question sur Python
    user_msg1 = Message(role=MessageRole.USER, content="Comment créer une classe en Python?")
    assistant_msg1 = Message(
        role=MessageRole.ASSISTANT, 
        content="Pour créer une classe en Python, utilisez le mot-clé 'class' suivi du nom de la classe et de deux-points. Par exemple:\n\nclass MaClasse:\n    def __init__(self):\n        pass"
    )
    
    usage1 = Usage(prompt_tokens=15, completion_tokens=45, total_tokens=60)
    turn1 = Turn(
        messages=[user_msg1, assistant_msg1],
        usage=usage1,
        latency_ms=1200.0,
        cost_estimate=0.0018  # 60 tokens * 0.00003 $/token
    )
    
    session.add_turn(turn1)
    print(f"Tour 1 ajouté - Tokens utilisés: {usage1.total_tokens}, Coût: ${turn1.cost_estimate}")
    
    # Tour 2: Question de suivi
    user_msg2 = Message(role=MessageRole.USER, content="Peux-tu me donner un exemple avec des méthodes?")
    assistant_msg2 = Message(
        role=MessageRole.ASSISTANT,
        content="Bien sûr! Voici un exemple plus complet:\n\nclass Personne:\n    def __init__(self, nom, age):\n        self.nom = nom\n        self.age = age\n    \n    def se_presenter(self):\n        return f'Je suis {self.nom} et j\\'ai {self.age} ans'\n    \n    def avoir_anniversaire(self):\n        self.age += 1\n        print(f'Joyeux anniversaire! {self.nom} a maintenant {self.age} ans')"
    )
    
    usage2 = Usage(prompt_tokens=25, completion_tokens=85, total_tokens=110)
    turn2 = Turn(
        messages=[user_msg2, assistant_msg2],
        usage=usage2,
        latency_ms=1800.0,
        cost_estimate=0.0033  # 110 tokens * 0.00003 $/token
    )
    
    session.add_turn(turn2)
    print(f"Tour 2 ajouté - Tokens utilisés: {usage2.total_tokens}, Coût: ${turn2.cost_estimate}")
    
    # Affichage des statistiques finales
    print(f"\n=== Statistiques de la session ===")
    print(f"Nombre de tours: {len(session.turns)}")
    print(f"Total tokens: {session.usage_totals.total_tokens}")
    print(f"Tokens prompts: {session.usage_totals.prompt_tokens}")
    print(f"Tokens completions: {session.usage_totals.completion_tokens}")
    print(f"Coût total estimé: ${session.calculate_total_cost():.4f}")
    print(f"Budget restant: ${config.budget_max - session.calculate_total_cost():.4f}")
    
    # Affichage de tous les messages dans l'ordre
    print(f"\n=== Historique complet de la conversation ===")
    all_messages = session.get_all_messages()
    for i, msg in enumerate(all_messages, 1):
        role_display = {
            MessageRole.SYSTEM: "SYSTÈME",
            MessageRole.USER: "UTILISATEUR", 
            MessageRole.ASSISTANT: "ASSISTANT"
        }[msg.role]
        print(f"{i}. [{role_display}] {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
    
    return session

def demo_model_info():
    """Démontre la gestion des informations de modèles."""
    print("\n=== Gestion des informations de modèles ===\n")
    
    # Différents modèles avec leurs caractéristiques
    models = [
        ModelInfo(
            id="gpt-4",
            context_length=8192,
            pricing_prompt=0.03,
            pricing_completion=0.06,
            description="Modèle le plus puissant d'OpenAI"
        ),
        ModelInfo(
            id="gpt-3.5-turbo",
            context_length=4096,
            pricing_prompt=0.0015,
            pricing_completion=0.002,
            description="Modèle rapide et économique"
        ),
        ModelInfo(
            id="claude-3-opus",
            context_length=200000,
            pricing_prompt=0.015,
            pricing_completion=0.075,
            description="Modèle Anthropic avec très long contexte"
        )
    ]
    
    print("Comparaison des modèles disponibles:")
    print("=" * 80)
    print(f"{'Modèle':<20} {'Contexte':<10} {'Prix Prompt':<12} {'Prix Compl.':<12} {'Description'}")
    print("=" * 80)
    
    for model in models:
        context = f"{model.context_length:,}" if model.context_length else "N/A"
        prompt_price = f"${model.pricing_prompt:.4f}" if model.pricing_prompt else "N/A"
        completion_price = f"${model.pricing_completion:.4f}" if model.pricing_completion else "N/A"
        description = model.description[:25] + "..." if len(model.description) > 25 else model.description
        
        print(f"{model.id:<20} {context:<10} {prompt_price:<12} {completion_price:<12} {description}")

def demo_serialization():
    """Démontre la sérialisation/désérialisation JSON."""
    print("\n=== Sérialisation et sauvegarde ===\n")
    
    # Créer une session avec quelques données
    session = Session(
        model="gpt-4",
        system="Assistant de démonstration",
        meta={"user_id": "demo_user", "session_type": "example"}
    )
    
    # Ajouter un tour simple
    user_msg = Message(role=MessageRole.USER, content="Test de sérialisation")
    assistant_msg = Message(role=MessageRole.ASSISTANT, content="Test réussi!")
    usage = Usage(prompt_tokens=10, completion_tokens=15, total_tokens=25)
    turn = Turn(messages=[user_msg, assistant_msg], usage=usage, cost_estimate=0.00075)
    
    session.add_turn(turn)
    
    # Sérialisation en JSON
    json_data = session.model_dump_json(indent=2)
    print("Session sérialisée en JSON:")
    print(json_data[:500] + "..." if len(json_data) > 500 else json_data)
    
    # Sauvegarde dans un fichier
    filename = "/Users/emi/Desktop/phemis/demo_session.json"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_data)
    print(f"\nSession sauvegardée dans: {filename}")
    
    # Rechargement depuis le fichier
    with open(filename, 'r', encoding='utf-8') as f:
        loaded_json = f.read()
    
    restored_session = Session.model_validate_json(loaded_json)
    print(f"Session rechargée - Modèle: {restored_session.model}")
    print(f"Nombre de tours: {len(restored_session.turns)}")
    print(f"Total tokens: {restored_session.usage_totals.total_tokens}")
    
    return restored_session

def main():
    """Lance toutes les démonstrations."""
    print("🤖 Démonstration des modèles Pydantic pour l'outil CLI LLM\n")
    
    # Démonstration principale
    session = demo_conversation()
    
    # Informations sur les modèles
    demo_model_info()
    
    # Sérialisation
    demo_serialization()
    
    print("\n" + "=" * 60)
    print("✅ Démonstration terminée avec succès!")
    print("📁 Fichier de session de démonstration créé: demo_session.json")

if __name__ == "__main__":
    main()