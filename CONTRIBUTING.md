# Contributing to Airflow MCP Server

Thank you for your interest in contributing! This document provides guidelines for contributing code, documentation, and bug reports.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Commit Messages](#commit-messages)
7. [Pull Request Process](#pull-request-process)
8. [Bug Reports](#bug-reports)
9. [Feature Requests](#feature-requests)
10. [Documentation](#documentation)

---

## Code of Conduct

Be respectful, inclusive, and professional. We are committed to providing a welcoming environment for all contributors regardless of background or experience level.

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **uv** package manager (install: `pip install uv`)
- **Git** (for version control)
- Active **Airflow instance** for integration testing (Docker Compose recommended)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Adrien-Crapart/airflow-mcp-server.git
cd airflow-mcp-server

# Create virtual environment and install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your Airflow credentials

# Run development server
uv run uvicorn airflow_mcp_server.server:create_app --factory --reload --host 127.0.0.1 --port 8000
```

### Verify Installation

```bash
# Run unit tests
uv run pytest tests/unit -v

# Run health check
curl http://localhost:8000/health
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name

# Branch naming convention:
# - feature/xxx      for new features
# - fix/xxx          for bug fixes
# - docs/xxx         for documentation
# - refactor/xxx     for code refactoring
# - test/xxx         for test improvements
```

### 2. Make Changes

- Keep commits **atomic** (one logical change per commit)
- Write descriptive commit messages (see [Commit Messages](#commit-messages))
- Ensure code passes linting before committing

```bash
# Format code
uv run ruff format .

# Check for lint issues
uv run ruff check . --fix

# Type-check (optional but recommended)
uv run mypy airflow_mcp_server/
```

### 3. Write/Update Tests

All new features should include tests:

```bash
# Unit test example (handlers/test_dags.py)
@pytest.mark.asyncio
async def test_trigger_dag(mock_airflow_client):
    result = await trigger_dag({"dag_id": "test_dag"})
    assert result["success"] is True
    mock_airflow_client.trigger_dag.assert_called_once_with("test_dag")
```

Run tests locally:

```bash
# Unit tests only (fast)
uv run pytest tests/unit -v

# With integration (requires Airflow)
uv run pytest -v

# Specific test file
uv run pytest tests/unit/test_dags.py -v

# With coverage
uv run pytest --cov=airflow_mcp_server tests/
```

### 4. Add Documentation

Update relevant docs for user-facing changes:

- **New tool**: Add entry to `docs/mcp_tools.md`
- **Architecture change**: Update `docs/architecture.md`
- **API change**: Update docstring in handler function
- **Setup change**: Update `.github/copilot-instructions.md`

### 5. Verify Locally

```bash
# Run full test suite
uv run pytest tests/ -v

# Lint + format
uv run ruff format . && uv run ruff check .

# Type check
uv run mypy airflow_mcp_server/

# Start dev server and manually test
uv run uvicorn airflow_mcp_server.server:create_app --factory --reload --host 127.0.0.1 --port 8000
```

---

## Code Standards

### Python Style Guide

We follow **PEP 8** with these specifics:

#### Type Hints (Required)

All public functions must have complete type annotations:

```python
# ✅ Good
async def list_dags(limit: int = 100) -> dict:
    """List all Airflow DAGs."""
    ...

# ❌ Bad
async def list_dags(limit):
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
async def trigger_dag(dag_id: str, conf: dict | None = None) -> dict:
    """Trigger a DAG run.
    
    Args:
        dag_id: ID of the DAG to trigger
        conf: Optional configuration dictionary
    
    Returns:
        {
            "success": bool,
            "data": {
                "dag_run_id": str,
                "execution_date": str,
                "state": str
            },
            "error": str | None
        }
    
    Raises:
        ValueError: If dag_id is empty
        ConnectionError: If Airflow is unreachable
    """
```

#### Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Functions | snake_case | `trigger_dag()` |
| Classes | PascalCase | `AirflowClient` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES = 3` |
| Private methods | _leading_underscore | `_validate_params()` |
| MCP tools | airflow_<domain>_<action> | `airflow_dag_trigger` |

#### Imports

Organize imports in three groups (separated by blank lines):

```python
# 1. Standard library
import asyncio
import logging
from typing import TypedDict

# 2. Third-party
import aiohttp
from fastapi import FastAPI

# 3. Local
from airflow_mcp_server.config import settings
from airflow_mcp_server.models import ToolResponse
```

### Error Handling

#### Expected Errors

Catch and re-raise as appropriate:

```python
try:
    result = await airflow_client.trigger_dag(dag_id)
except ValueError as e:
    # Bad parameters → 400
    logger.warning(f"Invalid DAG ID: {e}")
    return {"success": False, "data": None, "error": str(e)}
except ConnectionError as e:
    # Airflow unreachable → 503
    logger.error(f"Airflow connection failed: {e}")
    raise  # FastAPI will return 503
except Exception as e:
    # Unexpected → 500
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

#### Logging

Use appropriate log levels:

```python
logger = logging.getLogger(__name__)

logger.debug("Starting handler for dag_id: my_dag")      # Development
logger.info(f"Triggered DAG: {dag_id}")                  # Important events
logger.warning(f"DAG not found: {dag_id}")              # Potential issues
logger.error(f"Failed to connect to Airflow: {e}")      # Errors
logger.critical("Cannot start server: no config")        # System failures
```

---

## Testing

### Test Organization

```
tests/
├── unit/
│   ├── test_dags.py           # Handler tests (mocked client)
│   ├── test_tasks.py
│   ├── test_connections.py
│   └── test_airflow_client.py # Client tests
├── integration/
│   ├── test_dags_integration.py    # Full flow tests
│   ├── test_airflow_connection.py  # Airflow connectivity
│   └── fixtures/
│       └── test_dags/          # Sample DAGs for testing
└── conftest.py                # Shared fixtures
```

### Unit Test Template

```python
# tests/unit/test_dags.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from airflow_mcp_server.handlers.dags import list_dags


@pytest.fixture
def mock_airflow_client(monkeypatch):
    """Mock AirflowClient for testing."""
    mock = AsyncMock()
    monkeypatch.setattr("airflow_mcp_server.handlers.dags.airflow_client", mock)
    return mock


@pytest.mark.asyncio
async def test_list_dags_success(mock_airflow_client):
    """Test listing DAGs returns success."""
    mock_airflow_client.list_dags.return_value = {
        "dags": [{"dag_id": "my_dag", "description": "Test"}]
    }
    
    result = await list_dags({"limit": 100})
    
    assert result["success"] is True
    assert len(result["data"]["dags"]) == 1
    assert result["error"] is None


@pytest.mark.asyncio
async def test_list_dags_airflow_error(mock_airflow_client):
    """Test handling Airflow connection error."""
    mock_airflow_client.list_dags.side_effect = ConnectionError("Airflow unavailable")
    
    with pytest.raises(ConnectionError):
        await list_dags({"limit": 100})
```

### Integration Test Template

```python
# tests/integration/test_dags_integration.py
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_trigger_dag_integration(airflow_client):
    """Test triggering a DAG against real Airflow."""
    # Assumes Airflow instance is running
    result = await airflow_client.trigger_dag("example_dag")
    
    assert result["dag_run_id"] is not None
    assert result["state"] in ["queued", "running"]
```

### Running Tests

```bash
# Unit tests (fast, no Airflow required)
uv run pytest tests/unit -v

# All tests (requires Airflow)
uv run pytest tests/ -v

# Specific test
uv run pytest tests/unit/test_dags.py::test_list_dags_success -v

# With coverage
uv run pytest --cov=airflow_mcp_server --cov-report=html tests/

# Watch mode (re-run on file changes)
uv run pytest-watch tests/
```

### Test Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: Critical paths (trigger DAG, get logs)
- **Manual testing**: New MCP tool endpoints with curl

---

## Commit Messages

Follow the **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`:     New feature
- `fix`:      Bug fix
- `docs`:     Documentation
- `style`:    Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without feature changes
- `test`:     Adding/updating tests
- `chore`:    Build, dependencies, configuration

### Scope

Optional component affected:
- `handlers`
- `client`
- `server`
- `config`
- `tests`

### Subject

- Use imperative mood ("add" not "added")
- Don't capitalize first letter
- No period at end
- Max 50 characters

### Body

Explain **what** and **why**, not **how**:

```
feat(handlers): add dag pause/unpause tools

Add airflow_dag_pause and airflow_dag_unpause MCP tools to allow
Claude to manage DAG scheduling. This enables automated workflow
control without manual Airflow UI access.

Closes: #42
```

### Examples

```
fix(client): handle 429 rate limit from Airflow

feat(handlers): add task retry tool

docs: update CONTRIBUTING guide

refactor(server): extract request validation to middleware
```

---

## Pull Request Process

### Before Submitting

1. **Sync with main**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run full test suite**:
   ```bash
   uv run pytest tests/ -v
   uv run ruff format . && uv run ruff check .
   ```

3. **Update documentation** if needed

### PR Description Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Related Issues
Closes #123

## Testing
- Unit tests: ✅ All passing
- Integration tests: ✅ Tested against Airflow 2.5.3
- Manual testing: Tested with curl and Claude

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guide (ruff)
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

- At least one maintainer review required
- All tests must pass
- No merge conflicts
- Coverage should not decrease

### After Merge

- Branch will be deleted
- Contributor will be credited in release notes

---

## Bug Reports

### Report a Bug

Use the [GitHub Issues](https://github.com/Adrien-Crapart/airflow-mcp-server/issues) page.

**Template**:

```markdown
## Description
Clear description of the bug.

## Steps to Reproduce
1. Set up with X config
2. Call endpoint Y
3. Observe error Z

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version: 3.11
- Airflow version: 2.5.3
- Framework: FastAPI X.Y.Z
- OS: Windows 10

## Error Logs
```
(paste relevant error logs)
```

## Workaround (if any)
How you worked around the bug
```

---

## Feature Requests

### Suggest a Feature

Use the [GitHub Discussions](https://github.com/Adrien-Crapart/airflow-mcp-server/discussions) page or open an [Issue](https://github.com/Adrien-Crapart/airflow-mcp-server/issues) with the `enhancement` label.

**Template**:

```markdown
## Problem
What problem does this solve?

## Proposed Solution
How should this be implemented?

## Example Usage
How Claude would use this feature:
```
MCP call: airflow_new_tool({param: value})
Response: {...}
```

## Alternatives Considered
Other approaches you've thought of
```

---

## Documentation

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `.github/copilot-instructions.md` | AI assistant guidelines |
| `docs/architecture.md` | System design details |
| `docs/mcp_tools.md` | Reference for all MCP tools |
| `CONTRIBUTING.md` | This file! |
| Docstrings | In-code documentation |

### Documentation Standards

- Use **Markdown** for all docs
- Link to related sections (don't duplicate)
- Include code examples where helpful
- Keep up-to-date with code changes
- Use consistent formatting (headings, code blocks)

### Adding a New Tool

1. **Implement handler** in appropriate file (e.g., `handlers/dags.py`)
2. **Add docstring** with Args, Returns, Raises
3. **Write tests** in `tests/unit/` and `tests/integration/`
4. **Document in `docs/mcp_tools.md`**:
   ```markdown
   #### airflow_dag_trigger
   Trigger a DAG run.
   
   **Input**:
   - dag_id (string, required): ID of the DAG
   - conf (object, optional): Configuration
   
   **Output**:
   - dag_run_id (string): Created run ID
   - execution_date (string): ISO 8601 timestamp
   - state (string): "queued" | "running" | ...
   ```

---

## Resources

- **[Airflow REST API Docs](https://airflow.apache.org/docs/apache-airflow/stable/stable-api-ref.html)**
- **[Model Context Protocol](https://modelcontextprotocol.io/)**
- **[Python Type Hints](https://docs.python.org/3/library/typing.html)**
- **[FastAPI](https://fastapi.tiangolo.com/)**
- **[Pytest Documentation](https://docs.pytest.org/)**

---

## Questions?

- Check existing [GitHub Issues](https://github.com/Adrien-Crapart/airflow-mcp-server/issues)
- Start a [Discussion](https://github.com/Adrien-Crapart/airflow-mcp-server/discussions)
- Email maintainers

Thank you for contributing! 🎉
