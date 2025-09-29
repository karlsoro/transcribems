#!/usr/bin/env python3
"""
MCP Project Initialization Script

This script creates a new MCP project following the MCP Project Structure Specification.
It generates the complete folder structure, template files, and configuration.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List

def create_directory_structure(project_name: str, base_path: Path) -> None:
    """Create the complete MCP project directory structure."""

    directories = [
        # Configuration
        "config",

        # Documentation
        "docs/api",
        "docs/development",
        "docs/research",

        # Source code
        "src/mcp_server",
        "src/tools",
        "src/services",
        "src/models",
        "src/core",
        "src/api/endpoints",
        "src/api/middleware",
        "src/tasks",

        # Tests
        "tests/contract/mcp",
        "tests/integration/mcp",
        "tests/unit/services",
        "tests/unit/models",
        "tests/unit/tools",
        "tests/performance",
        "tests/e2e",
        "tests/manual",

        # Test data
        "test_data/fixtures",
        "test_data/expected_results",

        # Test reports
        "test_reports/coverage",
        "test_reports/execution",
        "test_reports/validation",
        "test_reports/metrics",

        # Scripts
        "scripts/setup",
        "scripts/validation",
        "scripts/performance",
        "scripts/deployment",
        "scripts/maintenance",

        # Runtime data
        "data/jobs",
        "data/results",
        "data/uploads",
        "data/cache",
        "data/logs",
        "data/temp",

        # Deployment
        "deploy/docker",
        "deploy/k8s/manifests",
        "deploy/k8s/helm",
        "deploy/terraform",
        "deploy/ansible",

        # Cache
        ".cache",
    ]

    print(f"Creating directory structure for '{project_name}'...")
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")

def create_template_files(project_name: str, base_path: Path) -> None:
    """Create template files with project-specific content."""

    templates = {
        # Python project configuration
        "pyproject.toml": create_pyproject_toml(project_name),

        # Environment configuration
        ".env.example": create_env_example(project_name),
        "config/default.env": create_default_config(project_name),
        "config/logging.yaml": create_logging_config(),
        "config/mcp.yaml": create_mcp_config(project_name),

        # Git configuration
        ".gitignore": create_gitignore(),

        # Documentation
        "README.md": create_readme(project_name),
        "docs/API_REFERENCE.md": create_api_reference(project_name),
        "docs/TESTING_GUIDE.md": create_testing_guide(project_name),
        "docs/DEPLOYMENT_GUIDE.md": create_deployment_guide(project_name),
        "docs/development/CONTRIBUTING.md": create_contributing_guide(project_name),
        "docs/development/ARCHITECTURE.md": create_architecture_doc(project_name),

        # Source code templates
        "src/__init__.py": "",
        "src/main.py": create_main_py(project_name),
        "src/mcp_server/__init__.py": "",
        "src/mcp_server/server.py": create_mcp_server(project_name),
        "src/tools/__init__.py": "",
        "src/tools/example_tool.py": create_example_tool(project_name),
        "src/services/__init__.py": "",
        "src/services/example_service.py": create_example_service(project_name),
        "src/core/__init__.py": "",
        "src/core/config.py": create_config_module(),
        "src/core/logging.py": create_logging_module(),

        # Test templates
        "tests/__init__.py": "",
        "tests/conftest.py": create_conftest(),
        "tests/contract/test_example_contract.py": create_contract_test(project_name),
        "tests/integration/test_example_integration.py": create_integration_test(project_name),
        "tests/unit/test_example_unit.py": create_unit_test(project_name),

        # Test data
        "test_data/fixtures/mcp_requests.json": create_mcp_fixtures(),

        # Scripts
        "scripts/validation/integration_test.py": create_integration_script(project_name),
        "scripts/validation/validate_implementation.py": create_validation_script(project_name),
        "scripts/setup/create_test_data.py": create_test_data_script(project_name),

        # Docker
        "deploy/docker/Dockerfile": create_dockerfile(project_name),
        "deploy/docker/docker-compose.yml": create_docker_compose(project_name),

        # Development tools
        "Makefile": create_makefile(project_name),
        "pytest.ini": create_pytest_ini(),
        "mypy.ini": create_mypy_ini(),
        ".pre-commit-config.yaml": create_precommit_config(),

        # Claude instructions
        "CLAUDE.md": create_claude_instructions(project_name),
    }

    print(f"\nCreating template files...")
    for file_path, content in templates.items():
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"✅ Created: {file_path}")

def create_pyproject_toml(project_name: str) -> str:
    """Create pyproject.toml template."""
    return f'''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name.lower().replace('_', '-')}"
version = "1.0.0"
description = "MCP server for {project_name} functionality"
authors = [
    {{name = "Your Name", email = "your.email@example.com"}},
]
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "asyncio",
    "aiofiles",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.20.0",
    "pytest-cov>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "black",
    "flake8",
    "mypy",
    "pre-commit",
    "pytest-xdist",
]

[project.scripts]
{project_name.lower().replace('_', '-')}-mcp = "src.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=xml --cov-report=term-missing"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
'''

def create_env_example(project_name: str) -> str:
    """Create .env.example template."""
    return f'''# {project_name} Environment Configuration Template
# Copy this file to .env and fill in your values

# MCP Server Configuration
{project_name.upper()}_LOG_LEVEL=INFO
{project_name.upper()}_HOST=localhost
{project_name.upper()}_PORT=8000

# Feature-specific Configuration
# Add your configuration variables here

# Development Configuration
DEBUG=false
TESTING=false

# Security
SECRET_KEY=your-secret-key-here

# External Services
# API_KEY=your-api-key-here
# DATABASE_URL=your-database-url-here
'''

def create_default_config(project_name: str) -> str:
    """Create default configuration."""
    return f'''# Default {project_name} Configuration
{project_name.upper()}_LOG_LEVEL=INFO
{project_name.upper()}_HOST=localhost
{project_name.upper()}_PORT=8000
{project_name.upper()}_WORK_DIR=./data

# Feature Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30

# Logging
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=data/logs/{project_name.lower()}.log
'''

def create_logging_config() -> str:
    """Create logging configuration."""
    return '''version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: data/logs/application.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  src:
    level: DEBUG
    handlers: [console, file]
    propagate: no

  mcp:
    level: INFO
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console]
'''

def create_mcp_config(project_name: str) -> str:
    """Create MCP-specific configuration."""
    return f'''# MCP Server Configuration for {project_name}

server:
  name: {project_name.lower()}
  version: "1.0.0"
  description: "MCP server for {project_name} functionality"

capabilities:
  tools: true
  resources: false
  prompts: false

tools:
  # Define your MCP tools here
  example_tool:
    name: "example_tool"
    description: "Example tool functionality"
    enabled: true

security:
  enable_auth: false
  allowed_origins: ["*"]

performance:
  max_concurrent_requests: 10
  request_timeout: 30
  enable_caching: true
'''

def create_gitignore() -> str:
    """Create .gitignore file."""
    return '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
/data/
/test_reports/
/.cache/
/logs/
/uploads/
/temp/

# Development
.mypy_cache/
.pytest_cache/
'''

def create_readme(project_name: str) -> str:
    """Create README.md template."""
    return f'''# {project_name}

MCP server for {project_name} functionality.

## Features

- 🔧 **MCP Tools**: [{project_name} specific tools]
- 🚀 **High Performance**: Async processing and optimized workflows
- 🧪 **Comprehensive Testing**: 100% test coverage with validation evidence
- 📊 **Monitoring**: Built-in logging and metrics
- 🐳 **Docker Ready**: Containerized deployment support

## Quick Start

### Prerequisites

- Python 3.9+
- pip or poetry
- Docker (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd {project_name.lower()}
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run tests:
   ```bash
   make test
   ```

### MCP Server Setup

#### Option 1: Direct Command Line
```bash
# Start the MCP server
{project_name.lower().replace('_', '-')}-mcp

# Or run directly with Python
python -m src.main
```

#### Option 2: Claude Desktop Integration
Add to your Claude Desktop configuration:

```json
{{
  "mcpServers": {{
    "{project_name.lower()}": {{
      "command": "{project_name.lower().replace('_', '-')}-mcp",
      "args": [],
      "env": {{
        "{project_name.upper()}_LOG_LEVEL": "INFO"
      }}
    }}
  }}
}}
```

#### Option 3: Docker Setup
```bash
docker-compose up --build
```

## MCP Tools

### Available Tools

1. **example_tool** - Example tool functionality

### Example Usage

```python
# Example MCP client usage
import asyncio
from mcp.client import ClientSession

async def use_{project_name.lower()}_tools():
    async with ClientSession() as session:
        result = await session.call_tool(
            "example_tool",
            {{"input": "example data"}}
        )
        return result

# Run the example
result = asyncio.run(use_{project_name.lower()}_tools())
print(result)
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-contract

# Generate coverage report
make coverage

# Run validation suite
make validate
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make typecheck

# Run all quality checks
make quality
```

## Configuration

Key environment variables:

- `{project_name.upper()}_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `{project_name.upper()}_HOST`: Server host (default: localhost)
- `{project_name.upper()}_PORT`: Server port (default: 8000)

## Architecture

- **MCP Server**: Model Context Protocol server implementation
- **Tools**: MCP tools for specific functionality
- **Services**: Business logic and processing
- **Models**: Data models and validation
- **Core**: Utilities and configuration

## Testing

- **Contract Tests**: Define expected behavior (TDD approach)
- **Integration Tests**: Test component interactions
- **Unit Tests**: Test individual components
- **Performance Tests**: Load and performance validation

## License

[Your License Here]

## Support

- Documentation: See `/docs` directory
- Issues: GitHub Issues
- API Reference: `docs/API_REFERENCE.md`
'''

def create_api_reference(project_name: str) -> str:
    """Create API reference documentation."""
    return f'''# {project_name} API Reference

## MCP Tools

### example_tool

**Description**: Example tool functionality

**Input Schema**:
```json
{{
  "type": "object",
  "properties": {{
    "input": {{
      "type": "string",
      "description": "Input data for processing"
    }}
  }},
  "required": ["input"]
}}
```

**Output Schema**:
```json
{{
  "type": "object",
  "properties": {{
    "success": {{
      "type": "boolean",
      "description": "Whether the operation succeeded"
    }},
    "result": {{
      "type": "string",
      "description": "Processing result"
    }}
  }}
}}
```

**Example Usage**:
```python
result = await session.call_tool("example_tool", {{"input": "test data"}})
```

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 400 | Invalid input | Check input parameters |
| 500 | Internal error | Contact support |

## Rate Limits

- Maximum 100 requests per minute per client
- Maximum 10 concurrent requests per client

## Authentication

Currently no authentication required. Future versions may implement API key authentication.
'''

def create_testing_guide(project_name: str) -> str:
    """Create testing guide."""
    return f'''# {project_name} Testing Guide

## Quick Start Testing

### 1. Run All Tests
```bash
make test
```

### 2. Run Specific Test Types
```bash
# Contract tests (TDD requirements)
pytest tests/contract/ -v

# Integration tests
pytest tests/integration/ -v

# Unit tests
pytest tests/unit/ -v

# Performance tests
pytest tests/performance/ -v
```

### 3. Generate Test Reports
```bash
# Coverage report
make coverage

# Full validation report
python scripts/validation/validate_implementation.py
```

## Test Structure

```
tests/
├── contract/         # Contract tests (define behavior)
├── integration/      # Integration tests (component interaction)
├── unit/            # Unit tests (isolated testing)
├── performance/     # Performance and load tests
├── e2e/            # End-to-end workflow tests
└── manual/         # Manual testing scripts
```

## Writing Tests

### Contract Test Example
```python
def test_example_tool_contract():
    \"\"\"Contract: Tool should process input and return result.\"\"\"
    # This test defines expected behavior
    # Implementation must make this test pass
    pass
```

### Integration Test Example
```python
def test_example_integration():
    \"\"\"Test example tool integration with services.\"\"\"
    # Test component interactions
    pass
```

### Unit Test Example
```python
def test_example_service():
    \"\"\"Test example service in isolation.\"\"\"
    # Test individual component
    pass
```

## Test Evidence

Test results are stored in `test_reports/` for validation:

- `test_reports/coverage/` - Code coverage reports
- `test_reports/execution/` - Test execution results
- `test_reports/validation/` - Validation evidence

## Manual Testing

Use scripts in `scripts/validation/` for manual testing:

```bash
# Integration test
python scripts/validation/integration_test.py

# System validation
python scripts/validation/validate_implementation.py
```
'''

def create_deployment_guide(project_name: str) -> str:
    """Create deployment guide."""
    return f'''# {project_name} Deployment Guide

## Docker Deployment

### Local Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

## Kubernetes Deployment

```bash
kubectl apply -f deploy/k8s/manifests/
```

## Environment Configuration

### Production Environment Variables
```bash
{project_name.upper()}_LOG_LEVEL=INFO
{project_name.upper()}_HOST=0.0.0.0
{project_name.upper()}_PORT=8000
```

### Health Checks

The server provides health check endpoints:
- `/health` - Basic health check
- `/ready` - Readiness check

## Monitoring

### Logs
Logs are written to `data/logs/` directory:
- `application.log` - Application logs
- `error.log` - Error logs

### Metrics
Application metrics available at `/metrics` endpoint.

## Security

### Production Security Checklist
- [ ] Configure proper environment variables
- [ ] Set up HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

## Backup and Recovery

### Data Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Recovery
```bash
# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz
```
'''

def create_contributing_guide(project_name: str) -> str:
    """Create contributing guide."""
    return f'''# Contributing to {project_name}

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create virtual environment
4. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Development Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes following coding standards

3. Run tests:
   ```bash
   make test
   ```

4. Run quality checks:
   ```bash
   make quality
   ```

5. Commit with descriptive message

6. Push and create pull request

## Coding Standards

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for all public functions
- Maintain test coverage above 80%

## Testing Requirements

- All new features must have contract tests
- Integration tests for component interactions
- Unit tests for individual functions
- Performance tests for critical paths

## Code Review Process

1. All changes require pull request
2. At least one approval required
3. All tests must pass
4. Code coverage must not decrease

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create release tag
4. Deploy to production
'''

def create_architecture_doc(project_name: str) -> str:
    """Create architecture documentation."""
    return f'''# {project_name} Architecture

## System Overview

{project_name} is an MCP (Model Context Protocol) server that provides [functionality description].

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │ -> │   MCP Server    │ -> │    Services     │
│  (Claude, etc.) │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              v                        v
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Tools       │    │     Models      │
                       │                 │    │                 │
                       └─────────────────┘    └─────────────────┘
```

## Component Description

### MCP Server (`src/mcp_server/`)
- Implements MCP protocol
- Handles client connections
- Routes tool requests

### Tools (`src/tools/`)
- MCP tool implementations
- Input validation
- Response formatting

### Services (`src/services/`)
- Business logic
- Data processing
- External integrations

### Models (`src/models/`)
- Data structures
- Validation schemas
- Type definitions

### Core (`src/core/`)
- Configuration management
- Logging setup
- Utilities

## Design Principles

1. **Separation of Concerns**: Clear boundaries between components
2. **Async First**: All I/O operations are asynchronous
3. **Type Safety**: Full type hints and validation
4. **Testability**: Designed for comprehensive testing
5. **Extensibility**: Easy to add new tools and features

## Data Flow

1. MCP client sends tool request
2. MCP server validates request
3. Tool processes request using services
4. Services perform business logic
5. Response sent back to client

## Security Considerations

- Input validation at tool level
- Service-level authorization
- Secure configuration management
- Audit logging

## Performance Considerations

- Async processing for scalability
- Connection pooling
- Caching where appropriate
- Resource cleanup

## Deployment Architecture

### Development
- Single container
- Local file storage
- Debug logging

### Production
- Load balanced containers
- External storage
- Structured logging
- Monitoring and alerting
'''

def create_main_py(project_name: str) -> str:
    """Create main.py template."""
    return f'''"""
{project_name} MCP Server

