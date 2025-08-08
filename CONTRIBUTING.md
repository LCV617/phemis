# 🤝 Contributing Guide

Welcome to the LLM CLI project! This guide will help you set up your development environment and contribute effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Code Standards](#code-standards)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Getting Started

### Prerequisites

- **Python 3.9+** - The project requires modern Python features
- **Git** - For version control
- **OpenRouter API Key** - For testing API integrations
- **Virtual Environment** - Recommended for isolation

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes** - Fix existing issues
- ✨ **New features** - Add new functionality
- 📚 **Documentation** - Improve or add documentation
- 🧪 **Tests** - Add or improve test coverage
- 🎨 **UI/UX improvements** - Better terminal output and user experience
- 🔧 **Infrastructure** - CI/CD, build tools, deployment

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/phemis.git
cd phemis

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_USERNAME/phemis.git
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .
```

### 4. Set Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### 5. Configure Environment

```bash
# Create .env file for local configuration
cp .env.example .env

# Edit .env with your settings
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
export LLM_DEBUG=1
```

### 6. Verify Installation

```bash
# Test the CLI
llm --version

# Run tests
pytest

# Run linting
make lint

# Check formatting
make format-check
```

## Code Standards

### Code Style

We use several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **pytest** - Testing

### Formatting and Linting

```bash
# Format code
make format

# Check formatting (without changes)
make format-check

# Run linting
make lint

# Run type checking
make typecheck

# Run all checks
make check-all
```

### Code Quality Rules

#### 1. Type Hints

All functions must have complete type hints:

```python
# Good
def process_session(session: Session, model: str) -> SessionResult:
    """Process a chat session."""
    pass

# Bad
def process_session(session, model):
    """Process a chat session."""
    pass
```

#### 2. Error Handling

Always handle errors gracefully with meaningful messages:

```python
# Good
def load_session(filepath: Path) -> Session:
    """Load session from file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return Session.model_validate(data)
    except FileNotFoundError:
        raise SessionError(f"Session file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise SessionError(f"Invalid JSON in session file: {e}")
    except ValidationError as e:
        raise SessionError(f"Invalid session format: {e}")

# Bad
def load_session(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return Session.model_validate(data)
```

#### 3. Documentation

All public functions need docstrings in Google style:

```python
def calculate_session_cost(
    session: Session, 
    pricing_info: Dict[str, ModelPricing]
) -> float:
    """
    Calculate total cost for a session.
    
    Args:
        session: The session to analyze
        pricing_info: Model pricing information
        
    Returns:
        Total cost in USD
        
    Raises:
        ValueError: If session has invalid usage data
        KeyError: If model pricing not available
        
    Example:
        >>> session = Session(model="gpt-4", turns=[...])
        >>> pricing = {"gpt-4": ModelPricing(...)}
        >>> cost = calculate_session_cost(session, pricing)
        >>> print(f"Cost: ${cost:.4f}")
    """
    pass
```

#### 4. Constants and Configuration

Use constants instead of magic numbers:

```python
# Good
DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 3
COST_PRECISION = 6

def make_request(url: str, timeout: float = DEFAULT_TIMEOUT) -> Response:
    pass

# Bad
def make_request(url: str, timeout: float = 60.0) -> Response:
    pass
```

### Project Structure Guidelines

#### File Organization
- **One class per file** (with exceptions for small utility classes)
- **Logical grouping** of related functions
- **Clear module boundaries** between CLI, core, and provider layers

#### Import Organization
```python
# Standard library imports
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

# Third-party imports
import typer
from rich.console import Console
from pydantic import BaseModel

# Local imports
from ..core.session import Session
from ..core.provider_openrouter import OpenRouterProvider
from .utils import format_cost
```

## Development Workflow

### Branch Naming

Use descriptive branch names:

```bash
# Feature branches
git checkout -b feature/add-session-export
git checkout -b feature/improve-error-messages

# Bug fix branches
git checkout -b fix/session-loading-crash
git checkout -b fix/cost-calculation-error

# Documentation branches
git checkout -b docs/update-getting-started
git checkout -b docs/add-api-examples
```

### Commit Messages

Follow conventional commit format:

```bash
# Format: type(scope): description

feat(cli): add session export command
fix(core): resolve cost calculation rounding error
docs(readme): update installation instructions
test(sessions): add integration tests for session loading
refactor(providers): simplify error handling
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

### Development Process

1. **Create Issue** - Describe the problem or feature
2. **Create Branch** - Use descriptive name
3. **Implement Changes** - Follow code standards
4. **Write Tests** - Ensure good coverage
5. **Update Documentation** - Keep docs in sync
6. **Run Checks** - Lint, format, test
7. **Create Pull Request** - Use template
8. **Address Review** - Respond to feedback
9. **Merge** - Squash and merge

## Testing

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── cli/
│   │   ├── test_ask.py
│   │   ├── test_models.py
│   │   └── test_sessions.py
│   ├── core/
│   │   ├── test_session.py
│   │   ├── test_storage.py
│   │   └── test_cost.py
│   └── providers/
│       └── test_openrouter.py
├── integration/             # End-to-end tests
│   ├── test_cli_integration.py
│   └── test_session_workflow.py
├── fixtures/               # Test data
│   ├── sample_sessions/
│   ├── mock_responses/
│   └── test_configs/
└── conftest.py            # Pytest configuration
```

### Writing Tests

#### Unit Tests
```python
# tests/unit/core/test_session.py
import pytest
from datetime import datetime
from llm.core.session import Session, Turn
from llm.core.schema import Message, Usage, MessageRole

class TestSession:
    """Test session management functionality."""
    
    def test_session_creation(self):
        """Test basic session creation."""
        session = Session(model="gpt-4", system="Test system")
        
        assert session.model == "gpt-4"
        assert session.system == "Test system"
        assert len(session.turns) == 0
        assert isinstance(session.created_at, datetime)
    
    def test_add_turn(self):
        """Test adding turns to session."""
        session = Session(model="gpt-4")
        
        turn = Turn(
            messages=[
                Message(role=MessageRole.USER, content="Hello"),
                Message(role=MessageRole.ASSISTANT, content="Hi there!")
            ],
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            cost_estimate=0.001
        )
        
        session.add_turn(turn)
        
        assert len(session.turns) == 1
        assert session.usage_totals.total_tokens == 30
        assert session.calculate_total_cost() == 0.001
    
    @pytest.mark.parametrize("model,expected_type", [
        ("gpt-4", "openai"),
        ("claude-3", "anthropic"),
        ("llama-2", "meta"),
    ])
    def test_model_provider_detection(self, model, expected_type):
        """Test model provider detection."""
        session = Session(model=model)
        assert session.get_provider_type() == expected_type
```

#### Integration Tests
```python
# tests/integration/test_cli_integration.py
import pytest
import tempfile
import json
from pathlib import Path
from typer.testing import CliRunner
from llm.cli.main import app

class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_ask_command_json_output(self):
        """Test ask command with JSON output."""
        result = self.runner.invoke(app, [
            "ask",
            "What is 2+2?",
            "--model", "openai/gpt-4o-mini",
            "--json"
        ])
        
        assert result.exit_code == 0
        
        # Parse JSON response
        response_data = json.loads(result.stdout)
        assert "question" in response_data
        assert "response" in response_data
        assert "model" in response_data
        assert "usage" in response_data
        assert response_data["question"] == "What is 2+2?"
    
    def test_session_workflow(self):
        """Test complete session workflow."""
        # Create session directory
        sessions_dir = Path(self.temp_dir) / "sessions"
        sessions_dir.mkdir()
        
        # Start chat and save session
        # (This would be more complex in reality)
        
        # List sessions
        result = self.runner.invoke(app, [
            "sessions", "list",
            "--dir", str(sessions_dir)
        ])
        
        assert result.exit_code == 0
```

### Mock Testing

Use mocks for external dependencies:

```python
# tests/unit/providers/test_openrouter.py
import pytest
from unittest.mock import Mock, patch
from llm.core.provider_openrouter import OpenRouterProvider

@pytest.fixture
def mock_requests():
    """Mock requests module."""
    with patch('llm.core.provider_openrouter.requests') as mock:
        yield mock

def test_list_models_success(mock_requests):
    """Test successful model listing."""
    # Configure mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "openai/gpt-4o-mini",
                "context_length": 128000,
                "pricing": {
                    "prompt": "0.00015",
                    "completion": "0.0006"
                }
            }
        ]
    }
    mock_requests.get.return_value = mock_response
    
    # Test
    provider = OpenRouterProvider(api_key="test-key")
    models = provider.list_models()
    
    assert len(models) == 1
    assert models[0].id == "openai/gpt-4o-mini"
    assert models[0].context_length == 128000
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/core/test_session.py

# Run tests with coverage
pytest --cov=llm --cov-report=html

# Run tests matching pattern
pytest -k "test_session"

# Run tests with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/

# Run fast tests (exclude slow markers)
pytest -m "not slow"
```

### Test Configuration

```python
# conftest.py
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_sessions_dir():
    """Create temporary directory for sessions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_openrouter_provider():
    """Mock OpenRouter provider."""
    provider = Mock()
    provider.list_models.return_value = []
    provider.chat_completion.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 50}
    }
    return provider

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("LLM_DEBUG", "1")
```

## Documentation

### Types of Documentation

1. **Code Documentation** - Docstrings and comments
2. **User Documentation** - README, guides, examples
3. **API Documentation** - Auto-generated from docstrings
4. **Architecture Documentation** - High-level design docs

### Documentation Standards

#### Docstring Format
```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    param3: Dict[str, Any] = None
) -> Tuple[bool, List[str]]:
    """
    Brief one-line description of the function.
    
    Longer description explaining what the function does,
    how it works, and any important details.
    
    Args:
        param1: Description of the first parameter
        param2: Description of optional parameter with default
        param3: Description of dict parameter, defaults to empty dict
        
    Returns:
        Tuple containing:
            - bool: Success status
            - List[str]: List of result messages
            
    Raises:
        ValueError: If param1 is empty
        TypeError: If param3 is not a dictionary
        CustomError: In specific error conditions
        
    Example:
        >>> success, messages = complex_function("test", param2=42)
        >>> print(f"Success: {success}")
        >>> for msg in messages:
        ...     print(f"Message: {msg}")
        
    Note:
        This function has side effects and modifies global state.
        
    Warning:
        This function is deprecated, use new_function() instead.
    """
    pass
