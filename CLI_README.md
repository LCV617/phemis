# LLM CLI - Documentation

## Vue d'ensemble

LLM CLI est un outil en ligne de commande pour interagir avec l'API OpenRouter. Il permet d'explorer les modèles disponibles, de gérer les sessions de conversation et d'effectuer des requêtes vers différents modèles de LLM.

## Installation

```bash
# Installation des dépendances
pip3 install typer rich requests pydantic tenacity

# Clonage et test du projet
git clone <repository>
cd phemis
python3 -m llm.cli.main --help
```

## Configuration

Avant d'utiliser le CLI, vous devez configurer votre clé API OpenRouter :

```bash
export OPENROUTER_API_KEY=your_api_key_here
```

Obtenez votre clé API sur : https://openrouter.ai/keys

## Utilisation

### Commandes principales

```bash
# Afficher l'aide générale
python3 -m llm.cli.main --help

# Afficher la version
python3 -m llm.cli.main --version

# Explorer les modèles disponibles
python3 -m llm.cli.main models --help
```

### Commande `models`

#### Lister tous les modèles

```bash
# Lister tous les modèles disponibles
python3 -m llm.cli.main models list

# Filtrer les modèles par nom
python3 -m llm.cli.main models list --filter gpt
python3 -m llm.cli.main models list --filter anthropic
python3 -m llm.cli.main models list --filter claude

# Afficher les détails complets de chaque modèle
python3 -m llm.cli.main models list --details
```

#### Obtenir des informations sur un modèle spécifique

```bash
# Informations détaillées sur un modèle
python3 -m llm.cli.main models info "openai/gpt-4o-mini"
python3 -m llm.cli.main models info "anthropic/claude-3-sonnet"
python3 -m llm.cli.main models info "google/gemini-pro"
```

### Exemples d'affichage

#### Liste des modèles

```
                         Available Models on OpenRouter                         
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Model ID                │ Context      │ Price In   │ Price Out   │ Description                                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
┃ anthropic/claude-3-sonnet │ 200k         │ $3.00/1M   │ $15.00/1M   │ Claude 3 Sonnet offers the ideal balance...     ┃
┃ openai/gpt-4o-mini      │ 128k         │ $0.15/1M   │ $0.60/1M    │ Latest GPT-4o mini model with improved...       ┃
└─────────────────────────┴──────────────┴────────────┴─────────────┴──────────────────────────────────────────────────┘

╭──────────────────────────────────────────────────────────────────────────────╮
│ ✓ 2 modèle(s) affiché(s) sur 47 total                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### Informations détaillées d'un modèle

```
╭─────────────────── Model Information: openai/gpt-4o-mini ────────────────────╮
│                                                                              │
│  Model ID: openai/gpt-4o-mini                                                │
│  Context Length: 128k                                                        │
│  Input Price: $0.015/1M                                                      │
│  Output Price: $0.600/1M                                                     │
│  Description:                                                                │
│  Latest GPT-4o mini model with improved efficiency and reasoning             │
│  capabilities                                                                │
│                                                                              │
│  Cost Estimates (per 1M tokens):                                             │
│    • Input: $0.015/1M                                                        │
│    • Output: $0.600/1M                                                       │
│                                                                              │
│  Typical Usage Costs:                                                        │
│    • Simple chat (1k in, 100 out): $0.0001                                   │
│    • Long document (10k in, 500 out): $0.0004                                │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Architecture du code

### Structure des fichiers

```
llm/
├── cli/
│   ├── __init__.py
│   ├── main.py          # Point d'entrée principal du CLI
│   └── models.py        # Commandes pour explorer les modèles
├── core/
│   ├── __init__.py
│   ├── provider_openrouter.py   # Client API OpenRouter
│   ├── schema.py               # Modèles de données Pydantic
│   └── utils.py                # Utilitaires diverses
```

### Fichiers créés

#### `/Users/emi/Desktop/phemis/llm/cli/main.py`

Application Typer principale avec :
- **Vérification AUTH** : Variable OPENROUTER_API_KEY obligatoire
- **Gestion erreurs globales** : Exception handler avec messages utilisateur clairs  
- **Version command** : `--version` pour afficher la version du package
- **Help amélioré** : Descriptions complètes des commandes
- **Architecture extensible** : Support pour les futures sous-commandes (chat, ask, sessions)

Fonctionnalités principales :
- Point d'entrée CLI avec `typer.Typer()`
- Gestion d'authentification centralisée
- Gestionnaire d'erreurs global avec panels Rich colorés
- Support des interruptions clavier (Ctrl+C)
- Messages d'erreur utilisateur-friendly

#### `/Users/emi/Desktop/phemis/llm/cli/models.py`

Sous-application pour gérer les modèles avec :

**Commande `list`** :
- Récupère tous les modèles via `provider_openrouter.list_models()`
- Affichage tableau Rich avec : ID, Context Length, Price In/Out, Description
- Option `--filter` pour filtrer par substring dans l'ID
- Option `--details` pour affichage étendu
- Tri alphabétique des résultats
- Gestion des prix manquants (afficher "N/A")
- Statistiques finales (nombre de modèles trouvés)

**Commande `info`** :
- Informations détaillées d'un modèle spécifique
- Calcul d'estimations de coût pour différents usages
- Suggestions de modèles similaires si non trouvé
- Panel Rich avec formatage professionnel

**Fonctionnalités techniques** :
- Formatage intelligent des prix (par million de tokens)
- Formatage des longueurs de contexte (128k, 200k, etc.)
- Troncature intelligente des descriptions
- Spinner de chargement avec `console.status()`
- Gestion complète des erreurs (auth, réseau, API)

## Gestion des erreurs

Le CLI gère plusieurs types d'erreurs :

1. **Erreurs d'authentification** : Clé API manquante ou invalide
2. **Erreurs réseau** : Problèmes de connexion à OpenRouter
3. **Erreurs API** : Codes d'erreur HTTP spécifiques
4. **Erreurs utilisateur** : Modèles non trouvés, filtres vides
5. **Interruptions** : Ctrl+C géré proprement

Chaque erreur est affichée dans un panel Rich coloré avec des suggestions de résolution.

## Tests

Un fichier de test complet est fourni (`test_cli.py`) qui simule toutes les fonctionnalités sans nécessiter de vraie clé API :

```bash
python3 test_cli.py
```

Le script teste :
- Affichage de la version
- Gestion des erreurs d'authentification  
- Liste des modèles avec et sans filtre
- Informations détaillées d'un modèle
- Gestion des modèles inexistants

## Développement futur

L'architecture est prête pour ajouter les commandes suivantes :

- `llm chat` : Sessions de chat interactives
- `llm ask` : Questions ponctuelles 
- `llm sessions` : Gestion des sessions sauvegardées

Chaque nouvelle commande peut être ajoutée comme sous-application Typer dans un fichier séparé et importée dans `main.py`.

## Compatibilité

- **Python** : 3.9+ (testé avec Python 3.9.6)
- **Dépendances** : typer, rich, requests, pydantic, tenacity
- **Plateforme** : Cross-platform (testé sur macOS)