Main entry point for the MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.server import start_server
from core.config import get_config
from core.logging import setup_logging

async def main():
    """Start the {project_name} MCP server."""
    # Load configuration
    config = get_config()

    # Setup logging
    setup_logging(config.log_level)

    # Start server
    await start_server(config)

if __name__ == "__main__":
    asyncio.run(main())
'''

def create_mcp_server(project_name: str) -> str:
    """Create MCP server template."""
    return f'''"""
{project_name} MCP Server Implementation

Implements the Model Context Protocol server for {project_name}.
"""

import asyncio
import logging
from typing import Dict, Any

from mcp import server
from mcp.types import Tool, TextContent

from ..tools.example_tool import example_tool, EXAMPLE_TOOL_DEFINITION

logger = logging.getLogger(__name__)

class {project_name.replace('_', '')}MCPServer:
    """MCP server for {project_name}."""

    def __init__(self):
        self.server = server.Server("{project_name.lower()}")
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            if name == "example_tool":
                result = await example_tool(arguments)
                return [TextContent(type="text", text=str(result))]
            else:
                raise ValueError(f"Unknown tool: {{name}}")

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [EXAMPLE_TOOL_DEFINITION]

    async def start(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server."""
        logger.info(f"Starting {{self.__class__.__name__}} on {{host}}:{{port}}")
        await self.server.run(host=host, port=port)

async def start_server(config):
    """Start the MCP server with configuration."""
    server_instance = {project_name.replace('_', '')}MCPServer()
    await server_instance.start(
        host=config.host,
        port=config.port
    )
'''

def create_example_tool(project_name: str) -> str:
    """Create example tool template."""
    return f'''"""
Example Tool for {project_name}

This is a template for MCP tools. Replace with your actual tool implementation.
"""

import logging
from typing import Dict, Any

from mcp.types import Tool
from ..services.example_service import ExampleService

logger = logging.getLogger(__name__)

# Tool definition for MCP
EXAMPLE_TOOL_DEFINITION = Tool(
    name="example_tool",
    description="Example tool for {project_name} functionality",
    inputSchema={{
        "type": "object",
        "properties": {{
            "input": {{
                "type": "string",
                "description": "Input data for processing"
            }}
        }},
        "required": ["input"]
    }}
)

async def example_tool(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example MCP tool implementation.

    Args:
        request: Tool request containing input parameters

    Returns:
        Tool response with processing results
    """
    try:
        # Validate input
        if "input" not in request:
            raise ValueError("Missing required parameter: input")

        input_data = request["input"]
        logger.info(f"Processing example tool request: {{input_data}}")

        # Use service for business logic
        service = ExampleService()
        result = await service.process(input_data)

        return {{
            "success": True,
            "result": result,
            "tool": "example_tool"
        }}

    except Exception as e:
        logger.error(f"Example tool failed: {{e}}")
        return {{
            "success": False,
            "error": str(e),
            "tool": "example_tool"
        }}
'''

def create_example_service(project_name: str) -> str:
    """Create example service template."""
    return f'''"""
Example Service for {project_name}

Business logic service template. Replace with your actual service implementation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class ExampleService:
    """Example service for {project_name} business logic."""

    def __init__(self):
        """Initialize the example service."""
        self.initialized = True
        logger.info("ExampleService initialized")

    async def process(self, input_data: str) -> str:
        """
        Process input data.

        Args:
            input_data: Input string to process

        Returns:
            Processed result
        """
        logger.debug(f"Processing input: {{input_data}}")

        # Replace with your actual business logic
        result = f"Processed: {{input_data}}"

        logger.info(f"Processing completed: {{result}}")
        return result

    async def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data.

        Args:
            input_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(input_data, str):
            return False

        if len(input_data.strip()) == 0:
            return False

        return True
'''

def create_config_module() -> str:
    """Create configuration module."""
    return '''"""
Configuration management for the MCP server.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    """Application configuration."""
    host: str = "localhost"
    port: int = 8000
    log_level: str = "INFO"
    work_dir: Path = Path("./data")
    debug: bool = False

def get_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        work_dir=Path(os.getenv("WORK_DIR", "./data")),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
'''

def create_logging_module() -> str:
    """Create logging module."""
    return '''"""
Logging configuration for the MCP server.
"""

import logging
import logging.config
from pathlib import Path
import yaml

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""

    # Ensure logs directory exists
    Path("data/logs").mkdir(parents=True, exist_ok=True)

    # Try to load logging config from file
    config_path = Path("config/logging.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # Fallback to basic configuration
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('data/logs/application.log')
            ]
        )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
