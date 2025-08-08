# OpenRouter Provider

Ce document décrit l'implémentation et l'utilisation du provider OpenRouter pour l'outil CLI LLM.

## Fonctionnalités implémentées

### ✅ Liste des modèles
- **Endpoint**: `GET /api/v1/models`
- **Fonction**: `list_models() -> List[ModelInfo]`
- Parse automatiquement les informations des modèles (ID, contexte, prix, description)
- Gestion complète des erreurs HTTP

### ✅ Complétion de chat
- **Endpoint**: `POST /api/v1/chat/completions`  
- **Fonction**: `chat_completion(messages, model, stream=False, extra_headers=None, **kwargs)`
- Support **streaming** et **non-streaming**
- Parser SSE pour les réponses streaming
- Gestion des événements `[DONE]` et filtrage des commentaires OpenRouter

### ✅ Authentification
- Header `Authorization: Bearer {OPENROUTER_API_KEY}`
- Support clé API via environnement ou paramètre constructeur
- Headers optionnels personnalisables (HTTP-Referer, X-Title, etc.)

### ✅ Gestion d'erreurs robuste
- **401**: `OpenRouterAuthError` - Erreur d'authentification
- **429**: `OpenRouterRateLimitError` - Limite de taux
- **5xx**: `OpenRouterServerError` - Erreurs serveur
- **Timeout**: Configuration personnalisable (défaut: 60s)
- **Retry automatique**: 3 tentatives avec backoff exponentiel

### ✅ Estimation des coûts
- Calcul basé sur l'usage des tokens et les prix des modèles
- Support des métriques `Usage` de Pydantic

## Configuration

### Variables d'environnement
```bash
export OPENROUTER_API_KEY="votre_clé_api"
```

### Installation des dépendances
```bash
pip install requests>=2.25.0 pydantic>=2.0.0
```

## Exemples d'utilisation

### 1. Initialisation
```python
from llm.core import OpenRouterProvider

# Avec clé API depuis l'environnement
provider = OpenRouterProvider()

# Ou avec clé API explicite
provider = OpenRouterProvider(api_key="votre_clé")

# Avec headers personnalisés
provider = OpenRouterProvider(
    extra_headers={
        "HTTP-Referer": "https://votre-site.com",
        "X-Title": "Mon App LLM"
    }
)
```

### 2. Liste des modèles
```python
try:
    models = provider.list_models()
    for model in models:
        print(f"Modèle: {model.id}")
        print(f"Contexte: {model.context_length} tokens")
        print(f"Prix: ${model.pricing_prompt} (prompt), ${model.pricing_completion} (completion)")
        print()
except OpenRouterError as e:
    print(f"Erreur: {e}")
```

### 3. Chat completion synchrone
```python
from llm.core import Message, MessageRole

messages = [
    Message(role=MessageRole.USER, content="Bonjour!")
]

response = provider.chat_completion(
    messages=messages,
    model="openai/gpt-3.5-turbo",
    stream=False
)

print(response["choices"][0]["message"]["content"])
```

### 4. Chat completion streaming
```python
messages = [
    Message(role=MessageRole.USER, content="Raconte-moi une histoire...")
]

stream = provider.chat_completion(
    messages=messages,
    model="openai/gpt-3.5-turbo", 
    stream=True
)

for chunk in stream:
    if "choices" in chunk:
        delta = chunk["choices"][0].get("delta", {})
        if "content" in delta:
            print(delta["content"], end="", flush=True)
```

### 5. Estimation des coûts
```python
from llm.core import Usage

usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

cost = provider.estimate_cost(
    usage=usage,
    pricing_prompt=0.00001,  # Prix par token prompt
    pricing_completion=0.00002  # Prix par token completion  
)

print(f"Coût estimé: ${cost:.4f}")
```

## Gestion d'erreurs

```python
from llm.core import (
    OpenRouterError,
    OpenRouterAuthError, 
    OpenRouterRateLimitError,
    OpenRouterServerError
)

try:
    models = provider.list_models()
except OpenRouterAuthError:
    print("Clé API invalide ou manquante")
except OpenRouterRateLimitError:
    print("Limite de taux atteinte - attendez avant de réessayer")
except OpenRouterServerError:
    print("Problème serveur OpenRouter")
except OpenRouterError as e:
    print(f"Autre erreur: {e}")
```

## Architecture

### Classes principales
- `OpenRouterProvider`: Client principal pour l'API OpenRouter
- `OpenRouterError`: Classe d'exception de base
- `OpenRouterAuthError`: Erreurs d'authentification (401)
- `OpenRouterRateLimitError`: Erreurs de limite de taux (429)  
- `OpenRouterServerError`: Erreurs serveur (5xx)

### Schémas Pydantic utilisés
- `ModelInfo`: Informations des modèles
- `Message`: Messages de conversation 
- `Usage`: Métriques d'usage des tokens

### Configuration API OpenRouter
- **Base URL**: `https://openrouter.ai/api/v1`
- **Content-Type**: `application/json`
- **Timeout par défaut**: 60 secondes
- **Retry automatique**: 3 tentatives pour 429, 5xx

## Tests

Exécuter les tests unitaires:
```bash
python -m pytest test_openrouter.py -v
```

Exécuter l'exemple d'utilisation:
```bash
python example_openrouter.py
```

## Limites et considérations

1. **Streaming SSE**: Ignore les commentaires "OPENROUTER PROCESSING" comme spécifié
2. **Pricing**: Conversion automatique string → float pour les prix
3. **Headers**: Support complet des headers personnalisés pour l'authentification de domaine
4. **Timeouts**: Configurable mais avec des valeurs raisonnables par défaut
5. **Retry**: Stratégie conservative pour éviter de surcharger l'API

Cette implémentation respecte les meilleures pratiques et offre une interface robuste pour interagir avec l'API OpenRouter.