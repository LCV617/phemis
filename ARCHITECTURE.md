# 🏗️ Architecture Documentation

Technical overview of the LLM CLI tool architecture, design patterns, and extension points.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Core Components](#core-components)
- [Design Patterns](#design-patterns)
- [Data Models](#data-models)
- [Extension Points](#extension-points)
- [Development Guidelines](#development-guidelines)
- [Testing Strategy](#testing-strategy)

## Overview

The LLM CLI tool follows a modular, layered architecture that separates concerns and enables easy extension:

```
┌─────────────────────────────────────────┐
│              CLI Layer                  │
│   (Commands, Arguments, User Interface) │
├─────────────────────────────────────────┤
│             Core Layer                  │
│  (Business Logic, Session Management)   │
├─────────────────────────────────────────┤
│           Provider Layer                │
│     (API Integration, Networking)       │
├─────────────────────────────────────────┤
│            Storage Layer                │
│     (File I/O, Session Persistence)     │
└─────────────────────────────────────────┘
```

### Key Design Principles

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Dependency Injection**: Core components are loosely coupled
- **Configuration-Driven**: Behavior controlled through config files
- **Extensible**: New providers and commands can be added easily
- **Testable**: Each component can be tested in isolation
- **Rich User Experience**: Beautiful terminal output with progress indicators

## Directory Structure

```
phemis/
├── llm/                          # Main package
│   ├── __init__.py              # Package initialization
│   ├── cli/                     # CLI command layer
│   │   ├── __init__.py
│   │   ├── main.py              # App setup and global commands
│   │   ├── ask.py               # Single Q&A command
│   │   ├── chat.py              # Interactive chat command
│   │   ├── models.py            # Model management commands
│   │   └── sessions.py          # Session management commands
│   └── core/                    # Core business logic
│       ├── __init__.py
│       ├── provider_openrouter.py  # OpenRouter API client
│       ├── session.py           # Session management logic
│       ├── schema.py            # Pydantic data models
│       ├── storage.py           # File I/O operations
│       ├── cost.py              # Cost calculation utilities
│       └── utils.py             # Helper functions
├── docs/                        # Documentation
├── examples/                    # Usage examples
├── tests/                       # Test suite
├── pyproject.toml              # Package configuration
├── requirements.txt            # Dependencies
└── README.md                   # Main documentation
```

## Core Components

### CLI Layer (`llm/cli/`)

**Purpose**: Handle user interaction, command parsing, and output formatting.

#### `main.py` - Application Bootstrap
```python
# Key responsibilities:
- Initialize Typer application
- Set up global error handling
- Configure logging and debugging
- Register sub-commands
- Handle version display and help
```

**Key Features**:
- Global error handling with user-friendly messages
- Environment variable validation
- Rich console output with colors and formatting
- Extensible command registration system

#### `ask.py` - Single Question Handler
```python
# Key responsibilities:
- Parse question and model parameters
- Handle streaming responses in real-time
- Format output (text or JSON)
- Calculate and display cost estimates
```

**Key Features**:
- Real-time response streaming
- JSON output for automation
- Cost tracking and display
- Error handling with helpful suggestions

#### `models.py` - Model Management
```python
# Key responsibilities:
- List and filter available models
- Display detailed model information
- Format pricing and capability data
- Handle model search and suggestions
```

**Key Features**:
- Rich table formatting for model lists
- Advanced filtering and search
- Cost comparison utilities
- Model recommendation engine

#### `sessions.py` - Session Management
```python
# Key responsibilities:
- List and manage saved sessions
- Display session summaries and details
- Handle session resumption
- Provide session analytics
```

**Key Features**:
- Session file validation
- Rich session summaries
- Cost breakdown analysis
- Session search and filtering

### Core Layer (`llm/core/`)

**Purpose**: Implement business logic, data processing, and provider abstraction.

#### `provider_openrouter.py` - API Provider
```python
class OpenRouterProvider:
    """
    Main API provider for OpenRouter integration.
    
    Features:
    - HTTP client with retry logic
    - Streaming response handling
    - Rate limiting and error handling
    - Model listing and information retrieval
    """
    
    def __init__(self, api_key: str, timeout: float = 60.0):
        # Initialize with configuration
        
    def list_models(self) -> List[ModelInfo]:
        # Fetch and parse available models
        
    def chat_completion(self, messages: List[Message], 
                       model: str, stream: bool = False):
        # Execute chat completion with streaming support
```

**Key Features**:
- Robust HTTP client with exponential backoff
- Streaming response parsing
- Comprehensive error handling
- Model caching and validation

#### `session.py` - Session Management
```python
class ChatSession:
    """
    Manages conversation state and history.
    
    Features:
    - Message history tracking
    - Token usage accumulation
    - Cost calculation
    - Persistence integration
    """
    
    def __init__(self, model: str, system: Optional[str] = None):
        # Initialize session with model and system prompt
        
    def add_turn(self, turn: Turn):
        # Add conversation turn with usage tracking
        
    def calculate_total_cost(self) -> float:
        # Calculate cumulative session cost
        
    def to_dict(self) -> Dict[str, Any]:
        # Serialize for storage
```

**Key Features**:
- Conversation state management
- Automatic cost tracking
- Usage statistics accumulation
- JSON serialization support

#### `schema.py` - Data Models
```python
# Pydantic models for type safety and validation

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Turn(BaseModel):
    messages: List[Message]
    usage: Optional[Usage] = None
    latency_ms: Optional[float] = None
    cost_estimate: Optional[float] = None

class Session(BaseModel):
    model: str
    system: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    turns: List[Turn] = Field(default_factory=list)
    usage_totals: Optional[Usage] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
```

**Key Features**:
- Type safety with Pydantic validation
- Automatic serialization/deserialization
- Default value handling
- Extensible metadata support

#### `storage.py` - Persistence Layer
```python
class SessionStorage:
    """
    Handle session file operations.
    
    Features:
    - JSON file management
    - Session validation
    - Directory management
    - Backup and recovery
    """
    
    def save_session(self, session: Session, filepath: Path):
        # Save session to JSON file with validation
        
    def load_session(self, filepath: Path) -> Session:
        # Load and validate session from file
        
    def list_sessions(self, directory: Path) -> List[Path]:
        # Find all valid session files
```

**Key Features**:
- Atomic file operations
- JSON schema validation
- Error recovery mechanisms
- Directory management

### Provider Layer

**Purpose**: Abstract external API interactions and handle networking.

#### Provider Interface
```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """List available models."""
        
    @abstractmethod
    def chat_completion(self, messages: List[Message], 
                       model: str, **kwargs) -> Any:
        """Execute chat completion."""
        
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed model information."""
```

This abstraction allows easy addition of new providers (Anthropic direct, OpenAI direct, etc.).

## Design Patterns

### 1. Command Pattern
The CLI layer implements the Command pattern for extensible sub-commands:

```python
# Each command is a separate module with consistent interface
class Command:
    def execute(self, args: CommandArgs) -> CommandResult:
        pass
```

### 2. Factory Pattern
Provider creation uses the Factory pattern:

```python
class ProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, **config) -> LLMProvider:
        if provider_type == "openrouter":
            return OpenRouterProvider(**config)
        # Add more providers here
```

### 3. Observer Pattern
Session events can trigger observers for logging, analytics, etc.:

```python
class SessionEventObserver:
    def on_turn_completed(self, turn: Turn):
        # Handle turn completion
        
    def on_session_ended(self, session: Session):
        # Handle session end
```

### 4. Strategy Pattern
Different response formatting strategies:

```python
class ResponseFormatter(ABC):
    @abstractmethod
    def format_response(self, response: Any) -> str:
        pass

class TextFormatter(ResponseFormatter):
    def format_response(self, response: Any) -> str:
        # Format as plain text

class JSONFormatter(ResponseFormatter):
    def format_response(self, response: Any) -> str:
        # Format as JSON
```

### 5. Decorator Pattern
Cost tracking and timing decorators:

```python
def track_cost(func):
    """Decorator to track API call costs."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        # Track cost and timing
        return result
    return wrapper
```

## Data Models

### Core Data Flow

```
User Input → Command Parser → Core Logic → Provider → API
     ↓              ↓              ↓          ↓        ↓
  Validation → Session State → Cost Calc → HTTP → JSON
     ↓              ↓              ↓          ↓        ↓
   Storage ← Response Format ← Usage Stats ← Parse ← Response
```

### Key Data Structures

#### Session Lifecycle
```python
# 1. Session Creation
session = Session(model="gpt-4", system="You are helpful")

# 2. Turn Addition
turn = Turn(
    messages=[user_message, assistant_message],
    usage=Usage(prompt_tokens=50, completion_tokens=200),
    latency_ms=1500.0,
    cost_estimate=0.0025
)
session.add_turn(turn)

# 3. Persistence
storage.save_session(session, "session_20240108_143022.json")
```

#### Cost Calculation Pipeline
```python
# Token counting
tokens = count_tokens(message.content, model)

# Price lookup
model_info = provider.get_model_info(model)
input_price = model_info.pricing_prompt
output_price = model_info.pricing_completion

# Cost calculation
cost = (input_tokens * input_price) + (output_tokens * output_price)

# Accumulation
session.usage_totals.add_usage(tokens)
session.total_cost += cost
```

## Extension Points

### Adding New Commands

1. **Create command module** in `llm/cli/`:
```python
# llm/cli/newcommand.py
from typer import Typer

newcommand_app = Typer(name="newcommand")

@newcommand_app.command()
def do_something():
    # Implementation
    pass
```

2. **Register in main.py**:
```python
from .newcommand import newcommand_app
app.add_typer(newcommand_app, name="newcommand")
```

### Adding New Providers

1. **Implement provider interface**:
```python
# llm/core/provider_newapi.py
class NewAPIProvider(LLMProvider):
    def list_models(self) -> List[ModelInfo]:
        # Implementation
        
    def chat_completion(self, messages, model, **kwargs):
        # Implementation
```

2. **Register in factory**:
```python
# Update ProviderFactory to include new provider
```

### Adding New Storage Backends

1. **Implement storage interface**:
```python
class DatabaseStorage(SessionStorage):
    def save_session(self, session: Session, identifier: str):
        # Save to database
        
    def load_session(self, identifier: str) -> Session:
        # Load from database
```

### Adding New Output Formats

1. **Create formatter**:
```python
class MarkdownFormatter(ResponseFormatter):
    def format_response(self, response: ChatResponse) -> str:
        # Format as Markdown
```

2. **Register formatter**:
```python
FORMATTERS = {
    'text': TextFormatter(),
    'json': JSONFormatter(),
    'markdown': MarkdownFormatter(),
}
```

## Development Guidelines

### Code Style

- **Type Hints**: All functions must have type hints
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Explicit error handling with meaningful messages
- **Logging**: Use structured logging with appropriate levels

### Example Function Documentation
```python
def calculate_session_cost(
    session: Session, 
    model_pricing: Dict[str, ModelPricing]
) -> float:
    """
    Calculate the total cost for a session.
    
    Args:
        session: The session to calculate cost for
        model_pricing: Pricing information for models
        
    Returns:
        Total cost in USD
        
    Raises:
        ValueError: If session contains invalid usage data
        KeyError: If model pricing not found
    """
    # Implementation
```

### Configuration Management

Configuration follows a hierarchy:
1. Command line arguments (highest priority)
2. Environment variables
3. User config file (`~/.config/llm/config.json`)
4. Project config file (`.llm-config.json`)
5. Default values (lowest priority)

```python
class Config:
    def __init__(self):
        self.values = {}
        self._load_defaults()
        self._load_project_config()
        self._load_user_config()
        self._load_env_vars()
        
    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)
```

### Error Handling Strategy

```python
# Custom exception hierarchy
class LLMCLIError(Exception):
    """Base exception for LLM CLI errors."""
    
class ProviderError(LLMCLIError):
    """Provider-related errors."""
    
class SessionError(LLMCLIError):
    """Session management errors."""
    
class ConfigurationError(LLMCLIError):
    """Configuration-related errors."""

# Error handling in CLI commands
@handle_errors
def command_function():
    try:
        # Command logic
        pass
    except ProviderError as e:
        # Specific handling for provider errors
        console.print(f"[red]Provider Error:[/red] {e}")
        suggest_provider_solutions()
    except Exception as e:
        # Generic error handling
        console.print(f"[red]Unexpected Error:[/red] {e}")
```

## Testing Strategy

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_providers.py
│   ├── test_session.py
│   └── test_storage.py
├── integration/             # Integration tests
│   ├── test_cli_commands.py
│   └── test_end_to_end.py
├── fixtures/               # Test data
│   ├── sample_sessions/
│   └── mock_responses/
└── conftest.py            # Pytest configuration
```

### Unit Testing Patterns

```python
# Test session management
def test_session_cost_calculation():
    session = Session(model="gpt-4")
    turn = Turn(
        messages=[Message(role="user", content="test")],
        usage=Usage(prompt_tokens=10, completion_tokens=20),
        cost_estimate=0.001
    )
    session.add_turn(turn)
    
    assert session.calculate_total_cost() == 0.001

# Mock external dependencies
@pytest.fixture
def mock_openrouter_provider():
    provider = Mock(spec=OpenRouterProvider)
    provider.list_models.return_value = [
        ModelInfo(id="test-model", context_length=4096)
    ]
    return provider

def test_model_listing(mock_openrouter_provider):
    models = mock_openrouter_provider.list_models()
    assert len(models) == 1
    assert models[0].id == "test-model"
```

### Integration Testing

```python
# Test CLI commands
def test_ask_command_integration():
    result = runner.invoke(app, [
        "ask", 
        "What is 2+2?", 
        "--model", "test-model",
        "--json"
    ])
    
    assert result.exit_code == 0
    response_data = json.loads(result.stdout)
    assert "response" in response_data
    assert "usage" in response_data
```

### Performance Testing

```python
# Test response time requirements
def test_response_time_performance():
    start_time = time.time()
    
    # Execute command
    result = execute_ask_command("Simple question", "fast-model")
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # Should respond within 5 seconds for simple questions
    assert response_time < 5.0
```

---

This architecture supports the current functionality while providing clear extension points for future enhancements. The modular design ensures that new features can be added without disrupting existing functionality, and the comprehensive testing strategy maintains code quality as the project grows.