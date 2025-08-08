# 🚀 Getting Started with LLM CLI

This guide will help you get up and running with the LLM CLI tool in just a few minutes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Your API Key](#getting-your-api-key)
- [First Steps](#first-steps)
- [Your First Chat](#your-first-chat)
- [Understanding the Interface](#understanding-the-interface)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, make sure you have:

- **Python 3.9 or higher** installed on your system
- **Command line access** (Terminal on Mac/Linux, Command Prompt on Windows)
- **Internet connection** for API access
- **A few dollars** in OpenRouter credit (minimum $1 recommended)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

If you don't have Python installed, download it from [python.org](https://python.org).

## Installation

### Step 1: Get the Code

```bash
# Clone the repository
git clone <repository-url>
cd phemis

# Or download and extract the ZIP file
```

### Step 2: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install the CLI tool
pip install -e .
```

### Step 3: Verify Installation

```bash
# Check if the tool is installed correctly
llm --version
```

You should see output like:
```
llm-cli version 0.1.0
```

## Getting Your API Key

### Step 1: Create OpenRouter Account

1. Go to [OpenRouter.ai](https://openrouter.ai)
2. Click "Sign up" and create an account
3. Verify your email address

### Step 2: Add Credit to Your Account

1. Go to [Credits page](https://openrouter.ai/credits)
2. Add at least $1 to your account
3. This will cover thousands of basic interactions

### Step 3: Create API Key

1. Visit [OpenRouter Keys](https://openrouter.ai/keys)
2. Click "Create Key"
3. Give it a name like "LLM CLI Tool"
4. Copy the generated key (starts with `sk-or-v1-`)

⚠️ **Important**: Save your API key securely. You won't be able to see it again!

### Step 4: Set Up Your API Key

Choose one of these methods:

#### Option A: Environment Variable (Recommended)

```bash
# For this session only
export OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# To make it permanent, add to your shell profile:
echo 'export OPENROUTER_API_KEY=sk-or-v1-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

#### Option B: Create .env File

```bash
# In the phemis directory
echo 'OPENROUTER_API_KEY=sk-or-v1-your-api-key-here' > .env
```

## First Steps

### Step 1: Test Your Setup

```bash
# This should show available models
llm models list
```

If you see a table of models, congratulations! Your setup is working.

### Step 2: Ask Your First Question

```bash
llm ask "Hello! Can you introduce yourself?" --model openai/gpt-4o-mini
```

You should see a response like:

```
Question:
> Hello! Can you introduce yourself?

Response:

Hello! I'm Claude, an AI assistant created by Anthropic. I'm here to help you with a wide variety of tasks including answering questions, helping with analysis, writing, math, coding, creative projects, and general conversation. I aim to be helpful, harmless, and honest in all my interactions. How can I assist you today?

────────────────────────────────────────
Model: openai/gpt-4o-mini | Tokens: 15→54 (69) | 1.2s | ~$0.0001
```

### Step 3: Explore Available Models

```bash
# See all models
llm models list

# Filter by provider
llm models list --filter anthropic
llm models list --filter openai

# Get detailed info about a model
llm models info openai/gpt-4o-mini
```

## Your First Chat

Now let's start an interactive conversation:

```bash
llm chat --model openai/gpt-4o-mini
```

You'll see:

```
🤖 Starting chat with openai/gpt-4o-mini
💰 Budget: Unlimited | Type ':help' for commands

You: 
```

Try these conversation starters:

1. **Basic conversation**:
   ```
   You: Hi! What's the weather like today?
   ```

2. **Ask for help with code**:
   ```
   You: Can you write a Python function to calculate fibonacci numbers?
   ```

3. **Creative tasks**:
   ```
   You: Write a haiku about programming
   ```

### Chat Commands

While in chat mode, you can use these special commands:

- `:help` - Show available commands
- `:models` - List available models  
- `:switch <model>` - Change to a different model
- `:system <prompt>` - Set a system prompt
- `:budget <amount>` - Set spending limit
- `:save` - Save the current session
- `:reset` - Clear conversation history
- `:exit` - End the chat

Example:
```
You: :system You are a helpful Python tutor
System prompt updated!

You: :budget 0.50
Budget set to $0.50

You: How do I create a class in Python?
```

## Understanding the Interface

### Response Format

Each response shows:
- **The question** you asked
- **The AI's response** (streamed in real-time)
- **Metadata footer** with:
  - Model used
  - Token usage (input→output total)
  - Response time
  - Estimated cost

Example footer:
```
Model: openai/gpt-4o-mini | Tokens: 15→54 (69) | 1.2s | ~$0.0001
```

### Cost Tracking

The tool shows cost estimates for every interaction:
- Individual request costs
- Running session totals
- Budget remaining (if set)

### Session Storage

Chat sessions are automatically saved to `./runs/` directory:
```
./runs/session_20240108_143022.json
```

You can:
- Resume sessions later
- Review conversation history
- Analyze usage patterns

## Next Steps

### 1. Try Different Models

Each model has different strengths:

```bash
# For quick questions (fast, cheap)
llm ask "What is Python?" --model openai/gpt-4o-mini

# For code help (balanced)
llm ask "Debug this code: print('hello world')" --model anthropic/claude-3-haiku

# For complex reasoning (powerful, expensive)
llm ask "Explain quantum computing" --model openai/gpt-4o
```

### 2. Use System Prompts

System prompts shape the AI's behavior:

```bash
llm ask "Explain variables" \
  --model openai/gpt-4o-mini \
  --system "You are a programming teacher for beginners. Use simple language and examples."
```

### 3. Automate with JSON Output

```bash
# Get structured output for scripts
llm ask "What is 2+2?" --model openai/gpt-4o-mini --json
```

### 4. Explore Session Management

```bash
# List your conversations
llm sessions list

# View a specific session
llm sessions show ./runs/session_20240108_143022.json

# Resume a conversation
llm sessions resume ./runs/session_20240108_143022.json
```

### 5. Set Up Budgets

```bash
# Start chat with spending limit
llm chat --model openai/gpt-4o --budget 0.25
```

## Troubleshooting

### "Command not found: llm"

```bash
# Make sure the tool is installed
pip install -e .

# Check if it's in your PATH
which llm

# Try running directly
python -m llm.cli.main --version
```

### "Authentication failed"

```bash
# Check your API key is set
echo $OPENROUTER_API_KEY

# Verify it starts with sk-or-v1-
echo $OPENROUTER_API_KEY | cut -c1-10

# Re-export if needed
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### "No models available"

```bash
# Test your internet connection
curl -I https://openrouter.ai

# Verify API key is valid
llm models list | head -5
```

### "Rate limit exceeded"

```bash
# Wait a moment and try again
sleep 5
llm ask "test" --model openai/gpt-4o-mini

# Or use a less popular model
llm ask "test" --model anthropic/claude-3-haiku
```

### Sessions not saving

```bash
# Check if runs directory exists
ls -la ./runs

# Create it if missing
mkdir -p ./runs

# Check permissions
ls -la ./runs
```

## Getting Help

### Built-in Help

```bash
# General help
llm --help

# Command-specific help
llm ask --help
llm chat --help
llm models --help
llm sessions --help
```

### Community Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the full docs in `/docs/`
- **Examples**: Look at example scripts in `/examples/`

## Summary

You now know how to:

✅ Install and configure the LLM CLI tool  
✅ Set up your OpenRouter API key  
✅ Ask single questions with `llm ask`  
✅ Have interactive conversations with `llm chat`  
✅ Explore and compare models with `llm models`  
✅ Manage your conversation sessions  
✅ Control costs and set budgets  

### Quick Reference Card

```bash
# Essential commands
llm ask "question" --model openai/gpt-4o-mini    # Single Q&A
llm chat --model anthropic/claude-3-haiku        # Interactive chat  
llm models list --filter openai                  # Find models
llm sessions list                                 # View conversations

# Cost control
llm chat --budget 0.50 --model gpt-4            # Set spending limit

# Automation
llm ask "question" --model gpt-4o-mini --json   # JSON output
```

Ready to explore further? Check out:
- [Commands Reference](COMMANDS_REFERENCE.md) - Complete command documentation
- [Budget Management](BUDGET_MANAGEMENT.md) - Advanced cost control
- [Sessions Guide](SESSIONS_GUIDE.md) - Deep dive into conversations

Happy chatting! 🤖