'''

def create_conftest() -> str:
    """Create pytest conftest.py."""
    return '''"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "logs").mkdir()
    (data_dir / "temp").mkdir()
    return data_dir

@pytest.fixture
def sample_request():
    """Sample MCP tool request for testing."""
    return {
        "input": "test data"
    }
'''

def create_contract_test(project_name: str) -> str:
    """Create contract test template."""
    return f'''"""
Contract tests for {project_name}.

These tests define the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from unittest.mock import Mock, AsyncMock

class Test{project_name.replace('_', '')}Contract:
    """Contract tests defining expected behavior."""

    def test_example_tool_processes_input(self):
        """
        Contract: Example tool should process input and return result.
        """
        # This will fail until example_tool is implemented
        from src.tools.example_tool import example_tool

        request = {{"input": "test data"}}
        # result = await example_tool(request)

        # Assert expected behavior
        # assert result["success"] is True
        # assert "result" in result
        # assert result["tool"] == "example_tool"

        # Placeholder assertion to make test fail initially
        assert False, "Contract test not implemented yet"

    def test_example_service_validates_input(self):
        """
        Contract: Example service should validate input data.
        """
        # This will fail until ExampleService is implemented
        from src.services.example_service import ExampleService

        service = ExampleService()

        # Test valid input
        # assert await service.validate_input("valid data") is True

        # Test invalid input
        # assert await service.validate_input("") is False
        # assert await service.validate_input(None) is False

        # Placeholder assertion to make test fail initially
        assert False, "Contract test not implemented yet"
'''

def create_integration_test(project_name: str) -> str:
    """Create integration test template."""
    return f'''"""
