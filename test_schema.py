#!/usr/bin/env python3
"""
Script de test pour valider tous les modèles Pydantic du fichier schema.py.
"""

from llm.core.schema import (
    Message, MessageRole, Usage, ModelInfo, Turn, Session, ChatConfig
)
from datetime import datetime
import json

def test_message():
    """Test du modèle Message."""
    print("Test Message...")
    
    # Test création normale
    msg = Message(role=MessageRole.USER, content="Hello world")
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello world"
    
    # Test avec enum en string
    msg2 = Message(role="assistant", content="Hi there!")
    assert msg2.role == MessageRole.ASSISTANT
    
    # Test validation erreur
    try:
        Message(role=MessageRole.USER, content="")
        assert False, "Should have failed"
    except ValueError:
        pass
    
    print("✓ Message tests passed")

def test_usage():
    """Test du modèle Usage."""
    print("Test Usage...")
    
    # Test création normale
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30
    
    # Test validation total incorrect
    try:
        Usage(prompt_tokens=10, completion_tokens=20, total_tokens=25)
        assert False, "Should have failed"
    except ValueError:
        pass
    
    # Test valeurs négatives
    try:
        Usage(prompt_tokens=-1, completion_tokens=20, total_tokens=19)
        assert False, "Should have failed"
    except ValueError:
        pass
    
    print("✓ Usage tests passed")

def test_model_info():
    """Test du modèle ModelInfo."""
    print("Test ModelInfo...")
    
    # Test création basique
    model = ModelInfo(id="gpt-4")
    assert model.id == "gpt-4"
    assert model.context_length is None
    
    # Test création complète
    model2 = ModelInfo(
        id="gpt-4",
        context_length=8192,
        pricing_prompt=0.03,
        pricing_completion=0.06,
        description="GPT-4 model"
    )
    assert model2.context_length == 8192
    assert model2.pricing_prompt == 0.03
    
    # Test ID vide
    try:
        ModelInfo(id="")
        assert False, "Should have failed"
    except ValueError:
        pass
    
    print("✓ ModelInfo tests passed")

def test_turn():
    """Test du modèle Turn."""
    print("Test Turn...")
    
    msg1 = Message(role=MessageRole.USER, content="Hello")
    msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there!")
    usage = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    
    # Test création basique
    turn = Turn(messages=[msg1, msg2])
    assert len(turn.messages) == 2
    
    # Test avec métadonnées
    turn2 = Turn(
        messages=[msg1, msg2],
        usage=usage,
        latency_ms=1500.0,
        cost_estimate=0.001
    )
    assert turn2.usage.total_tokens == 15
    assert turn2.latency_ms == 1500.0
    
    # Test messages vides
    try:
        Turn(messages=[])
        assert False, "Should have failed"
    except ValueError:
        pass
    
    # Test message système dans un turn (devrait échouer)
    system_msg = Message(role=MessageRole.SYSTEM, content="System prompt")
    try:
        Turn(messages=[system_msg, msg1])
        assert False, "Should have failed"
    except ValueError:
        pass
    
    print("✓ Turn tests passed")

def test_session():
    """Test du modèle Session."""
    print("Test Session...")
    
    # Test création basique
    session = Session(model="gpt-4")
    assert session.model == "gpt-4"
    assert session.schema_version == 1
    assert len(session.turns) == 0
    assert isinstance(session.created_at, datetime)
    
    # Test avec système
    session2 = Session(
        model="gpt-4",
        system="Tu es un assistant utile",
        meta={"user_id": "123"}
    )
    assert session2.system == "Tu es un assistant utile"
    assert session2.meta["user_id"] == "123"
    
    # Test ajout de tours
    msg1 = Message(role=MessageRole.USER, content="Hello")
    msg2 = Message(role=MessageRole.ASSISTANT, content="Hi!")
    usage = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    turn = Turn(messages=[msg1, msg2], usage=usage)
    
    session2.add_turn(turn)
    assert len(session2.turns) == 1
    assert session2.usage_totals.total_tokens == 15
    
    # Test get_all_messages
    all_messages = session2.get_all_messages()
    assert len(all_messages) == 3  # system + user + assistant
    assert all_messages[0].role == MessageRole.SYSTEM
    
    # Test calcul coût total
    turn_with_cost = Turn(
        messages=[msg1, msg2], 
        usage=usage,
        cost_estimate=0.002
    )
    session2.add_turn(turn_with_cost)
    total_cost = session2.calculate_total_cost()
    assert total_cost == 0.002
    
    print("✓ Session tests passed")

def test_chat_config():
    """Test du modèle ChatConfig."""
    print("Test ChatConfig...")
    
    # Test création basique
    config = ChatConfig(model="gpt-4")
    assert config.model == "gpt-4"
    assert config.system is None
    assert config.budget_max is None
    
    # Test création complète
    config2 = ChatConfig(
        model="gpt-4",
        system="Tu es un assistant utile",
        budget_max=10.0
    )
    assert config2.system == "Tu es un assistant utile"
    assert config2.budget_max == 10.0
    
    # Test conversion vers Session
    session = config2.to_session()
    assert session.model == "gpt-4"
    assert session.system == "Tu es un assistant utile"
    assert session.meta["budget_max"] == 10.0
    
    print("✓ ChatConfig tests passed")

def test_serialization():
    """Test de sérialisation JSON."""
    print("Test sérialisation JSON...")
    
    # Création d'une session complète
    session = Session(
        model="gpt-4",
        system="Tu es un assistant utile"
    )
    
    msg1 = Message(role=MessageRole.USER, content="Hello")
    msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there!")
    usage = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    turn = Turn(messages=[msg1, msg2], usage=usage, cost_estimate=0.001)
    
    session.add_turn(turn)
    
    # Test sérialisation
    json_data = session.model_dump_json()
    assert isinstance(json_data, str)
    
    # Test désérialisation
    session_restored = Session.model_validate_json(json_data)
    assert session_restored.model == session.model
    assert session_restored.system == session.system
    assert len(session_restored.turns) == len(session.turns)
    assert session_restored.usage_totals.total_tokens == session.usage_totals.total_tokens
    
    # Test avec datetime ISO
    data_dict = session.model_dump()
    assert isinstance(data_dict['created_at'], datetime)
    
    print("✓ Sérialisation tests passed")

def main():
    """Lance tous les tests."""
    print("=== Tests des modèles Pydantic ===\n")
    
    test_message()
    test_usage()
    test_model_info()
    test_turn()
    test_session()
    test_chat_config()
    test_serialization()
    
    print("\n=== Tous les tests sont passés avec succès! ===")

if __name__ == "__main__":
    main()