# 📖 Commands Reference

Complete reference for all LLM CLI commands with parameters, examples, and outputs.

## Table of Contents

- [Global Options](#global-options)
- [llm ask](#llm-ask)
- [llm chat](#llm-chat)
- [llm models](#llm-models)
- [llm sessions](#llm-sessions)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)

## Global Options

Available for all commands:

| Option | Description | Example |
|--------|-------------|---------|
| `--help` | Show help message | `llm --help` |
| `--version` | Show version and exit | `llm --version` |

```bash
# Show version
$ llm --version
llm-cli version 0.1.0

# Global help
$ llm --help
Usage: llm [OPTIONS] COMMAND [ARGS]...

  CLI tool for interacting with OpenRouter API.
  
  Before using this tool, make sure to set your OpenRouter API key:
  export OPENROUTER_API_KEY=your_api_key_here

Options:
  --version   Show version and exit
  --help      Show this message and exit.

Commands:
  ask       Ask a single question to an LLM
  chat      Start interactive chat sessions  
  models    Manage and explore available models
  sessions  Manage conversation sessions
```

## llm ask

Ask a single question to an LLM and get an immediate response.

### Syntax

```bash
llm ask <question> --model <MODEL_ID> [OPTIONS]
```

### Parameters

| Parameter | Required | Type | Description | Default |
|-----------|----------|------|-------------|---------|
| `question` | ✅ Yes | string | Your question | - |
| `--model`, `-m` | ✅ Yes | string | Model ID to use | - |
| `--system`, `-s` | ❌ No | string | System prompt | None |
| `--json` | ❌ No | flag | Output in JSON format | False |

### Examples

#### Basic Question

```bash
$ llm ask "What is machine learning?" --model openai/gpt-4o-mini

Question:
> What is machine learning?

Response:

Machine learning is a subset of artificial intelligence (AI) that focuses on developing algorithms and statistical models that enable computers to learn and make decisions or predictions without being explicitly programmed for each specific task.

Key concepts include:
- **Training Data**: Large datasets used to teach the model
- **Algorithms**: Mathematical procedures that find patterns
- **Models**: The trained system that can make predictions
- **Features**: Input variables used for prediction

────────────────────────────────────────
Model: openai/gpt-4o-mini | Tokens: 18→127 (145) | 1.45s | ~$0.0023
```

#### With System Prompt

```bash
$ llm ask "Explain variables" \
  --model anthropic/claude-3-haiku \
  --system "You are a programming teacher for absolute beginners"

Question:
> Explain variables

Response:

Think of variables like labeled boxes or containers! 📦

Just like you might have a box labeled "Toys" to store your toys, in programming we have variables to store information.

**What is a variable?**
A variable is a name we give to a piece of data so we can use it later.

**Simple example:**
```
name = "Alex"
age = 25
```

Here:
- `name` is a variable that stores the text "Alex"  
- `age` is a variable that stores the number 25

**Why use variables?**
- We can refer to the data easily: "Hello " + name
- We can change the value: age = age + 1
- We can reuse the same data multiple times

Think of it like having a nickname for something - instead of saying "that tall person with brown hair" every time, you just say "Sarah"!

────────────────────────────────────────
Model: anthropic/claude-3-haiku | Tokens: 25→156 (181) | 2.1s | ~$0.0004
```

#### JSON Output

```bash
$ llm ask "What is 2+2?" --model openai/gpt-4o-mini --json

{
  "question": "What is 2+2?",
  "response": "2+2 equals 4.",
  "model": "openai/gpt-4o-mini",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 6,
    "total_tokens": 18
  },
  "latency_ms": 0,
  "estimated_cost_usd": 0.0001,
  "system": null
}
```

#### Long Question

```bash
$ llm ask "Can you write a Python function that calculates the factorial of a number using recursion, include error handling for negative numbers, and explain how it works step by step?" --model anthropic/claude-3.5-sonnet

# Response will include complete code with explanation...
```

### Error Examples

#### Invalid Model

```bash
$ llm ask "test" --model invalid-model

Error: Model 'invalid-model' not found
💡 Tip: Use `llm models list` to see available models
```

#### Authentication Error

```bash
$ llm ask "test" --model openai/gpt-4o-mini
# (with invalid API key)

Error: Authentication failed (401): Invalid API key
💡 Tip: Check your OPENROUTER_API_KEY environment variable
```

#### Rate Limiting

```bash
$ llm ask "test" --model openai/gpt-4o-mini

Error: Rate limit exceeded (429): Too many requests
💡 Tip: Wait a moment and try again
```

## llm chat

Start an interactive conversation with an LLM model.

### Syntax

```bash
llm chat --model <MODEL_ID> [OPTIONS]
```

### Parameters

| Parameter | Required | Type | Description | Default |
|-----------|----------|------|-------------|---------|
| `--model`, `-m` | ✅ Yes | string | Model ID to use | - |
| `--system`, `-s` | ❌ No | string | System prompt | None |
| `--budget`, `-b` | ❌ No | float | Budget limit in USD | Unlimited |
| `--resume`, `-r` | ❌ No | string | Path to session file to resume | - |
| `--save-dir` | ❌ No | string | Directory to save sessions | `./runs` |

### Interactive Commands

While in chat mode, use these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `:help` | Show available commands | `:help` |
| `:models` | List available models | `:models` |
| `:switch <model>` | Switch to different model | `:switch openai/gpt-4o` |
| `:system <prompt>` | Set system prompt | `:system You are a Python expert` |
| `:budget <amount>` | Set budget limit | `:budget 1.50` |
| `:cost` | Show session cost summary | `:cost` |
| `:save` | Save current session | `:save` |
| `:load <file>` | Load session from file | `:load session.json` |
| `:reset` | Clear conversation history | `:reset` |
| `:history` | Show conversation history | `:history` |
| `:export <format>` | Export session (json/txt) | `:export json` |
| `:exit` | End chat session | `:exit` |

### Examples

#### Basic Chat

```bash
$ llm chat --model openai/gpt-4o-mini

🤖 Starting chat with openai/gpt-4o-mini
💰 Budget: Unlimited | Type ':help' for commands

You: Hello! What can you help me with?

Assistant: Hello! I'm here to help with a wide variety of tasks. I can assist you with:

• **Writing and editing** - Essays, emails, creative content
• **Programming** - Code writing, debugging, explanations
• **Analysis** - Data interpretation, research, problem-solving
• **Learning** - Explanations of concepts, tutoring, Q&A
• **Creative projects** - Brainstorming, storytelling, planning
• **General conversation** - Questions, discussions, advice

What would you like to work on today?

────────────────────────────────────────
Tokens: 12→87 (99) | 1.3s | ~$0.0015
Session cost: $0.0015 | Budget remaining: Unlimited

You: Can you help me debug a Python function?

Assistant: Absolutely! I'd be happy to help debug your Python function. Please share:

1. **The code** - Paste your function here
2. **The problem** - What's not working as expected?
3. **Error messages** - Any error output you're seeing
4. **Expected behavior** - What should it do?

The more details you provide, the better I can help you fix it!

────────────────────────────────────────
Tokens: 25→65 (90) | 0.9s | ~$0.0014
Session cost: $0.0029 | Budget remaining: Unlimited

You: :save
💾 Session saved to ./runs/session_20240108_143022.json

You: :exit
👋 Chat ended. Total cost: $0.0029
```

#### Chat with Budget

```bash
$ llm chat --model openai/gpt-4o --budget 0.50

🤖 Starting chat with openai/gpt-4o
💰 Budget: $0.50 | Type ':help' for commands

You: Explain quantum computing in detail

Assistant: [Detailed response about quantum computing...]

────────────────────────────────────────
Tokens: 15→845 (860) | 3.2s | ~$0.0473
Session cost: $0.0473 | Budget remaining: $0.4527

You: Continue with quantum algorithms

Assistant: [Response about quantum algorithms...]

────────────────────────────────────────
Tokens: 25→632 (657) | 2.8s | ~$0.0361
Session cost: $0.0834 | Budget remaining: $0.4166
```

#### Resume Session

```bash
$ llm chat --resume ./runs/session_20240108_143022.json

🔄 Resuming session with openai/gpt-4o-mini
📊 Previous conversation: 5 turns, 847 tokens, $0.0127
💰 Budget: Unlimited | Type ':help' for commands

[Previous conversation context loaded]

You: Let's continue where we left off...
```

#### Using Interactive Commands

```bash
You: :help

📋 Available Chat Commands:

🤖 Model Management:
  :models                 - List available models
  :switch <model>         - Switch to different model
  
⚙️  Configuration:
  :system <prompt>        - Set system prompt
  :budget <amount>        - Set budget limit ($)
  
💾 Session Management:
  :save                   - Save current session
  :load <file>           - Load session from file
  :reset                 - Clear conversation history
  :history               - Show conversation summary
  
📊 Information:
  :cost                  - Show cost breakdown
  :export <format>       - Export session (json/txt)
  
🚪 Exit:
  :exit                  - End chat session

You: :switch anthropic/claude-3-haiku
🔄 Switched to model: anthropic/claude-3-haiku
💰 Budget: Unlimited | Session cost so far: $0.0029

You: :budget 2.00
💰 Budget set to $2.00 (remaining: $1.9971)

You: :cost

💰 Session Cost Breakdown:

Turn 1: $0.0015 (12→87 tokens)
Turn 2: $0.0014 (25→65 tokens)

Total Cost: $0.0029
Budget Remaining: $1.9971
Model: anthropic/claude-3-haiku
```

## llm models

Explore and get information about available models.

### Subcommands

| Subcommand | Description | Usage |
|------------|-------------|-------|
| `list` | List all available models | `llm models list` |
| `info` | Get detailed model information | `llm models info <MODEL_ID>` |

### llm models list

List and filter available models.

#### Syntax

```bash
llm models list [OPTIONS]
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|----------|
| `--filter`, `-f` | string | Filter models by substring | None |
| `--details`, `-d` | flag | Show detailed information | False |

#### Examples

##### Basic Model List

```bash
$ llm models list

                         Available Models on OpenRouter                         
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Model ID                │ Context      │ Price In   │ Price Out   │ Description                                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ anthropic/claude-3-haiku │ 200k         │ $0.25/1M   │ $1.25/1M    │ Fast and economical model for simple tasks      │
│ openai/gpt-4o-mini      │ 128k         │ $0.15/1M   │ $0.60/1M    │ Most cost-effective small model                 │
│ anthropic/claude-3-sonnet│ 200k         │ $3.00/1M   │ $15.00/1M   │ Balanced performance and capability              │
│ openai/gpt-4o           │ 128k         │ $5.00/1M   │ $15.00/1M   │ Most capable OpenAI model                       │
└─────────────────────────┴──────────────┴────────────┴─────────────┴──────────────────────────────────────────────────┘

╭──────────────────────────────────────────────────────────────────────────────╮
│ ✓ 4 model(s) displayed out of 127 total                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### Filter by Provider

```bash
$ llm models list --filter anthropic

                    Available Models on OpenRouter                     
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Model ID                     │ Context      │ Price In   │ Price Out   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ anthropic/claude-3-haiku     │ 200k         │ $0.25/1M   │ $1.25/1M    │
│ anthropic/claude-3-sonnet    │ 200k         │ $3.00/1M   │ $15.00/1M   │
│ anthropic/claude-3.5-sonnet  │ 200k         │ $3.00/1M   │ $15.00/1M   │
│ anthropic/claude-3-opus      │ 200k         │ $15.00/1M  │ $75.00/1M   │
└──────────────────────────────┴──────────────┴────────────┴─────────────┘

╭──────────────────────────────────────────────────────────────────────────────╮
│ ✓ 4 model(s) displayed (filtered on 'anthropic') out of 127 total          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### Detailed View

```bash
$ llm models list --filter gpt-4o-mini --details

╭─────────────────────────────── Model 1/1 ───────────────────────────────────╮
│                                                                              │
│ ID: openai/gpt-4o-mini                                                      │
│ Context: 128k                                                               │
│ Price In: $0.15/1M                                                         │
│ Price Out: $0.60/1M                                                        │
│ Description:                                                                │
│ OpenAI's most cost-effective small model. GPT-4o mini is OpenAI's most     │
│ cost-efficient small model that's smarter and cheaper than GPT-3.5 Turbo, │
│ and has vision capabilities. The model has 128K context and an October     │
│ 2023 knowledge cutoff.                                                     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────╮
│ ✓ 1 model(s) displayed (filtered on 'gpt-4o-mini') out of 127 total       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### llm models info

Get detailed information about a specific model.

#### Syntax

```bash
llm models info <MODEL_ID>
```

#### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `model_id` | ✅ Yes | string | Exact model identifier |

#### Examples

##### Detailed Model Information

```bash
$ llm models info openai/gpt-4o-mini

╭─────────────────── Model Information: openai/gpt-4o-mini ───────────────────╮
│                                                                              │
│  Model ID: openai/gpt-4o-mini                                              │
│  Context Length: 128k                                                      │
│  Input Price: $0.150/1M                                                    │
│  Output Price: $0.600/1M                                                   │
│  Description:                                                               │
│  OpenAI's most cost-effective small model. GPT-4o mini is OpenAI's most   │
│  cost-efficient small model that's smarter and cheaper than GPT-3.5 Turbo,│
│  and has vision capabilities. The model has 128K context and an October   │
│  2023 knowledge cutoff.                                                    │
│                                                                              │
│  Cost Estimates (per 1M tokens):                                           │
│    • Input: $0.150/1M                                                      │
│    • Output: $0.600/1M                                                     │
│                                                                              │
│  Typical Usage Costs:                                                       │
│    • Simple chat (1k in, 100 out): $0.0001                                │
│    • Long document (10k in, 500 out): $0.0004                             │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### Model Not Found

```bash
$ llm models info nonexistent-model

╭─────────────────────────── Model not found ────────────────────────────────╮
│ Model 'nonexistent-model' not found                                         │
│                                                                              │
│ Models similar found:                                                        │
│   • openai/gpt-4o-mini                                                     │
│   • anthropic/claude-3-sonnet                                              │
│   • meta-llama/llama-3.1-70b-instruct                                     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## llm sessions

Manage saved conversation sessions.

### Subcommands

| Subcommand | Description | Usage |
|------------|-------------|-------|
| `list` | List all saved sessions | `llm sessions list` |
| `show` | Show detailed session information | `llm sessions show <PATH>` |
| `resume` | Resume a saved session | `llm sessions resume <PATH>` |

### llm sessions list

List all saved sessions with summary information.

#### Syntax

```bash
llm sessions list [OPTIONS]
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|----------|
| `--dir`, `-d` | string | Sessions directory path | `./runs` |

#### Example

```bash
$ llm sessions list

                                Sessions (3 found)                                
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Filename                         │ Date            │ Model                   │ Turns │ Tokens  │ Est. Cost  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ session_20240108_143022.json     │ 2024-01-08 14:30│ openai/gpt-4o-mini     │     5 │   1,247 │ $0.0189    │
│ session_20240108_151445.json     │ 2024-01-08 15:14│ anthropic/claude-3-haiku│     3 │     847 │ $0.0034    │
│ session_20240107_203015.json     │ 2024-01-07 20:30│ openai/gpt-4o          │     8 │   2,156 │ $0.1234    │
└──────────────────────────────────┴─────────────────┴─────────────────────────┴───────┴─────────┴────────────┘

Use 'llm sessions show <filename>' for more details
```

### llm sessions show

Show detailed information about a specific session.

#### Syntax

```bash
llm sessions show <SESSION_PATH>
```

#### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `session_path` | ✅ Yes | string | Path to session JSON file |

#### Example

```bash
$ llm sessions show ./runs/session_20240108_143022.json

Session: session_20240108_143022.json

╭─────────────────────────── Session Information ────────────────────────────╮
│ Model: openai/gpt-4o-mini                                                   │
│ Created: 2024-01-08 14:30:22                                               │
│ System: You are a helpful programming assistant                             │
│ Turns: 5                                                                    │
│ Total tokens: 1,247 (prompt: 678, completion: 569)                        │
│ Estimated cost: $0.0189                                                     │
│ Avg latency: 1.45s                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────── 💬 First Exchange ──────────────────────────────╮
│                                                                              │
│ USER: Can you help me debug a Python function that's supposed to calculate  │
│ fibonacci numbers recursively?                                               │
│                                                                              │
│ ASSISTANT: I'd be happy to help you debug your Fibonacci function! Please   │
│ share the code you're working with, and let me know what specific issues... │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────── 💬 Last Exchange ───────────────────────────────╮
│                                                                              │
│ USER: Perfect! The memoization version works much better. Can you explain   │
│ the time complexity difference?                                              │
│                                                                              │
│ ASSISTANT: Great question! Let me break down the time complexity            │
│ differences between the recursive approaches:                                │
│ - Basic recursion: O(2^n) - exponential time...                            │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

Cost Breakdown by Turn:
┏━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Turn   │ Prompt Tokens  │ Completion Tokens   │ Cost       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│   1    │            45  │                 127 │ $0.0020    │
│   2    │           134  │                  89 │ $0.0025    │
│   3    │           198  │                 156 │ $0.0033    │
│   4    │           267  │                 134 │ $0.0042    │
│   5    │           345  │                  63 │ $0.0069    │
└────────┴────────────────┴─────────────────────┴────────────┘

Actions available:
• Resume the session: llm sessions resume ./runs/session_20240108_143022.json
• List all sessions: llm sessions list
```

### llm sessions resume

Resume an existing conversation session.

#### Syntax

```bash
llm sessions resume <SESSION_PATH>
```

#### Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `session_path` | ✅ Yes | string | Path to session JSON file |

#### Example

```bash
$ llm sessions resume ./runs/session_20240108_143022.json

🔄 Resuming session: session_20240108_143022.json
Model: openai/gpt-4o-mini
Previous turns: 5
Tokens used: 1,247

🤖 Continuing chat with openai/gpt-4o-mini
💰 Budget: Unlimited | Previous cost: $0.0189 | Type ':help' for commands

[Previous conversation context is loaded]

You: Let's continue with the algorithm optimization discussion...
```

## Exit Codes

The CLI uses standard exit codes to indicate success or failure:

| Exit Code | Meaning | When Used |
|-----------|---------|----------|
| `0` | Success | Command completed successfully |
| `1` | General error | Authentication, network, or API errors |
| `2` | Invalid usage | Missing parameters or invalid options |
| `130` | Interrupted | User pressed Ctrl+C |

### Examples

```bash
# Check exit code in bash
llm ask "test" --model openai/gpt-4o-mini
echo "Exit code: $?"
# Output: Exit code: 0

# Handle errors in scripts
if ! llm models list >/dev/null 2>&1; then
    echo "Failed to connect to OpenRouter"
    exit 1
fi
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | `sk-or-v1-abc123...` |

### Optional

| Variable | Description | Default | Example |
|----------|-------------|---------|----------|
| `OPENROUTER_HTTP_REFERER` | HTTP Referer for analytics | None | `https://myapp.com` |
| `OPENROUTER_X_TITLE` | App name for analytics | None | `My LLM App` |
| `LLM_DEBUG` | Enable debug logging | `false` | `true` |
| `LLM_CONFIG_DIR` | Config directory | `~/.config/llm` | `/custom/config` |
| `LLM_SESSIONS_DIR` | Default sessions directory | `./runs` | `/my/sessions` |

### Setting Environment Variables

```bash
# For current session
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
export OPENROUTER_HTTP_REFERER=https://myapp.com
export LLM_DEBUG=true

# Permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENROUTER_API_KEY=sk-or-v1-your-key-here' >> ~/.bashrc

# Using .env file (in project directory)
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key-here' > .env
echo 'OPENROUTER_HTTP_REFERER=https://myapp.com' >> .env
```

## Configuration Files

### User Configuration

Create `~/.config/llm/config.json` for user-wide defaults:

```json
{
  "default_model": "openai/gpt-4o-mini",
  "default_budget": 1.0,
  "session_dir": "~/Documents/llm-sessions",
  "default_system_prompt": "You are a helpful assistant.",
  "stream_responses": true,
  "save_sessions": true,
  "show_costs": true,
  "auto_save_interval": 300
}
```

### Project Configuration

Create `.llm-config.json` in your project directory:

```json
{
  "default_model": "anthropic/claude-3.5-sonnet",
  "session_dir": "./conversations",
  "default_system_prompt": "You are a code review assistant for this Python project.",
  "default_budget": 5.0
}
```

### Configuration Priority

Configuration is loaded in this order (highest to lowest priority):

1. Command line arguments
2. Environment variables  
3. Project configuration (`.llm-config.json`)
4. User configuration (`~/.config/llm/config.json`)
5. Built-in defaults

### Configuration Schema

| Setting | Type | Description | Default |
|---------|------|-------------|----------|
| `default_model` | string | Default model ID | `openai/gpt-4o-mini` |
| `default_budget` | number | Default budget limit | `null` (unlimited) |
| `session_dir` | string | Sessions storage directory | `./runs` |
| `default_system_prompt` | string | Default system prompt | `null` |
| `stream_responses` | boolean | Enable response streaming | `true` |
| `save_sessions` | boolean | Auto-save chat sessions | `true` |
| `show_costs` | boolean | Display cost information | `true` |
| `auto_save_interval` | number | Auto-save interval (seconds) | `300` |
| `max_retries` | number | API retry attempts | `3` |
| `request_timeout` | number | Request timeout (seconds) | `60` |

---

**Need more help?** Check out the other documentation files:
- [Getting Started Guide](GETTING_STARTED.md) - Basic setup and first steps
- [Sessions Guide](SESSIONS_GUIDE.md) - Deep dive into session management
- [Budget Management](BUDGET_MANAGEMENT.md) - Cost control and optimization