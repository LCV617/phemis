# 💾 Sessions Guide

Complete guide to managing conversation sessions in LLM CLI.

## Table of Contents

- [What are Sessions?](#what-are-sessions)
- [Session File Format](#session-file-format)
- [Creating Sessions](#creating-sessions)
- [Managing Sessions](#managing-sessions)
- [Session Analysis](#session-analysis)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## What are Sessions?

Sessions are persistent conversation records that capture:

- **Complete conversation history** with user and assistant messages
- **Usage statistics** including token counts and costs
- **Model and configuration** details
- **Timing information** for performance analysis
- **Metadata** for organization and search

### Benefits of Sessions

✅ **Continuity** - Resume conversations exactly where you left off  
✅ **Analysis** - Track costs, token usage, and conversation patterns  
✅ **Backup** - Never lose important conversations  
✅ **Sharing** - Export and share conversations with others  
✅ **Learning** - Review and learn from past interactions  

## Session File Format

Sessions are stored as JSON files with the following structure:

### Basic Structure

```json
{
  "model": "openai/gpt-4o-mini",
  "system": "You are a helpful programming assistant",
  "created_at": "2024-01-08T14:30:22.123456",
  "turns": [
    {
      "messages": [
        {
          "role": "user",
          "content": "How do I create a Python class?"
        },
        {
          "role": "assistant", 
          "content": "To create a Python class, use the `class` keyword..."
        }
      ],
      "usage": {
        "prompt_tokens": 25,
        "completion_tokens": 187,
        "total_tokens": 212
      },
      "latency_ms": 1450.2,
      "cost_estimate": 0.0034
    }
  ],
  "usage_totals": {
    "prompt_tokens": 25,
    "completion_tokens": 187,
    "total_tokens": 212
  },
  "meta": {
    "user_id": "default",
    "session_type": "chat",
    "tags": ["python", "programming"]
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model identifier used for this session |
| `system` | string | System prompt (null if none) |
| `created_at` | datetime | Session creation timestamp |
| `turns` | array | List of conversation turns |
| `usage_totals` | object | Cumulative token usage |
| `meta` | object | Additional metadata |

### Turn Structure

Each turn represents one exchange (user question + assistant response):

```json
{
  "messages": [
    {
      "role": "user",
      "content": "User's message content"
    },
    {
      "role": "assistant",
      "content": "Assistant's response content"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 123,
    "total_tokens": 168
  },
  "latency_ms": 2150.7,
  "cost_estimate": 0.0051
}
```

## Creating Sessions

### Automatic Creation

Sessions are automatically created when you start a chat:

```bash
# New chat session
llm chat --model openai/gpt-4o-mini

🤖 Starting chat with openai/gpt-4o-mini
💾 Session will be saved to ./runs/session_20240108_143022.json
💰 Budget: Unlimited | Type ':help' for commands

You: Hello!
```

### Manual Save

You can manually save a session at any time during chat:

```bash
You: :save
💾 Session saved to ./runs/session_20240108_143022.json

# Save with custom name
You: :save my_coding_session
💾 Session saved to ./runs/my_coding_session.json
```

### Custom Session Directory

```bash
# Use custom directory
llm chat --model gpt-4 --save-dir ./my-conversations

# Set via environment variable
export LLM_SESSIONS_DIR=./my-conversations
llm chat --model gpt-4
```

## Managing Sessions

### Listing Sessions

```bash
# List all sessions
llm sessions list

# Use custom directory
llm sessions list --dir ./my-conversations

# Example output:
                                Sessions (5 found)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Filename                        ┃ Date            ┃ Model                   ┃ Turns ┃ Tokens  ┃ Est. Cost  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ session_20240108_143022.json    │ 2024-01-08 14:30│ openai/gpt-4o-mini     │     8 │   2,456 │ $0.0367    │
│ python_tutorial.json            │ 2024-01-08 15:45│ anthropic/claude-3-haiku│     5 │   1,234 │ $0.0089    │
│ debugging_session.json          │ 2024-01-07 20:15│ openai/gpt-4o          │    12 │   4,567 │ $0.2134    │
└─────────────────────────────────┴─────────────────┴─────────────────────────┴───────┴─────────┴────────────┘

Use 'llm sessions show <filename>' for more details
```

### Viewing Session Details

```bash
# Show detailed session information
llm sessions show ./runs/session_20240108_143022.json

# Example output:
Session: session_20240108_143022.json

╭─────────────────────────── Session Information ───────────────────────────╮
│ Model: openai/gpt-4o-mini                                                   │
│ Created: 2024-01-08 14:30:22                                               │
│ System: You are a helpful programming assistant                             │
│ Turns: 8                                                                    │
│ Total tokens: 2,456 (prompt: 1,234, completion: 1,222)                    │
│ Estimated cost: $0.0367                                                     │
│ Avg latency: 1.85s                                                         │
╰─────────────────────────────────────────────────────────────────────────────╰

╭─────────────────────────── 💬 First Exchange ─────────────────────────────╮
│                                                                              │
│ USER: Can you help me understand Python decorators? I'm confused about     │
│ how they work and when to use them.                                         │
│                                                                              │
│ ASSISTANT: I'd be happy to explain Python decorators! They're a powerful   │
│ feature that can seem confusing at first, but once you understand the...   │
│                                                                              │
╰─────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────── 💬 Last Exchange ────────────────────────────╮
│                                                                              │
│ USER: That's really helpful! Can you show me a practical example of a      │
│ custom decorator for timing functions?                                       │
│                                                                              │
│ ASSISTANT: Absolutely! Here's a practical timing decorator that you can     │
│ use to measure function execution time...                                    │
│                                                                              │
╰─────────────────────────────────────────────────────────────────────────────╯

Cost Breakdown by Turn:
┏━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Turn   ┃ Prompt Tokens  ┃ Completion Tokens   ┃ Cost       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│   1    │            25  │                 187 │ $0.0034    │
│   2    │           156  │                 234 │ $0.0062    │
│   3    │           234  │                 189 │ $0.0078    │
│   4    │           289  │                 156 │ $0.0087    │
│   5    │           334  │                 201 │ $0.0097    │
│ ...    │           ...  │                 ... │ ...        │
└────────┴────────────────┴─────────────────────┴────────────┘

Actions available:
• Resume the session: llm sessions resume ./runs/session_20240108_143022.json
• List all sessions: llm sessions list
```

### Resuming Sessions

```bash
# Resume a specific session
llm sessions resume ./runs/session_20240108_143022.json

# Output:
🔄 Resuming session: session_20240108_143022.json
Model: openai/gpt-4o-mini
Previous turns: 8
Tokens used: 2,456

🤖 Continuing chat with openai/gpt-4o-mini
💰 Budget: Unlimited | Previous cost: $0.0367 | Type ':help' for commands

[Previous conversation context is loaded]

You: Let's continue with more advanced decorator examples...
```

## Session Analysis

### Usage Patterns

You can analyze your session files to understand usage patterns:

```bash
# List sessions sorted by cost
llm sessions list | sort -k6 -nr

# Count sessions by model
grep -h '"model"' ./runs/*.json | sort | uniq -c

# Example output:
     12 "model": "openai/gpt-4o-mini"
      8 "model": "anthropic/claude-3-haiku" 
      3 "model": "openai/gpt-4o"
```

### Token Usage Analysis

```python
#!/usr/bin/env python3
"""
Analyze token usage across all sessions.
"""

import json
import glob
from collections import defaultdict
from pathlib import Path

def analyze_sessions(sessions_dir="./runs"):
    """Analyze all sessions in directory."""
    
    stats = defaultdict(list)
    total_cost = 0
    total_tokens = 0
    
    for session_file in glob.glob(f"{sessions_dir}/*.json"):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            model = session['model']
            usage = session.get('usage_totals', {})
            tokens = usage.get('total_tokens', 0)
            cost = sum(turn.get('cost_estimate', 0) for turn in session.get('turns', []))
            
            stats[model].append({
                'tokens': tokens,
                'cost': cost,
                'turns': len(session.get('turns', []))
            })
            
            total_cost += cost
            total_tokens += tokens
            
        except Exception as e:
            print(f"Error reading {session_file}: {e}")
    
    # Print summary
    print(f"📊 Session Analysis Summary")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Tokens: {total_tokens:,}")
    print()
    
    for model, sessions in stats.items():
        model_tokens = sum(s['tokens'] for s in sessions)
        model_cost = sum(s['cost'] for s in sessions)
        model_turns = sum(s['turns'] for s in sessions)
        
        print(f"🤖 {model}")
        print(f"  Sessions: {len(sessions)}")
        print(f"  Tokens: {model_tokens:,}")
        print(f"  Cost: ${model_cost:.4f}")
        print(f"  Turns: {model_turns}")
        print(f"  Avg tokens/session: {model_tokens//len(sessions):,}")
        print()

if __name__ == "__main__":
    analyze_sessions()
```

### Cost Tracking

```bash
# Calculate total spending
python3 -c "
import json, glob
total = sum(
    sum(turn.get('cost_estimate', 0) for turn in json.load(open(f)).get('turns', []))
    for f in glob.glob('./runs/*.json')
)
print(f'Total spent: \${total:.4f}')
"

# Example output:
Total spent: $2.4567
```

## Advanced Usage

### Session Export

Export sessions to different formats:

```python
#!/usr/bin/env python3
"""
Export session to different formats.
"""

import json
import argparse
from datetime import datetime

def export_session(session_file, format_type='txt'):
    """Export session to specified format."""
    
    with open(session_file, 'r') as f:
        session = json.load(f)
    
    if format_type == 'txt':
        return export_to_text(session)
    elif format_type == 'md':
        return export_to_markdown(session)
    elif format_type == 'csv':
        return export_to_csv(session)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

def export_to_text(session):
    """Export session to plain text."""
    
    output = []
    output.append(f"Session: {session.get('model', 'Unknown')}")
    output.append(f"Created: {session.get('created_at', 'Unknown')}")
    
    if session.get('system'):
        output.append(f"System: {session['system']}")
    
    output.append("=" * 50)
    output.append("")
    
    for i, turn in enumerate(session.get('turns', []), 1):
        messages = turn.get('messages', [])
        
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            output.append(f"{role}: {content}")
            output.append("")
        
        # Add turn stats
        usage = turn.get('usage', {})
        if usage:
            tokens = usage.get('total_tokens', 0)
            cost = turn.get('cost_estimate', 0)
            latency = turn.get('latency_ms', 0)
            output.append(f"[Turn {i} - Tokens: {tokens}, Cost: ${cost:.4f}, Time: {latency:.0f}ms]")
            output.append("")
    
    return "\n".join(output)

def export_to_markdown(session):
    """Export session to Markdown format."""
    
    output = []
    output.append(f"# Chat Session")
    output.append("")
    output.append(f"**Model:** {session.get('model', 'Unknown')}")
    output.append(f"**Created:** {session.get('created_at', 'Unknown')}")
    
    if session.get('system'):
        output.append(f"**System Prompt:** {session['system']}")
    
    output.append("")
    output.append("## Conversation")
    output.append("")
    
    for i, turn in enumerate(session.get('turns', []), 1):
        messages = turn.get('messages', [])
        
        for msg in messages:
            role = "👤 **User**" if msg['role'] == 'user' else "🤖 **Assistant**"
            content = msg['content']
            output.append(f"{role}: {content}")
            output.append("")
        
        # Add turn stats as collapsible section
        usage = turn.get('usage', {})
        if usage:
            tokens = usage.get('total_tokens', 0)
            cost = turn.get('cost_estimate', 0)
            latency = turn.get('latency_ms', 0)
            
            output.append("<details>")
            output.append(f"<summary>Turn {i} Statistics</summary>")
            output.append("")
            output.append(f"- **Tokens:** {tokens}")
            output.append(f"- **Cost:** ${cost:.4f}")
            output.append(f"- **Latency:** {latency:.0f}ms")
            output.append("")
            output.append("</details>")
            output.append("")
    
    return "\n".join(output)

# Usage example
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export session to different formats')
    parser.add_argument('session_file', help='Path to session JSON file')
    parser.add_argument('--format', choices=['txt', 'md', 'csv'], default='txt', 
                       help='Export format')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        result = export_session(args.session_file, args.format)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"Exported to {args.output}")
        else:
            print(result)
            
    except Exception as e:
        print(f"Export failed: {e}")
```

### Session Filtering

Filter sessions by various criteria:

```python
#!/usr/bin/env python3
"""
Filter sessions by various criteria.
"""

import json
import glob
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def filter_sessions(sessions_dir="./runs", **filters):
    """Filter sessions based on criteria."""
    
    matching_sessions = []
    
    for session_file in glob.glob(f"{sessions_dir}/*.json"):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            session['filename'] = Path(session_file).name
            
            if matches_filters(session, filters):
                matching_sessions.append(session)
                
        except Exception as e:
            print(f"Error reading {session_file}: {e}")
    
    return matching_sessions

def matches_filters(session, filters):
    """Check if session matches all filters."""
    
    # Model filter
    if filters.get('model') and filters['model'] not in session.get('model', ''):
        return False
    
    # Date range filter
    if filters.get('since'):
        created_at = datetime.fromisoformat(session.get('created_at', ''))
        if created_at < filters['since']:
            return False
    
    # Minimum turns filter
    if filters.get('min_turns'):
        turns = len(session.get('turns', []))
        if turns < filters['min_turns']:
            return False
    
    # Cost range filter
    if filters.get('min_cost') or filters.get('max_cost'):
        total_cost = sum(turn.get('cost_estimate', 0) for turn in session.get('turns', []))
        if filters.get('min_cost') and total_cost < filters['min_cost']:
            return False
        if filters.get('max_cost') and total_cost > filters['max_cost']:
            return False
    
    # System prompt filter
    if filters.get('system_contains'):
        system = session.get('system', '').lower()
        if filters['system_contains'].lower() not in system:
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Filter chat sessions')
    parser.add_argument('--dir', default='./runs', help='Sessions directory')
    parser.add_argument('--model', help='Filter by model (substring match)')
    parser.add_argument('--since', help='Filter by date (YYYY-MM-DD)')
    parser.add_argument('--min-turns', type=int, help='Minimum number of turns')
    parser.add_argument('--min-cost', type=float, help='Minimum cost')
    parser.add_argument('--max-cost', type=float, help='Maximum cost')
    parser.add_argument('--system-contains', help='Filter by system prompt content')
    parser.add_argument('--format', choices=['list', 'table', 'json'], default='list',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Prepare filters
    filters = {}
    if args.model:
        filters['model'] = args.model
    if args.since:
        filters['since'] = datetime.strptime(args.since, '%Y-%m-%d')
    if args.min_turns:
        filters['min_turns'] = args.min_turns
    if args.min_cost:
        filters['min_cost'] = args.min_cost
    if args.max_cost:
        filters['max_cost'] = args.max_cost
    if args.system_contains:
        filters['system_contains'] = args.system_contains
    
    # Filter sessions
    sessions = filter_sessions(args.dir, **filters)
    
    # Output results
    if args.format == 'json':
        print(json.dumps(sessions, indent=2, default=str))
    elif args.format == 'table':
        print_table(sessions)
    else:
        print_list(sessions)

def print_list(sessions):
    """Print sessions as a simple list."""
    print(f"Found {len(sessions)} matching sessions:")
    for session in sessions:
        turns = len(session.get('turns', []))
        cost = sum(turn.get('cost_estimate', 0) for turn in session.get('turns', []))
        model = session.get('model', 'Unknown')[:20]
        print(f"  {session['filename']} - {model} - {turns} turns - ${cost:.4f}")

def print_table(sessions):
    """Print sessions in table format."""
    if not sessions:
        print("No matching sessions found.")
        return
    
    print(f"{'Filename':<30} {'Model':<20} {'Turns':<6} {'Cost':<10}")
    print("-" * 70)
    
    for session in sessions:
        filename = session['filename'][:29]
        model = session.get('model', 'Unknown')[:19]
        turns = len(session.get('turns', []))
        cost = sum(turn.get('cost_estimate', 0) for turn in session.get('turns', []))
        
        print(f"{filename:<30} {model:<20} {turns:<6} ${cost:<9.4f}")

if __name__ == "__main__":
    main()
```

### Usage Examples

```bash
# Filter by model
python3 filter_sessions.py --model anthropic --format table

# Filter by date and cost
python3 filter_sessions.py --since 2024-01-01 --min-cost 0.01 --format table

# Find long conversations
python3 filter_sessions.py --min-turns 10 --format list

# Find coding sessions
python3 filter_sessions.py --system-contains "programming" --format table
```

## Best Practices

### Session Organization

1. **Use descriptive filenames** when saving manually:
   ```bash
   You: :save python_debugging_session_2024
   You: :save machine_learning_discussion
   You: :save code_review_feedback
   ```

2. **Create topic-specific directories**:
   ```bash
   mkdir -p sessions/{programming,writing,research}
   
   # Use different directories for different purposes
   llm chat --model gpt-4 --save-dir ./sessions/programming
   llm chat --model claude-3 --save-dir ./sessions/writing
   ```

3. **Tag sessions with metadata**:
   ```json
   {
     "meta": {
       "tags": ["python", "debugging", "performance"],
       "project": "web-scraper",
       "importance": "high"
     }
   }
   ```

### Session Hygiene

1. **Regular cleanup**:
   ```bash
   # Remove sessions older than 30 days
   find ./runs -name "*.json" -mtime +30 -delete
   
   # Archive old sessions
   mkdir -p archive/$(date +%Y-%m)
   mv ./runs/session_2024-01-*.json archive/2024-01/
   ```

2. **Backup important sessions**:
   ```bash
   # Create backup of important sessions
   rsync -av ./runs/ ./backup/sessions/
   
   # Or use git for version control
   git add runs/
   git commit -m "Update session backups"
   ```

3. **Session size management**:
   ```bash
   # Find large sessions
   find ./runs -name "*.json" -size +1M -ls
   
   # Compress old sessions
   gzip ./runs/session_2023-*.json
   ```

### Performance Tips

1. **Session directory optimization**:
   - Keep active sessions in fast storage (SSD)
   - Archive old sessions to slower storage
   - Use indexed directories for large collections

2. **Memory management**:
   - Very long conversations can consume significant memory
   - Consider splitting long sessions into multiple parts
   - Use session filtering to work with subsets

3. **Load time optimization**:
   ```bash
   # Pre-filter sessions to reduce load time
   llm sessions list --dir ./recent-sessions
   
   # Use specific session names instead of listing all
   llm sessions show ./runs/important_session.json
   ```

## Troubleshooting

### Common Issues

#### Session File Corruption

```bash
# Check if session file is valid JSON
python3 -m json.tool ./runs/session_file.json > /dev/null
echo $? # 0 = valid, non-zero = invalid

# Validate session structure
python3 -c "
import json
with open('./runs/session_file.json') as f:
    session = json.load(f)
assert 'model' in session
assert 'turns' in session
print('Session file is valid')
"
```

#### Recovering Corrupted Sessions

```python
#!/usr/bin/env python3
"""
Attempt to recover corrupted session files.
"""

import json
import re
from pathlib import Path

def recover_session(filename):
    """Attempt to recover a corrupted session file."""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Try to extract valid JSON parts
    json_objects = []
    
    # Look for complete JSON objects
    brace_level = 0
    start_pos = None
    
    for i, char in enumerate(content):
        if char == '{':
            if brace_level == 0:
                start_pos = i
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0 and start_pos is not None:
                try:
                    obj = json.loads(content[start_pos:i+1])
                    json_objects.append(obj)
                except json.JSONDecodeError:
                    pass
                start_pos = None
    
    # Try to reconstruct session
    if json_objects:
        session = json_objects[0]  # Assume first is the main session
        
        # Validate required fields
        if 'model' not in session:
            session['model'] = 'unknown'
        if 'turns' not in session:
            session['turns'] = []
        if 'created_at' not in session:
            session['created_at'] = '2024-01-01T00:00:00'
        
        # Save recovered session
        backup_name = f"{filename}.backup"
        Path(filename).rename(backup_name)
        
        with open(filename, 'w') as f:
            json.dump(session, f, indent=2)
        
        print(f"Recovered session saved to {filename}")
        print(f"Original backed up to {backup_name}")
        return True
    
    print(f"Could not recover {filename}")
    return False

# Usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 recover_session.py <session_file.json>")
        sys.exit(1)
    
    recover_session(sys.argv[1])
```

#### Permission Issues

```bash
# Fix session directory permissions
chmod 755 ./runs
chmod 644 ./runs/*.json

# Check disk space
df -h ./runs

# Check file ownership
ls -la ./runs/
```

#### Large Session Files

```bash
# Check session file sizes
du -h ./runs/*.json | sort -hr

# Compress large sessions
for file in ./runs/*.json; do
    if [ $(stat -c%s "$file") -gt 1048576 ]; then  # > 1MB
        echo "Compressing $file"
        gzip "$file"
    fi
done
```

### Debug Mode

Enable debug mode to troubleshoot session issues:

```bash
# Enable debug logging
LLM_DEBUG=1 llm sessions list

# Check session file validation
LLM_DEBUG=1 llm sessions show ./runs/problematic_session.json

# Debug session resume
LLM_DEBUG=1 llm sessions resume ./runs/session.json
```

### Recovery Strategies

1. **Incremental backups**:
   ```bash
   # Create timestamped backups
   rsync -av ./runs/ "./backups/sessions-$(date +%Y%m%d-%H%M%S)/"
   ```

2. **Session validation script**:
   ```python
   #!/usr/bin/env python3
   """Validate all session files."""
   
   import json
   import glob
   from pathlib import Path
   
   def validate_sessions(directory="./runs"):
       """Validate all session files in directory."""
       
       valid_count = 0
       invalid_files = []
       
       for session_file in glob.glob(f"{directory}/*.json"):
           try:
               with open(session_file, 'r') as f:
                   session = json.load(f)
               
               # Check required fields
               required_fields = ['model', 'turns', 'created_at']
               for field in required_fields:
                   if field not in session:
                       raise ValueError(f"Missing required field: {field}")
               
               valid_count += 1
               
           except Exception as e:
               invalid_files.append((session_file, str(e)))
       
       print(f"✅ {valid_count} valid session files")
       if invalid_files:
           print(f"❌ {len(invalid_files)} invalid session files:")
           for filename, error in invalid_files:
               print(f"   {Path(filename).name}: {error}")
       
       return len(invalid_files) == 0
   
   if __name__ == "__main__":
       validate_sessions()
   ```

3. **Automated cleanup**:
   ```bash
   #!/bin/bash
   # Session cleanup script
   
   SESSIONS_DIR="./runs"
   BACKUP_DIR="./backup/sessions"
   
   # Create backup directory
   mkdir -p "$BACKUP_DIR"
   
   # Backup all sessions
   rsync -av "$SESSIONS_DIR/" "$BACKUP_DIR/"
   
   # Remove empty sessions
   find "$SESSIONS_DIR" -name "*.json" -size 0 -delete
   
   # Archive sessions older than 30 days
   find "$SESSIONS_DIR" -name "session_*.json" -mtime +30 \
       -exec mv {} ./archive/ \;
   
   # Compress large sessions
   find "$SESSIONS_DIR" -name "*.json" -size +1M \
       -exec gzip {} \;
   
   echo "Session cleanup completed"
   ```

---

**Next Steps:**
- [Getting Started Guide](GETTING_STARTED.md) - Basic setup and usage
- [Commands Reference](COMMANDS_REFERENCE.md) - Complete command documentation  
- [Budget Management](BUDGET_MANAGEMENT.md) - Cost control and optimization