Integration tests for {project_name}.

These tests verify component interactions.
"""

import pytest
import asyncio

class Test{project_name.replace('_', '')}Integration:
    """Integration tests for component interactions."""

    @pytest.mark.asyncio
    async def test_example_tool_integration(self, sample_request):
        """Test example tool integration with services."""
        from src.tools.example_tool import example_tool

        # Test tool integration
        result = await example_tool(sample_request)

        # Verify integration works
        assert isinstance(result, dict)
        assert "success" in result
        assert "tool" in result

    @pytest.mark.asyncio
    async def test_mcp_server_integration(self):
        """Test MCP server integration."""
        # This would test the actual MCP server
        # For now, just verify imports work
        from src.mcp_server.server import {project_name.replace('_', '')}MCPServer

        server = {project_name.replace('_', '')}MCPServer()
        assert server is not None
'''

def create_unit_test(project_name: str) -> str:
    """Create unit test template."""
    return f'''"""
Unit tests for {project_name}.

These tests verify individual components in isolation.
"""

import pytest
import asyncio

class Test{project_name.replace('_', '')}Unit:
    """Unit tests for individual components."""

    @pytest.mark.asyncio
    async def test_example_service_process(self):
        """Test ExampleService.process method."""
        from src.services.example_service import ExampleService

        service = ExampleService()
        result = await service.process("test input")

        assert isinstance(result, str)
        assert "test input" in result

    @pytest.mark.asyncio
    async def test_example_service_validate_input(self):
        """Test ExampleService.validate_input method."""
        from src.services.example_service import ExampleService

        service = ExampleService()

        # Test valid input
        assert await service.validate_input("valid") is True

        # Test invalid input
        assert await service.validate_input("") is False
        assert await service.validate_input(123) is False
'''

def create_mcp_fixtures() -> str:
    """Create MCP test fixtures."""
    return '''{
  "example_requests": [
    {
      "tool": "example_tool",
      "parameters": {
        "input": "test data"
      }
    }
  ],
  "expected_responses": [
    {
      "success": true,
      "result": "Processed: test data",
      "tool": "example_tool"
    }
  ]
}'''

def create_integration_script(project_name: str) -> str:
    """Create integration test script."""
    return f'''#!/usr/bin/env python3
"""
Integration test script for {project_name}.

