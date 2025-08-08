# Commande ASK - Documentation

La commande `llm ask` permet de poser une question unique à un modèle LLM et d'obtenir une réponse immédiate avec streaming en temps réel.

## Installation

Assurez-vous d'avoir installé les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

Définissez votre clé API OpenRouter :

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

## Usage de base

### Syntaxe

```bash
python -m llm.cli.ask "<question>" --model <MODEL_ID> [--system "<system_prompt>"] [--json]
```

### Paramètres

- `question` : Votre question (obligatoire)
- `--model` / `-m` : Identifiant du modèle à utiliser (obligatoire)
- `--system` / `-s` : Prompt système optionnel
- `--json` : Sortie en format JSON pour l'intégration dans des scripts

## Exemples d'utilisation

### 1. Question simple

```bash
python -m llm.cli.ask "What is 2+2?" --model openai/gpt-4o-mini
```

**Sortie :**
```
Question:
> What is 2+2?

Response:

2+2 equals 4.

────────────────────────────────────────
Model: openai/gpt-4o-mini | Tokens: 12→6 (18) | 1.23s | ~$0.0001
```

### 2. Avec prompt système

```bash
python -m llm.cli.ask "Explain quantum physics" --model openai/gpt-4o-mini --system "You are a physics teacher for high school students"
```

### 3. Sortie JSON

```bash
python -m llm.cli.ask "What is AI?" --model openai/gpt-4o-mini --json
```

**Sortie :**
```json
{
  "question": "What is AI?",
  "response": "Artificial Intelligence (AI) refers to...",
  "model": "openai/gpt-4o-mini",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 120,
    "total_tokens": 135
  },
  "latency_ms": 1234.5,
  "estimated_cost_usd": 0.0045,
  "system": null
}
```

### 4. Question longue avec échappement

```bash
python -m llm.cli.ask "Can you write a Python function to calculate fibonacci numbers and explain how it works?" --model anthropic/claude-3-haiku
```

## Modèles supportés

La commande supporte tous les modèles disponibles via OpenRouter. Exemples populaires :

- `openai/gpt-4o-mini` - Modèle rapide et économique
- `openai/gpt-4o` - Modèle le plus capable d'OpenAI
- `anthropic/claude-3-haiku` - Modèle rapide d'Anthropic
- `anthropic/claude-3.5-sonnet` - Modèle équilibré d'Anthropic
- `meta-llama/llama-3.1-70b-instruct` - Modèle open source

## Fonctionnalités

### Mode Streaming

Par défaut, la réponse s'affiche en temps réel au fur et à mesure de sa génération, offrant une expérience interactive.

### Métadonnées complètes

Après chaque réponse, vous obtenez :
- Modèle utilisé
- Nombre de tokens (prompt → completion)
- Temps de réponse
- Coût estimé

### Gestion d'erreurs

La commande gère intelligemment les erreurs avec des messages d'aide :

```bash
# Modèle invalide
Error: Model 'invalid-model' not found
💡 Tip: Use `llm models list` to see available models

# Problème d'authentification
Error: Authentication error (401): Check your OpenRouter API key
💡 Tip: Check your OPENROUTER_API_KEY environment variable

# Rate limiting
Error: Rate limit exceeded (429): Too many requests
💡 Tip: Wait a moment and try again
```

## Intégration dans des scripts

### Bash

```bash
#!/bin/bash

# Obtenir une réponse JSON
RESPONSE=$(python -m llm.cli.ask "What's the current date format?" --model openai/gpt-4o-mini --json)

# Parser avec jq
ANSWER=$(echo "$RESPONSE" | jq -r '.response')
COST=$(echo "$RESPONSE" | jq -r '.estimated_cost_usd')

echo "Answer: $ANSWER"
echo "Cost: \$$COST"
```

### Python