```

#### README Updates
When adding new features, update:
- Feature list in main README
- Installation instructions (if needed)
- Usage examples
- Command reference

#### User Guide Updates
- Add new command documentation
- Update workflow examples
- Add troubleshooting sections
- Include performance notes

### Building Documentation

```bash
# Generate API documentation
make docs-api

# Build user documentation
make docs-build

# Serve documentation locally
make docs-serve

# Check documentation for issues
make docs-check
```

## Pull Request Process

### PR Template

When creating a pull request, use this template:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- Detailed list of changes
- Include any breaking changes
- Note any new dependencies

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new functionality
- [ ] Updated existing tests if needed
- [ ] Manual testing performed

## Documentation
- [ ] Updated docstrings
- [ ] Updated user documentation
- [ ] Updated README if needed
- [ ] Added examples if applicable

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented where necessary
- [ ] No new linting errors
- [ ] All tests pass
- [ ] Documentation is updated

## Screenshots (if applicable)
Include screenshots for UI changes.

## Additional Context
Any additional information about the PR.
```

### PR Review Process

1. **Automated Checks** - CI/CD runs tests and linting
2. **Code Review** - Maintainers review code quality
3. **Testing** - Manual testing of new functionality
4. **Documentation Review** - Check docs are complete
5. **Final Approval** - Approved by maintainer
6. **Merge** - Squash and merge to main

