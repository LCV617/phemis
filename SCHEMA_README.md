# Schémas Pydantic pour l'outil CLI LLM

Ce document décrit les modèles Pydantic utilisés par l'outil CLI LLM, définis dans `/Users/emi/Desktop/phemis/llm/core/schema.py`.

## Vue d'ensemble

Les modèles Pydantic fournissent une validation de données robuste et une sérialisation JSON automatique pour tous les aspects de l'application LLM.

## Modèles disponibles

### 1. Message
Représente un message individuel dans une conversation.

```python
from llm.core.schema import Message, MessageRole

msg = Message(role=MessageRole.USER, content="Hello world")
```

**Champs:**
- `role`: Role du message (user/assistant/system)
- `content`: Contenu textuel du message (non vide)

### 2. Usage
Métrique d'utilisation des tokens pour un appel API.

```python
from llm.core.schema import Usage

usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
```

**Champs:**
- `prompt_tokens`: Nombre de tokens dans le prompt (≥0)
- `completion_tokens`: Nombre de tokens dans la réponse (≥0) 
- `total_tokens`: Total des tokens (doit égaler prompt + completion)

**Validation:** Le total des tokens est automatiquement validé.

### 3. ModelInfo
Informations sur un modèle LLM.

```python
from llm.core.schema import ModelInfo

model = ModelInfo(
    id="gpt-4",
    context_length=8192,
    pricing_prompt=0.03,
    pricing_completion=0.06,
    description="Modèle GPT-4"
)
```

**Champs:**
- `id`: Identifiant unique du modèle (requis, non vide)
- `context_length`: Longueur maximale du contexte (optionnel)
- `pricing_prompt`: Prix par token de prompt en USD (optionnel)
- `pricing_completion`: Prix par token de completion en USD (optionnel)
- `description`: Description du modèle (optionnel)

### 4. Turn
Représente un tour de conversation (typiquement user + assistant).

```python
from llm.core.schema import Turn, Message, Usage, MessageRole

messages = [
    Message(role=MessageRole.USER, content="Hello"),
    Message(role=MessageRole.ASSISTANT, content="Hi there!")
]
usage = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15)

turn = Turn(
    messages=messages,
    usage=usage,
    latency_ms=1500.0,
    cost_estimate=0.001
)
```

**Champs:**
- `messages`: Liste des messages (min. 1 message)
- `usage`: Métriques d'usage (optionnel)
- `latency_ms`: Latence de réponse en ms (optionnel)
- `cost_estimate`: Estimation du coût en USD (optionnel)

**Validation:** Les messages système ne sont pas autorisés dans un tour.

### 5. Session
Session de conversation complète avec historique et métadonnées.

```python
from llm.core.schema import Session, Turn

session = Session(
    model="gpt-4",
    system="Tu es un assistant utile",
    meta={"user_id": "123"}
)

# Ajouter un tour
session.add_turn(turn)

# Obtenir tous les messages dans l'ordre
all_messages = session.get_all_messages()

# Calculer le coût total
total_cost = session.calculate_total_cost()
```

**Champs:**
- `schema_version`: Version du schéma (défaut: 1)
- `created_at`: Date de création (ISO 8601)
- `model`: Modèle LLM utilisé (requis)
- `system`: Message système (optionnel)
- `turns`: Liste des tours de conversation
- `usage_totals`: Usage cumulé total (calculé automatiquement)
- `meta`: Métadonnées diverses (dict)

**Méthodes utiles:**
- `add_turn(turn)`: Ajoute un tour et met à jour les totaux
- `get_all_messages()`: Retourne tous les messages (système + tours)
- `calculate_total_cost()`: Calcule le coût total estimé

### 6. ChatConfig
Configuration pour une session de chat.

```python
from llm.core.schema import ChatConfig

config = ChatConfig(
    model="gpt-4",
    system="Tu es un expert Python",
    budget_max=10.0
)

# Convertir en session
session = config.to_session()
```

**Champs:**
- `model`: Modèle LLM à utiliser (requis)
- `system`: Message système (optionnel)
- `budget_max`: Budget maximum en USD (optionnel)

**Méthodes:**
- `to_session()`: Créer une nouvelle session depuis la config

## Sérialisation JSON

Tous les modèles supportent la sérialisation/désérialisation JSON automatique :

```python
# Sérialisation
json_data = session.model_dump_json(indent=2)

# Désérialisation
session_restored = Session.model_validate_json(json_data)

# Sauvegarde dans un fichier
with open("session.json", "w") as f:
    f.write(session.model_dump_json(indent=2))

# Chargement depuis un fichier
with open("session.json", "r") as f:
    session = Session.model_validate_json(f.read())
```

## Validation des données

Les modèles incluent une validation complète :

- **Messages**: Contenu non vide
- **Usage**: Tokens positifs, total correct
- **ModelInfo**: ID non vide
- **Turn**: Au moins 1 message, pas de messages système
- **Session**: Modèle non vide, datetime ISO 8601
- **ChatConfig**: Modèle non vide

## Exemples d'usage

Voir les fichiers suivants pour des exemples complets :
- `/Users/emi/Desktop/phemis/example_usage.py` - Démonstration complète
- `/Users/emi/Desktop/phemis/test_schema.py` - Tests de validation
- `/Users/emi/Desktop/phemis/demo_session.json` - Exemple de session sérialisée

## Installation des dépendances

```bash
pip install -r requirements.txt
```

Les dépendances requises sont :
- `pydantic>=2.0.0` - Validation des données
- `python-dateutil>=2.8.0` - Parsing des dates

## Tests

Pour exécuter les tests de validation :

```bash
python3 test_schema.py
```

Pour voir la démonstration complète :

```bash
python3 example_usage.py
```