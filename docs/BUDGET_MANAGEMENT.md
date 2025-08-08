# 💰 Budget Management Guide

Complete guide to managing costs and optimizing spending with LLM CLI.

## Table of Contents

- [Understanding Costs](#understanding-costs)
- [Setting Budgets](#setting-budgets)
- [Cost Tracking](#cost-tracking)
- [Optimization Strategies](#optimization-strategies)
- [Model Cost Comparison](#model-cost-comparison)
- [Usage Analytics](#usage-analytics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Understanding Costs

### How OpenRouter Pricing Works

OpenRouter charges for two types of tokens:

- **Input tokens** (prompt): The text you send to the model
- **Output tokens** (completion): The text the model generates

Pricing varies by model and is typically quoted per million tokens.

### Cost Components

Each API call includes:
1. **Base cost** = (input_tokens × input_price) + (output_tokens × output_price)
2. **OpenRouter markup** (small percentage added to provider prices)
3. **No additional fees** from LLM CLI tool

### Example Cost Calculation

For `openai/gpt-4o-mini`:
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

A conversation with 1,000 input tokens and 500 output tokens costs:
```
(1,000 × $0.15/1M) + (500 × $0.60/1M) = $0.00015 + $0.0003 = $0.00045
```

## Setting Budgets

### Command-Line Budgets

Set spending limits directly in commands:

```bash
# Set budget for chat session
llm chat --budget 0.50 --model openai/gpt-4o

# Start with budget warning at 80%
llm chat --budget 1.00 --warn-at 0.80 --model anthropic/claude-3-sonnet
```

### Environment Variables

Set default budgets via environment:

```bash
# Set default daily budget
export LLM_DAILY_BUDGET=5.00

# Set default session budget
export LLM_SESSION_BUDGET=1.00

# Use in commands
llm chat --model gpt-4  # Automatically uses session budget
```

### Configuration Files

Set budgets in configuration files:

```json
// ~/.config/llm/config.json
{
  "default_budget": 2.0,
  "daily_budget": 10.0,
  "budget_warnings": {
    "50_percent": true,
    "80_percent": true,
    "90_percent": true
  },
  "budget_actions": {
    "at_limit": "warn",  // or "stop"
    "over_limit": "stop"
  }
}
```

### Interactive Budget Management

During chat sessions:

```bash
You: :budget 1.50
💰 Budget set to $1.50

You: :budget status
💰 Budget Status:
   Current: $0.23 spent
   Limit: $1.50
   Remaining: $1.27 (85%)

You: :budget increase 0.50
💰 Budget increased to $2.00
```

## Cost Tracking

### Real-Time Cost Display

Every interaction shows cost information:

```bash
$ llm ask "Explain machine learning" --model openai/gpt-4o-mini

Question:
> Explain machine learning

Response:

Machine learning is a subset of artificial intelligence...

────────────────────────────────────────
Model: openai/gpt-4o-mini | Tokens: 18→234 (252) | 1.45s | ~$0.0037
```

### Session Cost Tracking

Chat sessions show cumulative costs:

```bash
You: Tell me about Python decorators

Assistant: Python decorators are a powerful feature that allows you to modify or extend the behavior of functions or classes without permanently modifying their code...

────────────────────────────────────────
Tokens: 25→187 (212) | 1.8s | ~$0.0035
Session cost: $0.0035 | Budget remaining: $0.9965

You: Can you show me a practical example?

Assistant: Absolutely! Here's a practical timing decorator...

────────────────────────────────────────
Tokens: 234→156 (390) | 1.2s | ~$0.0059
Session cost: $0.0094 | Budget remaining: $0.9906
```

### Budget Alerts

The tool provides automatic warnings:

```bash
⚠️  Budget Alert: 50% used ($0.50 of $1.00)
⚠️  Budget Warning: 80% used ($0.80 of $1.00)
🚨 Budget Critical: 90% used ($0.90 of $1.00)
🛑 Budget Exceeded: $1.05 spent (limit: $1.00)
```

### Cost History

View detailed cost breakdown:

```bash
You: :cost detailed

💰 Session Cost Breakdown:

Turn 1: $0.0035 (25→187 tokens) - "Tell me about Python decorators"
Turn 2: $0.0059 (234→156 tokens) - "Can you show me a practical example?"
Turn 3: $0.0028 (189→98 tokens) - "How about error handling?"
Turn 4: $0.0041 (267→145 tokens) - "Best practices for decorators?"

Total Cost: $0.0163
Average per turn: $0.0041
Budget remaining: $0.9837

Model: openai/gpt-4o-mini
Input price: $0.15/1M tokens
Output price: $0.60/1M tokens
```

## Optimization Strategies

### 1. Choose the Right Model

**For simple tasks** - Use cost-effective models:
```bash
# Best value for basic questions
llm ask "What is Python?" --model openai/gpt-4o-mini

# Fast and cheap for simple tasks  
llm ask "Translate 'hello' to French" --model anthropic/claude-3-haiku
```

**For complex tasks** - Use powerful models efficiently:
```bash
# Use GPT-4 for complex reasoning, but be specific
llm ask "Analyze this algorithm's time complexity: [code]" --model openai/gpt-4o

# Not: "Tell me about algorithms in general"
```

### 2. Optimize Your Prompts

**Be specific and concise:**
```bash
# Expensive (vague, leads to long responses)
llm ask "Tell me about programming" --model gpt-4

# Cheaper (specific, focused response)
llm ask "Explain Python list comprehensions with 2 examples" --model gpt-4
```

**Use system prompts effectively:**
```bash
# Efficient system prompt
llm chat --model gpt-4 --system "Give concise, code-focused answers for Python questions"

# Inefficient system prompt
llm chat --model gpt-4 --system "You are an expert in everything. Please provide detailed explanations with historical context, multiple examples, and comprehensive coverage of every topic."
```

### 3. Manage Context Length

**Long conversations accumulate context costs:**
```bash
# Monitor context growth
You: :context size
📏 Context: 2,456 tokens (costs $0.0037 per new turn)

# Reset context when appropriate
You: :reset
🔄 Context cleared. Fresh start!
```

**Use session breaks strategically:**
```bash
# End and restart for new topics
You: :save current_topic
You: :exit

# Start fresh session for new topic
llm chat --model same-model
```

### 4. Batch Similar Queries

**Instead of multiple sessions:**
```bash
# Expensive: 3 separate calls
llm ask "Explain lists" --model gpt-4
llm ask "Explain dictionaries" --model gpt-4  
llm ask "Explain sets" --model gpt-4
```

**Use one comprehensive session:**
```bash
llm ask "Explain Python lists, dictionaries, and sets with examples for each" --model gpt-4
```

### 5. Smart Model Switching

**Start cheap, escalate if needed:**
```bash
# Try with cheaper model first
llm ask "Debug this Python code: [code]" --model anthropic/claude-3-haiku

# If response isn't good enough, try more powerful model
llm ask "Debug this Python code with detailed explanation: [code]" --model openai/gpt-4o
```

**Use model strengths:**
```bash
# Anthropic models excel at analysis
llm ask "Review this code for best practices" --model anthropic/claude-3.5-sonnet

# OpenAI models excel at creative tasks
llm ask "Write a creative story about robots" --model openai/gpt-4o

# Use smaller models for simple tasks
llm ask "Fix this typo in my code" --model openai/gpt-4o-mini
```

## Model Cost Comparison

### Cost Tiers

#### Ultra Budget (< $0.50/1M tokens)
```bash
# Free/very cheap models
llm models list --filter "free" | head -5

# Example usage
llm ask "Simple question" --model some-free-model
```

#### Budget Tier ($0.50-2.00/1M tokens)
| Model | Input | Output | Best For |
|-------|-------|--------|-----------|
| `openai/gpt-4o-mini` | $0.15/1M | $0.60/1M | General questions, simple coding |
| `anthropic/claude-3-haiku` | $0.25/1M | $1.25/1M | Analysis, longer context |
| `google/gemini-flash` | $0.35/1M | $1.05/1M | Multimodal tasks |

#### Performance Tier ($2.00-5.00/1M tokens)
| Model | Input | Output | Best For |
|-------|-------|--------|-----------|
| `anthropic/claude-3-sonnet` | $3.00/1M | $15.00/1M | Code review, analysis |
| `anthropic/claude-3.5-sonnet` | $3.00/1M | $15.00/1M | Creative writing, complex coding |
| `openai/gpt-4-turbo` | $10.00/1M | $30.00/1M | Complex reasoning |

#### Premium Tier ($5.00+/1M tokens)
| Model | Input | Output | Best For |
|-------|-------|--------|-----------|
| `openai/gpt-4o` | $5.00/1M | $15.00/1M | Most challenging tasks |
| `anthropic/claude-3-opus` | $15.00/1M | $75.00/1M | Highest quality analysis |

### Cost Comparison Tool

Compare costs for your specific use case:

```python
#!/usr/bin/env python3
"""
Cost comparison calculator for different models.
"""

def calculate_cost(input_tokens, output_tokens, input_price_per_1m, output_price_per_1m):
    """Calculate cost for given token usage."""
    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m
    return input_cost + output_cost

# Model pricing (per 1M tokens)
models = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "openai/gpt-4o": {"input": 5.00, "output": 15.00},
    "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00}
}

# Your typical usage pattern
input_tokens = 1000   # Your average prompt length
output_tokens = 500   # Typical response length
monthly_requests = 200  # How many requests per month

print(f"📊 Cost Comparison for {monthly_requests} monthly requests")
print(f"   Average: {input_tokens} input + {output_tokens} output tokens\n")

for model_name, pricing in models.items():
    per_request = calculate_cost(
        input_tokens, output_tokens, 
        pricing["input"], pricing["output"]
    )
    monthly_cost = per_request * monthly_requests
    
    print(f"{model_name}:")
    print(f"  Per request: ${per_request:.4f}")
    print(f"  Monthly: ${monthly_cost:.2f}")
    print()

# Find most economical model
costs = {
    model: calculate_cost(input_tokens, output_tokens, pricing["input"], pricing["output"]) * monthly_requests
    for model, pricing in models.items()
}

cheapest = min(costs, key=costs.get)
print(f"💡 Most economical: {cheapest} (${costs[cheapest]:.2f}/month)")
```

### Sample Output
```bash
$ python3 cost_calculator.py

📊 Cost Comparison for 200 monthly requests
   Average: 1000 input + 500 output tokens

openai/gpt-4o-mini:
  Per request: $0.0005
  Monthly: $0.09

anthropic/claude-3-haiku:
  Per request: $0.0009
  Monthly: $0.18

openai/gpt-4o:
  Per request: $0.0125
  Monthly: $2.50

anthropic/claude-3-opus:
  Per request: $0.0525
  Monthly: $10.50

💡 Most economical: openai/gpt-4o-mini ($0.09/month)
```

## Usage Analytics

### Built-in Analytics

View your usage patterns:

```bash
# Session statistics
llm sessions list | grep -E "Cost|Tokens"

# Daily usage summary
llm usage today

# Weekly usage breakdown
llm usage week --breakdown-by model

# Monthly spending report
llm usage month --format detailed
```

### Custom Analytics Scripts

#### Daily Spending Tracker

```python
#!/usr/bin/env python3
"""
Track daily spending across all sessions.
"""

import json
import glob
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_daily_spending(sessions_dir="./runs", days_back=30):
    """Analyze spending over the last N days."""
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    daily_costs = defaultdict(float)
    daily_tokens = defaultdict(int)
    model_usage = defaultdict(float)
    
    for session_file in glob.glob(f"{sessions_dir}/*.json"):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            # Parse session date
            created_at = datetime.fromisoformat(session.get('created_at', ''))
            if created_at < start_date:
                continue
                
            date_key = created_at.strftime('%Y-%m-%d')
            model = session.get('model', 'unknown')
            
            # Calculate session cost and tokens
            session_cost = 0
            session_tokens = 0
            
            for turn in session.get('turns', []):
                turn_cost = turn.get('cost_estimate', 0)
                turn_tokens = turn.get('usage', {}).get('total_tokens', 0)
                
                session_cost += turn_cost
                session_tokens += turn_tokens
            
            daily_costs[date_key] += session_cost
            daily_tokens[date_key] += session_tokens
            model_usage[model] += session_cost
            
        except Exception as e:
            print(f"Error processing {session_file}: {e}")
    
    # Print daily breakdown
    print(f"📅 Daily Spending (Last {days_back} Days)")
    print(f"{'Date':<12} {'Cost':<10} {'Tokens':<10} {'$/Token':<10}")
    print("-" * 45)
    
    total_cost = 0
    total_tokens = 0
    
    for i in range(days_back):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        cost = daily_costs.get(date, 0)
        tokens = daily_tokens.get(date, 0)
        cost_per_token = cost / tokens if tokens > 0 else 0
        
        if cost > 0:  # Only show days with activity
            print(f"{date:<12} ${cost:<9.4f} {tokens:<10,} ${cost_per_token:<9.6f}")
            total_cost += cost
            total_tokens += tokens
    
    print("-" * 45)
    print(f"{'TOTAL':<12} ${total_cost:<9.4f} {total_tokens:<10,} ${total_cost/total_tokens if total_tokens > 0 else 0:<9.6f}")
    
    # Model breakdown
    print(f"\n🤖 Model Usage")
    print(f"{'Model':<30} {'Cost':<10} {'%':<6}")
    print("-" * 48)
    
    for model, cost in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
        percentage = (cost / total_cost * 100) if total_cost > 0 else 0
        print(f"{model:<30} ${cost:<9.4f} {percentage:<5.1f}%")
    
    # Weekly average
    weeks = days_back / 7
    weekly_avg = total_cost / weeks if weeks > 0 else 0
    monthly_projection = weekly_avg * 4.33  # Average weeks per month
    
    print(f"\n📊 Projections")
    print(f"Weekly average: ${weekly_avg:.4f}")
    print(f"Monthly projection: ${monthly_projection:.2f}")
    
    return {
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'daily_costs': dict(daily_costs),
        'model_usage': dict(model_usage),
        'monthly_projection': monthly_projection
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze daily LLM spending')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--dir', default='./runs', help='Sessions directory')
    
    args = parser.parse_args()
    
    analyze_daily_spending(args.dir, args.days)
```

#### Model ROI Analysis

```python
#!/usr/bin/env python3
"""
Analyze return on investment for different models.
"""

import json
import glob
from collections import defaultdict

def analyze_model_roi(sessions_dir="./runs"):
    """Analyze cost vs. value for different models."""
    
    model_stats = defaultdict(lambda: {
        'cost': 0,
        'tokens': 0,
        'sessions': 0,
        'avg_turns': 0,
        'total_turns': 0
    })
    
    for session_file in glob.glob(f"{sessions_dir}/*.json"):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            model = session.get('model', 'unknown')
            turns = len(session.get('turns', []))
            
            session_cost = sum(
                turn.get('cost_estimate', 0) 
                for turn in session.get('turns', [])
            )
            
            session_tokens = sum(
                turn.get('usage', {}).get('total_tokens', 0)
                for turn in session.get('turns', [])
            )
            
            stats = model_stats[model]
            stats['cost'] += session_cost
            stats['tokens'] += session_tokens
            stats['sessions'] += 1
            stats['total_turns'] += turns
            
        except Exception as e:
            continue
    
    # Calculate averages
    for model, stats in model_stats.items():
        if stats['sessions'] > 0:
            stats['avg_turns'] = stats['total_turns'] / stats['sessions']
            stats['cost_per_session'] = stats['cost'] / stats['sessions']
            stats['cost_per_turn'] = stats['cost'] / stats['total_turns'] if stats['total_turns'] > 0 else 0
            stats['cost_per_token'] = stats['cost'] / stats['tokens'] if stats['tokens'] > 0 else 0
    
    # Print analysis
    print("🎯 Model ROI Analysis")
    print()
    
    print(f"{'Model':<30} {'Sessions':<8} {'Avg Turns':<10} {'Cost/Session':<12} {'Cost/Turn':<10} {'Efficiency':<10}")
    print("-" * 95)
    
    # Sort by cost per turn (efficiency metric)
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['cost_per_turn'])
    
    for model, stats in sorted_models:
        if stats['sessions'] == 0:
            continue
            
        efficiency = "High" if stats['cost_per_turn'] < 0.01 else "Medium" if stats['cost_per_turn'] < 0.05 else "Low"
        
        print(f"{model:<30} {stats['sessions']:<8} {stats['avg_turns']:<10.1f} ${stats['cost_per_session']:<11.4f} ${stats['cost_per_turn']:<9.4f} {efficiency:<10}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if sorted_models:
        most_efficient = sorted_models[0][0]
        print(f"• Most efficient model: {most_efficient}")
        
        expensive_models = [model for model, stats in sorted_models if stats['cost_per_turn'] > 0.05]
        if expensive_models:
            print(f"• Consider alternatives to: {', '.join(expensive_models[:3])}")
        
        # Usage patterns
        high_volume_models = [model for model, stats in model_stats.items() if stats['sessions'] > 10]
        if high_volume_models:
            print(f"• High-volume models (optimize these): {', '.join(high_volume_models[:3])}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze model ROI')
    parser.add_argument('--dir', default='./runs', help='Sessions directory')
    
    args = parser.parse_args()
    
    analyze_model_roi(args.dir)
```

## Best Practices

### 1. Budget Planning

**Set realistic budgets:**
```bash
# Start conservative
llm chat --budget 0.25 --model openai/gpt-4o-mini

# Increase as needed
You: :budget increase 0.25
```

**Use tiered budgets:**
```bash
# Daily exploration budget
export LLM_DAILY_BUDGET=1.00

# Project work budget
llm chat --budget 5.00 --model anthropic/claude-3.5-sonnet --save-dir ./project-sessions

# Learning budget  
llm chat --budget 2.00 --model openai/gpt-4o-mini --save-dir ./learning-sessions
```

### 2. Cost-Conscious Prompting

**Front-load your requirements:**
```bash
# Good: Everything in one request
llm ask "Write a Python function to parse CSV files. Include error handling, type hints, and docstring" --model gpt-4

# Avoid: Multiple follow-up requests
# "Write a Python function to parse CSV"
# "Add error handling"
# "Add type hints" 
# "Add documentation"
```

**Use structured prompts:**
```bash
llm ask "Task: Debug Python code
Code: [paste code]
Error: [error message]
Context: [brief context]
Expected: Working code with explanation" --model anthropic/claude-3.5-sonnet
```

### 3. Smart Model Selection

**Create model aliases for common tasks:**
```bash
# In your shell profile
alias llm-quick="llm ask --model openai/gpt-4o-mini"
alias llm-code="llm ask --model anthropic/claude-3.5-sonnet"
alias llm-deep="llm ask --model openai/gpt-4o"

# Usage
llm-quick "What's the Python syntax for list comprehension?"
llm-code "Review this function for best practices: [code]"
llm-deep "Design a distributed system architecture for [requirements]"
```

**Model escalation strategy:**
```bash
# Try cheaper model first
if ! llm ask "$QUESTION" --model anthropic/claude-3-haiku --json | jq -e '.response | length > 50' >/dev/null; then
    echo "Trying more powerful model..."
    llm ask "$QUESTION" --model openai/gpt-4o
fi
```

### 4. Monitoring and Alerts

**Set up spending alerts:**
```bash
#!/bin/bash
# daily_budget_check.sh

DAILY_LIMIT=5.00
SPENT=$(python3 -c "
import json, glob
from datetime import datetime, timedelta

today = datetime.now().strftime('%Y-%m-%d')
cost = sum(
    sum(turn.get('cost_estimate', 0) for turn in json.load(open(f)).get('turns', []))
    for f in glob.glob('./runs/*.json')
    if today in json.load(open(f)).get('created_at', '')
)
print(f'{cost:.4f}')
")

if (( $(echo "$SPENT > $DAILY_LIMIT" | bc -l) )); then
    echo "⚠️ Daily budget exceeded: \$${SPENT} (limit: \$${DAILY_LIMIT})"
    # Send notification, email, etc.
fi
```

**Add to cron for daily checks:**
```bash
# Add to crontab -e
0 18 * * * /path/to/daily_budget_check.sh
```

### 5. Cost Optimization Automation

**Auto-switch models based on budget:**
```bash
#!/bin/bash
# smart_llm.sh - Automatically choose model based on remaining budget

QUESTION="$1"
DAILY_BUDGET=5.00

# Calculate spent today
SPENT=$(python3 calculate_daily_spent.py)
REMAINING=$(echo "$DAILY_BUDGET - $SPENT" | bc -l)

# Choose model based on remaining budget
if (( $(echo "$REMAINING > 2.00" | bc -l) )); then
    MODEL="openai/gpt-4o"  # Premium model
elif (( $(echo "$REMAINING > 0.50" | bc -l) )); then
    MODEL="anthropic/claude-3.5-sonnet"  # Balanced model
else
    MODEL="openai/gpt-4o-mini"  # Budget model
fi

echo "Using $MODEL (\$$REMAINING budget remaining)"
llm ask "$QUESTION" --model "$MODEL"
```

## Troubleshooting

### Common Issues

#### Unexpected High Costs

```bash
# Check recent high-cost sessions
llm sessions list | sort -k6 -nr | head -5

# Analyze specific session
llm sessions show ./runs/expensive_session.json

# Look for patterns
grep -h "cost_estimate" ./runs/*.json | sort -n | tail -10
```

#### Budget Not Working

```bash
# Check budget configuration
echo "Config budget: $LLM_SESSION_BUDGET"
echo "Daily budget: $LLM_DAILY_BUDGET"

# Verify budget is set in chat
You: :budget status

# Debug budget calculation
LLM_DEBUG=1 llm chat --budget 1.00 --model gpt-4
```

#### Cost Calculation Errors

```bash
# Verify model pricing
llm models info openai/gpt-4o-mini | grep -E "Price|Cost"

# Check session cost calculation
python3 -c "
import json
with open('./runs/session.json') as f:
    session = json.load(f)
for i, turn in enumerate(session['turns']):
    print(f'Turn {i+1}: cost={turn.get(\"cost_estimate\", 0)}')
"
```

### Recovery Strategies

#### Budget Overrun Recovery

```bash
# Pause expensive operations
export LLM_EMERGENCY_MODE=1

# Switch to cheapest models only
alias llm="llm --model openai/gpt-4o-mini"

# Review and clean up expensive sessions
find ./runs -name "*.json" -exec python3 -c "
import sys, json
with open(sys.argv[1]) as f: s=json.load(f)
cost = sum(t.get('cost_estimate',0) for t in s.get('turns',[]))
if cost > 0.1: print(f'{sys.argv[1]}: ${cost:.4f}')
" {} \;
```

#### Cost Tracking Reset

```bash
# Archive expensive sessions
mkdir -p ./archive/expensive
find ./runs -name "*.json" -exec python3 -c "
import sys, json, shutil
with open(sys.argv[1]) as f: s=json.load(f)
cost = sum(t.get('cost_estimate',0) for t in s.get('turns',[]))
if cost > 0.05: shutil.move(sys.argv[1], './archive/expensive/')
" {} \;

# Start fresh with strict budget
llm chat --budget 0.25 --model openai/gpt-4o-mini
```

### Budget Health Check

Run this weekly to maintain cost control:

```python
#!/usr/bin/env python3
"""
Weekly budget health check.
"""

def budget_health_check():
    """Comprehensive budget analysis."""
    
    # Import your analytics functions
    from daily_spending_tracker import analyze_daily_spending
    from model_roi_analysis import analyze_model_roi
    
    print("📊 Weekly Budget Health Check")
    print("=" * 50)
    
    # Analyze spending trends
    spending_data = analyze_daily_spending(days_back=7)
    
    # Check for anomalies
    if spending_data['monthly_projection'] > 20:  # Adjust threshold
        print("⚠️ HIGH SPENDING ALERT")
        print(f"   Monthly projection: ${spending_data['monthly_projection']:.2f}")
        print("   Consider:")  
        print("   • Switching to cheaper models")
        print("   • Reducing session frequency")
        print("   • Optimizing prompts")
        print()
    
    # Model efficiency check
    print("🤖 Model Efficiency Check:")
    analyze_model_roi()
    
    # Recommendations
    print("\n💡 Weekly Recommendations:")
    print("• Review high-cost sessions")
    print("• Archive old sessions")
    print("• Update budget limits if needed")
    print("• Consider model alternatives")

if __name__ == "__main__":
    budget_health_check()
```

---

**Related Documentation:**
- [Getting Started Guide](GETTING_STARTED.md) - Basic setup and first steps
- [Commands Reference](COMMANDS_REFERENCE.md) - Complete command documentation
- [Sessions Guide](SESSIONS_GUIDE.md) - Session management and analysis