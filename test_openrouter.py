#!/usr/bin/env python3
"""
Tests pour le provider OpenRouter.

Tests unitaires et d'intégration pour vérifier le bon fonctionnement
du provider OpenRouter.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from llm.core import (
    OpenRouterProvider,
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    Message,
    MessageRole,
    Usage
)


class TestOpenRouterProvider:
    """Tests pour la classe OpenRouterProvider."""
    
    def test_init_with_api_key(self):
        """Test d'initialisation avec clé API explicite."""
        provider = OpenRouterProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.timeout == OpenRouterProvider.DEFAULT_TIMEOUT
    
    def test_init_from_env(self):
        """Test d'initialisation avec clé API depuis l'environnement."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}):
            provider = OpenRouterProvider()
            assert provider.api_key == "env-key"
    
    def test_init_no_api_key(self):
        """Test d'initialisation sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(OpenRouterAuthError):
                OpenRouterProvider()
    
    def test_get_headers(self):
        """Test de construction des headers."""
        provider = OpenRouterProvider(api_key="test-key")
        headers = provider._get_headers()
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
    
    def test_get_headers_with_extra(self):
        """Test de construction des headers avec headers supplémentaires."""
        provider = OpenRouterProvider(
            api_key="test-key",
            extra_headers={"HTTP-Referer": "https://example.com"}
        )
        headers = provider._get_headers({"X-Custom": "value"})
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["HTTP-Referer"] == "https://example.com"
        assert headers["X-Custom"] == "value"
    
    @patch('requests.Session.get')
    def test_list_models_success(self, mock_get):
        """Test de récupération des modèles avec succès."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "openai/gpt-4",
                    "context_length": 8192,
                    "description": "GPT-4 model",
                    "pricing": {
                        "prompt": "0.00003",
                        "completion": "0.00006"
                    }
                },
                {
                    "id": "anthropic/claude-3",
                    "context_length": 100000,
                    "description": "Claude 3 model",
                    "pricing": {
                        "prompt": "0.00001",
                        "completion": "0.00003"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        provider = OpenRouterProvider(api_key="test-key")
        models = provider.list_models()
        
        assert len(models) == 2
        assert models[0].id == "openai/gpt-4"
        assert models[0].context_length == 8192
        assert models[0].pricing_prompt == 0.00003
        assert models[0].pricing_completion == 0.00006
        assert models[1].id == "anthropic/claude-3"
    
    @patch('requests.Session.get')
    def test_list_models_auth_error(self, mock_get):
        """Test de gestion d'erreur d'authentification."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        provider = OpenRouterProvider(api_key="invalid-key")
        
        with pytest.raises(OpenRouterAuthError):
            provider.list_models()
    
    @patch('requests.Session.get')
    def test_list_models_rate_limit_error(self, mock_get):
        """Test de gestion d'erreur de limite de taux."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        provider = OpenRouterProvider(api_key="test-key")
        
        with pytest.raises(OpenRouterRateLimitError):
            provider.list_models()
    
    @patch('requests.Session.get')
    def test_list_models_server_error(self, mock_get):
        """Test de gestion d'erreur serveur."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        provider = OpenRouterProvider(api_key="test-key")
        
        with pytest.raises(OpenRouterServerError):
            provider.list_models()
    
    @patch('requests.Session.post')
    def test_chat_completion_sync(self, mock_post):
        """Test de complétion de chat synchrone."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Bonjour! Comment puis-je vous aider?"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }
        mock_post.return_value = mock_response
        
        provider = OpenRouterProvider(api_key="test-key")
        messages = [Message(role=MessageRole.USER, content="Bonjour")]
        
        response = provider.chat_completion(
            messages=messages,
            model="openai/gpt-3.5-turbo",
            stream=False
        )
        
        assert "choices" in response
        assert response["choices"][0]["message"]["content"] == "Bonjour! Comment puis-je vous aider?"
        assert response["usage"]["total_tokens"] == 25
    
    def test_estimate_cost(self):
        """Test d'estimation des coûts."""
        provider = OpenRouterProvider(api_key="test-key")
        
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        cost = provider.estimate_cost(
            usage=usage,
            pricing_prompt=0.00001,  # $0.00001 par token
            pricing_completion=0.00002  # $0.00002 par token
        )
        
        expected_cost = (100 * 0.00001) + (50 * 0.00002)  # 0.001 + 0.001 = 0.002
        assert cost == expected_cost
    
    def test_estimate_cost_no_pricing(self):
        """Test d'estimation des coûts sans données de prix."""
        provider = OpenRouterProvider(api_key="test-key")
        
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        cost = provider.estimate_cost(
            usage=usage,
            pricing_prompt=None,
            pricing_completion=0.00002
        )
        
        assert cost is None


def test_message_conversion():
    """Test de conversion des messages vers le format API."""
    messages = [
        Message(role=MessageRole.SYSTEM, content="Vous êtes un assistant IA."),
        Message(role=MessageRole.USER, content="Bonjour!"),
        Message(role=MessageRole.ASSISTANT, content="Bonjour! Comment allez-vous?")
    ]
    
    # Simuler la conversion comme dans chat_completion
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg.role.value,
            "content": msg.content
        })
    
    assert len(api_messages) == 3
    assert api_messages[0]["role"] == "system"
    assert api_messages[1]["role"] == "user"
    assert api_messages[2]["role"] == "assistant"


if __name__ == "__main__":
    # Exécuter les tests si le script est lancé directement
    pytest.main([__file__, "-v"])