### Review Criteria

Reviewers will check for:

- **Functionality** - Does it work as expected?
- **Code Quality** - Follows project standards?
- **Test Coverage** - Adequate tests included?
- **Documentation** - Complete and accurate?
- **Performance** - No significant performance regressions?
- **Security** - No security vulnerabilities?
- **Compatibility** - Works with existing features?

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **Major version** (X.y.z) - Breaking changes
- **Minor version** (x.Y.z) - New features, backward compatible
- **Patch version** (x.y.Z) - Bug fixes, backward compatible

### Release Workflow

1. **Feature Freeze** - Stop adding new features
2. **Testing** - Comprehensive testing of release candidate
3. **Documentation** - Update changelog and docs
4. **Version Bump** - Update version in `pyproject.toml`
5. **Tag Release** - Create git tag
6. **Build Package** - Build distribution packages
7. **Publish** - Upload to PyPI
8. **Announce** - Update README and announce release

### Changelog Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2024-01-08

### Added
- New session export functionality
- Support for custom system prompts in batch mode
- Cost optimization suggestions in session analysis

### Changed
- Improved error messages for authentication failures
- Updated model pricing information
- Enhanced session loading performance

### Fixed
- Fixed session file corruption issue
- Resolved memory leak in long conversations
- Fixed cost calculation edge cases

### Deprecated
- Old session format support (will be removed in 2.0.0)

### Security
- Updated dependencies to fix security vulnerabilities
```

---

Thank you for contributing to the LLM CLI project! Your contributions help make this tool better for everyone. If you have questions, feel free to open an issue or reach out to the maintainers.