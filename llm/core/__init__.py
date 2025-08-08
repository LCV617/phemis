"""
Module core pour l'outil CLI LLM.

Ce module contient les composants de base incluant les schémas de données
et les providers d'API.
"""

from .schema import (
    Message,
    MessageRole,
    Usage,
    ModelInfo,
    Turn,
    Session,
    ChatConfig
)

from .provider_openrouter import (
    OpenRouterProvider,
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterServerError
)

__all__ = [
    "Message",
    "MessageRole", 
    "Usage",
    "ModelInfo",
    "Turn",
    "Session",
    "ChatConfig",
    "OpenRouterProvider",
    "OpenRouterError",
    "OpenRouterAuthError",
    "OpenRouterRateLimitError",
    "OpenRouterServerError"
]