```python
import subprocess
import json

def ask_llm(question, model="openai/gpt-4o-mini", system=None):
    cmd = [
        "python", "-m", "llm.cli.ask",
        question,
        "--model", model,
        "--json"
    ]
    
    if system:
        cmd.extend(["--system", system])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

# Usage
try:
    response = ask_llm("Explain machine learning in one paragraph")
    print(f"Response: {response['response']}")
    print(f"Tokens used: {response['usage']['total_tokens']}")
    print(f"Cost: ${response['estimated_cost_usd']:.4f}")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
```

### Node.js

```javascript
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

async function askLLM(question, model = 'openai/gpt-4o-mini') {
    const cmd = `python -m llm.cli.ask "${question}" --model ${model} --json`;
    
    try {
        const { stdout } = await execAsync(cmd);
        return JSON.parse(stdout);
    } catch (error) {
        throw new Error(`LLM Error: ${error.message}`);
    }
}

// Usage
askLLM("What is Node.js?")
    .then(response => {
        console.log('Response:', response.response);
        console.log('Cost: $' + response.estimated_cost_usd.toFixed(4));
    })
    .catch(console.error);
```

## Cas d'usage avancés

### 1. Processing pipeline

```bash
# Traitement en chaîne
python -m llm.cli.ask "Summarize: $(cat article.txt)" --model anthropic/claude-3-haiku --json | jq -r '.response' > summary.txt
```

### 2. Interactive scripting

```bash
#!/bin/bash
echo "AI Assistant - Ask anything!"
while true; do
    read -p "Question: " question
    if [ "$question" = "exit" ]; then
        break
    fi
    python -m llm.cli.ask "$question" --model openai/gpt-4o-mini
    echo
done
```

### 3. Batch processing

```python
import json
from concurrent.futures import ThreadPoolExecutor

questions = [
    "What is Python?",
    "What is JavaScript?",
    "What is Go?"
]

def process_question(question):
    # Use the ask command programmatically
    result = ask_llm(question)
    return {
        'question': question,
        'answer': result['response'],
        'cost': result['estimated_cost_usd']
    }

# Process in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_question, questions))

total_cost = sum(r['cost'] for r in results)
print(f"Processed {len(results)} questions for ${total_cost:.4f}")
```

## Performance et coûts

### Optimisation des coûts

1. **Choisir le bon modèle** : Utilisez `openai/gpt-4o-mini` pour des tâches simples
2. **Questions précises** : Réduisez les tokens inutiles
3. **Prompt système efficace** : Un bon prompt système peut réduire les tokens de réponse

### Modèles recommandés par usage

| Usage | Modèle recommandé | Coût relatif |
|-------|------------------|--------------|
| Questions simples | `openai/gpt-4o-mini` | Très bas |
| Analyse de code | `anthropic/claude-3.5-sonnet` | Moyen |
| Tâches complexes | `openai/gpt-4o` | Élevé |
| Traduction | `openai/gpt-4o-mini` | Très bas |
| Créativité | `anthropic/claude-3.5-sonnet` | Moyen |

## Dépannage

### Problèmes courants

1. **"Module not found"**
   ```bash
   # S'assurer d'être dans le bon répertoire
   cd /path/to/phemis
   python -m llm.cli.ask "test" --model openai/gpt-4o-mini
   ```

2. **"Authentication error"**
   ```bash
   # Vérifier la clé API
   echo $OPENROUTER_API_KEY
   export OPENROUTER_API_KEY="your-key-here"
   ```

3. **"Rate limit exceeded"**
   - Attendre quelques secondes entre les requêtes
   - Utiliser un modèle moins demandé

4. **"Model not found"**
   - Vérifier l'identifiant exact du modèle
   - Certains modèles peuvent être temporairement indisponibles

### Debug mode

Pour plus d'informations de débogage, vous pouvez examiner les réponses en mode verbose :

```python
# Dans example_ask_usage.py
export PYTHONPATH=.
python example_ask_usage.py
```

## Contributing

Pour étendre la commande ask :

1. Modifier `/Users/emi/Desktop/phemis/llm/cli/ask.py`
2. Ajouter des tests dans `test_ask.py`
3. Mettre à jour cette documentation

## Licence

Ce projet fait partie du framework LLM CLI sous licence MIT.