This script tests the complete MCP server functionality.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {project_name.replace('_', '')}IntegrationTest:
    """Integration test suite for {project_name}."""

    def __init__(self):
        self.test_results = {{
            "started_at": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }}

    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("🚀 Starting {project_name} Integration Test Suite")

        test_methods = [
            ("Tool Import Test", self.test_tool_imports),
            ("Service Test", self.test_services),
            ("MCP Server Test", self.test_mcp_server),
        ]

        for test_name, test_method in test_methods:
            await self.run_single_test(test_name, test_method)

        self.print_results()

    async def run_single_test(self, test_name: str, test_method):
        """Run a single test."""
        logger.info(f"🔍 Running: {{test_name}}")

        try:
            result = await test_method()
            self.test_results["tests_run"] += 1

            if result.get("success", False):
                self.test_results["tests_passed"] += 1
                logger.info(f"✅ {{test_name}}: PASSED")
            else:
                self.test_results["tests_failed"] += 1
                logger.error(f"❌ {{test_name}}: FAILED")

            self.test_results["test_details"].append({{
                "name": test_name,
                "success": result.get("success", False),
                "result": result
            }})

        except Exception as e:
            self.test_results["tests_run"] += 1
            self.test_results["tests_failed"] += 1
            logger.error(f"❌ {{test_name}}: FAILED - {{e}}")

    async def test_tool_imports(self):
        """Test that all tools can be imported."""
        try:
            from src.tools.example_tool import example_tool, EXAMPLE_TOOL_DEFINITION

            # Test tool is callable
            assert callable(example_tool)
            assert EXAMPLE_TOOL_DEFINITION.name == "example_tool"

            return {{"success": True, "message": "Tools imported successfully"}}
        except Exception as e:
            return {{"success": False, "error": str(e)}}

    async def test_services(self):
        """Test service functionality."""
        try:
            from src.services.example_service import ExampleService

            service = ExampleService()
            result = await service.process("test data")

            assert isinstance(result, str)
            assert "test data" in result

            return {{"success": True, "message": "Services working correctly"}}
        except Exception as e:
            return {{"success": False, "error": str(e)}}

    async def test_mcp_server(self):
        """Test MCP server initialization."""
        try:
            from src.mcp_server.server import {project_name.replace('_', '')}MCPServer

            server = {project_name.replace('_', '')}MCPServer()
            assert server is not None

            return {{"success": True, "message": "MCP server initialized"}}
        except Exception as e:
            return {{"success": False, "error": str(e)}}

    def print_results(self):
        """Print test results."""
        logger.info("🏁 Integration Test Results")
        logger.info(f"Tests Run: {{self.test_results['tests_run']}}")
        logger.info(f"Tests Passed: {{self.test_results['tests_passed']}}")
        logger.info(f"Tests Failed: {{self.test_results['tests_failed']}}")

        # Save results
        with open("test_reports/execution/integration_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)

async def main():
    """Run integration tests."""
    test_suite = {project_name.replace('_', '')}IntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
'''

def create_validation_script(project_name: str) -> str:
    """Create validation script."""
    return f'''#!/usr/bin/env python3
"""
Validation script for {project_name}.

This script validates the complete implementation.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔍 {{description}}...")
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {{description}}: PASSED")
            return True
        else:
            print(f"❌ {{description}}: FAILED")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {{description}}: ERROR - {{e}}")
        return False

def main():
    """Run validation checks."""
    print("🚀 {project_name} Validation Suite")
    print("=" * 50)

    checks = [
        ("pytest tests/contract/ -v", "Contract Tests"),
        ("pytest tests/unit/ -v", "Unit Tests"),
        ("pytest tests/integration/ -v", "Integration Tests"),
        ("pytest --cov=src --cov-report=term-missing", "Code Coverage"),
        ("python -m src.main --help", "MCP Server Check"),
    ]

    passed = 0
    total = len(checks)

    for command, description in checks:
        if run_command(command, description):
            passed += 1

    print("\\n" + "=" * 50)
    print(f"Validation Results: {{passed}}/{{total}} checks passed")

    if passed == total:
        print("🎉 All validation checks passed!")
        sys.exit(0)
    else:
        print("⚠️ Some validation checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

def create_test_data_script(project_name: str) -> str:
    """Create test data creation script."""
    return f'''#!/usr/bin/env python3
"""
Create test data for {project_name}.

This script generates test data and fixtures.
"""

import json
from pathlib import Path

def create_test_fixtures():
    """Create test fixtures."""

    # Sample MCP requests
    mcp_fixtures = {{
        "tool_requests": [
            {{
                "tool": "example_tool",
                "parameters": {{
                    "input": "sample test data"
                }}
            }}
        ],
        "expected_responses": [
            {{
                "success": True,
                "result": "Processed: sample test data",
                "tool": "example_tool"
            }}
        ]
    }}

    # Save fixtures
    fixtures_file = Path("test_data/fixtures/mcp_requests.json")
    fixtures_file.parent.mkdir(parents=True, exist_ok=True)

    with open(fixtures_file, "w") as f:
        json.dump(mcp_fixtures, f, indent=2)

    print(f"✅ Created test fixtures: {{fixtures_file}}")

def create_sample_data():
    """Create sample data files."""

    # Create sample data directory
    sample_dir = Path("test_data/samples")
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Create sample text file
    sample_file = sample_dir / "sample.txt"
    sample_file.write_text("This is sample test data for {project_name}.")

    print(f"✅ Created sample data: {{sample_file}}")

def main():
    """Create all test data."""
    print("🔧 Creating test data for {project_name}")

    create_test_fixtures()
    create_sample_data()

    print("✅ Test data creation complete!")

if __name__ == "__main__":
    main()
'''

def create_dockerfile(project_name: str) -> str:
    """Create Dockerfile."""
    return f'''FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY config/ config/

# Create data directories
RUN mkdir -p data/logs data/temp data/uploads

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV {project_name.upper()}_HOST=0.0.0.0
ENV {project_name.upper()}_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "src.main"]
'''

def create_docker_compose(project_name: str) -> str:
    """Create docker-compose.yml."""
    return f'''version: '3.8'

services:
  {project_name.lower().replace('_', '-')}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - {project_name.upper()}_LOG_LEVEL=INFO
      - {project_name.upper()}_HOST=0.0.0.0
      - {project_name.upper()}_PORT=8000
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  data:
'''

def create_makefile(project_name: str) -> str:
    """Create Makefile."""
    return f'''.PHONY: help install test lint format typecheck quality coverage validate clean

help:
\t@echo "Available commands:"
\t@echo "  install     Install dependencies"
\t@echo "  test        Run all tests"
\t@echo "  test-unit   Run unit tests"
\t@echo "  test-integration Run integration tests"
\t@echo "  test-contract Run contract tests"
\t@echo "  lint        Run code linting"
\t@echo "  format      Format code"
\t@echo "  typecheck   Run type checking"
\t@echo "  quality     Run all quality checks"
\t@echo "  coverage    Generate coverage report"
\t@echo "  validate    Run full validation suite"
\t@echo "  clean       Clean generated files"

install:
\tpip install -e .[dev]

test:
\tpytest tests/ -v

test-unit:
\tpytest tests/unit/ -v

test-integration:
\tpytest tests/integration/ -v

test-contract:
\tpytest tests/contract/ -v

lint:
\tflake8 src/ tests/

format:
\tblack src/ tests/
\tisort src/ tests/

typecheck:
\tmypy src/

quality: lint typecheck

coverage:
\tpytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

validate:
\tpython scripts/validation/validate_implementation.py

clean:
\trm -rf .pytest_cache/
\trm -rf .mypy_cache/
\trm -rf htmlcov/
\trm -rf test_reports/
\trm -rf .coverage
\trm -rf coverage.xml
\tfind . -type d -name __pycache__ -exec rm -rf {{}} +
\tfind . -type f -name "*.pyc" -delete
'''

def create_pytest_ini() -> str:
    """Create pytest.ini."""
    return '''[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --disable-warnings --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    contract: marks tests as contract tests
    unit: marks tests as unit tests
'''

def create_mypy_ini() -> str:
    """Create mypy.ini."""
    return '''[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
'''

def create_precommit_config() -> str:
    """Create pre-commit configuration."""
    return '''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
        stages: [commit]
'''

def create_claude_instructions(project_name: str) -> str:
    """Create CLAUDE.md instructions."""
    return f'''# Claude Code Instructions for {project_name}

## Project Overview

{project_name} is an MCP (Model Context Protocol) server that provides [describe functionality].

## Development Guidelines

### Architecture
- **MCP Server**: Implements the Model Context Protocol
- **Tools**: MCP tools that provide functionality to clients
- **Services**: Business logic and data processing
- **Models**: Data structures and validation

### Folder Structure
This project follows the MCP Project Structure Specification:
- `src/` - Source code
- `tests/` - All test code
- `docs/` - Documentation
- `config/` - Configuration files
- `test_reports/` - Test evidence for validation

### Development Workflow
1. Write contract tests first (TDD)
2. Implement functionality to pass tests
3. Add integration and unit tests
4. Ensure 100% code coverage
5. Generate test evidence

### Key Commands
- `make test` - Run all tests
- `make coverage` - Generate coverage reports
- `make validate` - Full validation suite
- `python scripts/validation/integration_test.py` - Integration testing

### Testing Requirements
- Contract tests define expected behavior
- 100% code coverage required
- Test evidence generated in `test_reports/`
- JUnit XML format for validation systems

### MCP Tool Development
1. Define tool in `src/tools/[name]_tool.py`
2. Implement business logic in `src/services/`
3. Add contract tests in `tests/contract/`
4. Register tool in MCP server

### Code Style
- Use type hints for all functions
- Follow PEP 8 conventions
- Write comprehensive docstrings
- Use async/await for I/O operations

### Validation System Compliance
This project generates formal test evidence for validation systems:
- Code coverage reports (HTML + XML)
- Test execution results (JUnit XML)
- Requirements traceability matrix
- Validation summary documentation
'''

def main():
    """Main function to create MCP project."""
    parser = argparse.ArgumentParser(description="Initialize a new MCP project")
    parser.add_argument("project_name", help="Name of the MCP project")
    parser.add_argument("--path", default=".", help="Base path for project creation")

    args = parser.parse_args()

    project_name = args.project_name
    base_path = Path(args.path) / project_name

    if base_path.exists():
        response = input(f"Directory '{base_path}' already exists. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Project creation cancelled.")
            sys.exit(0)

    print(f"🚀 Creating MCP project: {project_name}")
    print(f"📁 Location: {base_path}")
    print("=" * 60)

    try:
        # Create directory structure
        create_directory_structure(project_name, base_path)

        # Create template files
        create_template_files(project_name, base_path)

        print("\\n🎉 MCP Project Created Successfully!")
        print("=" * 60)
        print(f"📁 Project location: {base_path}")
        print("\\n🚀 Next steps:")
        print(f"1. cd {project_name}")
        print("2. python -m venv venv")
        print("3. source venv/bin/activate")
        print("4. pip install -e .[dev]")
        print("5. make test")
        print("\\n📚 Documentation:")
        print("- README.md - Project overview")
        print("- docs/API_REFERENCE.md - MCP tools documentation")
        print("- docs/TESTING_GUIDE.md - Testing instructions")
        print("- CLAUDE.md - Claude Code development instructions")

    except Exception as e:
        print(f"❌ Project creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()