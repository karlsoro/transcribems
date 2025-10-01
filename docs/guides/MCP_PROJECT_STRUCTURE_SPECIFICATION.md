# MCP Project Structure Specification

## Overview

This document defines the standard folder structure for Model Context Protocol (MCP) projects. This specification ensures consistency, maintainability, and proper organization across all MCP implementations.

**Version**: 1.0.0
**Based on**: TranscribeMCP MCP Server Implementation
**Compliance**: Production-ready, validation-system compatible

## 📁 Standard MCP Project Structure

```
mcp-project-name/
├── 📁 config/                      # Application configuration
│   ├── default.env                 # Default environment variables
│   ├── production.env              # Production configuration
│   ├── development.env             # Development configuration
│   ├── logging.yaml                # Logging configuration
│   ├── models.yaml                 # AI model configurations
│   └── mcp.yaml                    # MCP-specific settings
│
├── 📁 docs/                        # Documentation
│   ├── README.md                   # Project overview and setup
│   ├── API_REFERENCE.md            # MCP tools and API documentation
│   ├── TESTING_GUIDE.md            # Testing instructions
│   ├── DEPLOYMENT_GUIDE.md         # Deployment instructions
│   ├── TROUBLESHOOTING.md          # Common issues and solutions
│   ├── api/                        # API documentation
│   │   ├── openapi.yaml            # OpenAPI specification
│   │   ├── mcp-tools.md            # MCP tools documentation
│   │   └── schemas.md              # Data schemas
│   ├── development/                # Development documentation
│   │   ├── CONTRIBUTING.md         # Contribution guidelines
│   │   ├── ARCHITECTURE.md         # System architecture
│   │   ├── CODING_STANDARDS.md     # Code style guidelines
│   │   └── FOLDER_STRUCTURE.md     # This document
│   └── research/                   # Research and findings
│       ├── technology-choices.md   # Technology decisions
│       └── performance-analysis.md # Performance research
│
├── 📁 src/                         # Source code
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   ├── mcp_server/                 # MCP server implementation
│   │   ├── __init__.py
│   │   ├── server.py               # Main MCP server
│   │   ├── handlers.py             # Request handlers
│   │   └── middleware.py           # MCP middleware
│   ├── tools/                      # MCP tools implementation
│   │   ├── __init__.py
│   │   ├── tool_base.py            # Base tool class
│   │   ├── [feature]_tool.py       # Individual MCP tools
│   │   └── tool_registry.py        # Tool registration
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── [feature]_service.py    # Domain services
│   │   ├── storage_service.py      # Data storage
│   │   └── validation_service.py   # Input validation
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   ├── mcp_models.py           # MCP-specific models
│   │   ├── domain_models.py        # Business domain models
│   │   └── types.py                # Type definitions
│   ├── core/                       # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration management
│   │   ├── logging.py              # Logging setup
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── utils.py                # Utility functions
│   ├── api/                        # API layer (if needed)
│   │   ├── __init__.py
│   │   ├── endpoints/              # HTTP endpoints
│   │   └── middleware/             # API middleware
│   └── tasks/                      # Background tasks
│       ├── __init__.py
│       └── [feature]_tasks.py      # Async tasks
│
├── 📁 tests/                       # Test suites
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── contract/                   # Contract tests (TDD)
│   │   ├── __init__.py
│   │   ├── mcp/                    # MCP-specific contract tests
│   │   │   ├── test_[tool]_tool.py
│   │   │   └── test_mcp_server.py
│   │   └── test_[feature]_contract.py
│   ├── integration/                # Integration tests
│   │   ├── __init__.py
│   │   ├── mcp/                    # MCP integration tests
│   │   │   └── test_mcp_integration.py
│   │   └── test_[feature]_integration.py
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── services/
│   │   ├── models/
│   │   └── tools/
│   ├── performance/                # Performance tests
│   │   ├── __init__.py
│   │   └── test_[feature]_performance.py
│   ├── e2e/                        # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_[feature]_e2e.py
│   └── manual/                     # Manual testing scripts
│       └── test_[feature]_manual.py
│
├── 📁 test_data/                   # Test fixtures and data
│   ├── fixtures/                   # Test fixtures
│   │   ├── mcp_requests.json       # Sample MCP requests
│   │   └── [feature]_fixtures.json
│   ├── expected_results/           # Expected test outputs
│   └── [domain]/                   # Domain-specific test data
│       └── sample_files.*
│
├── 📁 test_reports/                # Test evidence and results
│   ├── coverage/                   # Code coverage reports
│   │   ├── html/                   # HTML coverage dashboard
│   │   ├── coverage.xml            # Machine-readable coverage
│   │   ├── .coverage               # Coverage database
│   │   └── summary.txt             # Coverage summary
│   ├── execution/                  # Test execution results
│   │   ├── pytest_results.xml      # JUnit XML test results
│   │   ├── [feature]_test_results.xml
│   │   └── test_execution_log.txt   # Detailed execution log
│   ├── validation/                 # Validation evidence
│   │   ├── TEST_EVIDENCE_SUMMARY.md
│   │   ├── requirements_traceability.csv
│   │   └── validation_report.pdf
│   └── metrics/                    # Performance and quality metrics
│       ├── performance_benchmarks.json
│       └── quality_metrics.json
│
├── 📁 scripts/                     # Standalone utilities
│   ├── setup/                      # Setup and initialization
│   │   ├── install_dependencies.py
│   │   ├── create_test_data.py
│   │   └── initialize_project.py
│   ├── validation/                 # Validation scripts
│   │   ├── integration_test.py
│   │   ├── mcp_validation.py
│   │   ├── system_demo.py
│   │   └── validate_implementation.py
│   ├── performance/                # Performance testing
│   │   ├── performance_benchmark.py
│   │   └── load_test.py
│   ├── deployment/                 # Deployment utilities
│   │   ├── deploy.py
│   │   └── health_check.py
│   └── maintenance/                # Maintenance scripts
│       ├── cleanup.py
│       └── backup.py
│
├── 📁 data/                        # Runtime data
│   ├── jobs/                       # Job data
│   ├── results/                    # Processing results
│   ├── uploads/                    # User uploads
│   ├── cache/                      # Cached data
│   ├── logs/                       # Application logs
│   └── temp/                       # Temporary files
│
├── 📁 deploy/                      # Deployment configurations
│   ├── docker/                     # Docker deployment
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   └── .dockerignore
│   ├── k8s/                        # Kubernetes deployment
│   │   ├── manifests/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   └── helm/                   # Helm charts
│   ├── terraform/                  # Infrastructure as Code
│   │   ├── main.tf
│   │   └── variables.tf
│   └── ansible/                    # Configuration management
│       └── playbook.yml
│
├── 📁 .cache/                      # Generated/cache files
│   ├── .mypy_cache/                # MyPy cache
│   ├── .pytest_cache/              # Pytest cache
│   ├── recordings/                 # Test recordings
│   └── build/                      # Build artifacts
│
└── 📄 Root Configuration Files
    ├── pyproject.toml              # Python project configuration
    ├── requirements.txt            # Python dependencies
    ├── requirements-dev.txt        # Development dependencies
    ├── .env.example                # Environment variables template
    ├── .gitignore                  # Git ignore rules
    ├── .pre-commit-config.yaml     # Pre-commit hooks
    ├── Makefile                    # Build and development commands
    ├── setup.cfg                   # Python setup configuration
    ├── mypy.ini                    # Type checking configuration
    ├── pytest.ini                 # Test configuration
    ├── CLAUDE.md                   # Claude Code instructions
    ├── LICENSE                     # Project license
    └── CHANGELOG.md                # Version history
```

## 🎯 Core Principles

### 1. **Separation of Concerns**
- **`src/`** - Production code only
- **`tests/`** - All test code
- **`docs/`** - All documentation
- **`config/`** - All configuration
- **`data/`** - Runtime data only

### 2. **MCP-Specific Organization**
- **`src/mcp_server/`** - MCP protocol implementation
- **`src/tools/`** - MCP tools (the main interface)
- **`tests/contract/mcp/`** - MCP protocol compliance tests
- **`test_data/fixtures/mcp_requests.json`** - MCP test data

### 3. **Validation System Compliance**
- **`test_reports/`** - Formal test evidence
- **`test_reports/validation/`** - Validation documentation
- **`test_reports/execution/`** - JUnit XML results
- **`test_reports/coverage/`** - Code coverage evidence

### 4. **Development Workflow Support**
- **`scripts/validation/`** - Easy testing commands
- **`scripts/setup/`** - Environment setup
- **`config/`** - Environment-specific configs
- **`.cache/`** - Generated files (gitignored)

## 📋 File Naming Conventions

### **Python Files**
```
snake_case.py                    # Standard Python convention
test_[feature]_[type].py         # Test files
[feature]_service.py             # Service classes
[feature]_tool.py                # MCP tool implementations
[feature]_model.py               # Data models
```

### **Configuration Files**
```
lowercase.env                    # Environment files
lowercase.yaml                   # YAML configurations
UPPERCASE.md                     # Important documentation
lowercase.json                   # JSON data files
```

### **Test Evidence Files**
```
[feature]_test_results.xml       # JUnit XML results
requirements_traceability.csv    # Traceability matrix
TEST_EVIDENCE_SUMMARY.md         # Validation summary
coverage.xml                     # Coverage data
```

## 🔧 Required Configuration Files

### **Root Level**
- **`pyproject.toml`** - Python project metadata and dependencies
- **`.env.example`** - Environment variables template
- **`.gitignore`** - Git ignore patterns
- **`CLAUDE.md`** - Claude Code development instructions

### **Config Directory**
- **`default.env`** - Default application settings
- **`logging.yaml`** - Logging configuration
- **`mcp.yaml`** - MCP server configuration

### **Test Configuration**
- **`tests/conftest.py`** - Pytest configuration
- **`pytest.ini`** - Pytest settings
- **`mypy.ini`** - Type checking configuration

## 🧪 Test Organization Strategy

### **Test Types by Directory**
```
tests/contract/     → TDD contract tests (define behavior)
tests/unit/         → Unit tests (isolated components)
tests/integration/  → Integration tests (component interaction)
tests/performance/  → Performance and load tests
tests/e2e/          → End-to-end workflow tests
tests/manual/       → Manual testing scripts
```

### **MCP-Specific Tests**
```
tests/contract/mcp/test_[tool]_tool.py    → MCP tool contract tests
tests/integration/mcp/                    → MCP protocol integration
test_data/fixtures/mcp_requests.json      → MCP test fixtures
```

### **Test Evidence Requirements**
```
test_reports/coverage/       → Code coverage (HTML + XML)
test_reports/execution/      → Test results (JUnit XML)
test_reports/validation/     → Validation evidence
test_reports/metrics/        → Performance metrics
```

## 🚀 MCP Tool Implementation Pattern

### **Tool File Structure**
```python
# src/tools/[feature]_tool.py
from mcp.types import Tool
from src.services.[feature]_service import [Feature]Service

def [feature]_tool(request: dict) -> dict:
    """
    MCP tool for [feature] functionality.

    Args:
        request: MCP tool request

    Returns:
        MCP tool response
    """
    # Implementation here
    pass

# Tool metadata
TOOL_DEFINITION = Tool(
    name="[feature]_tool",
    description="[Feature] functionality",
    inputSchema={
        "type": "object",
        "properties": {
            # Input schema
        }
    }
)
```

### **Service Pattern**
```python
# src/services/[feature]_service.py
class [Feature]Service:
    """Service for [feature] business logic."""

    def __init__(self):
        pass

    async def process(self, data: Any) -> Any:
        """Process [feature] request."""
        pass
```

## 📊 Validation System Requirements

### **Required Test Evidence**
1. **Code Coverage** - Minimum 80% coverage with HTML reports
2. **Test Results** - JUnit XML format for automated processing
3. **Requirements Traceability** - CSV mapping tests to requirements
4. **Validation Summary** - Executive summary document
5. **Performance Metrics** - Benchmark and performance data

### **Evidence Generation Commands**
```bash
# Generate complete test evidence
pytest tests/ --cov=src --cov-report=html --cov-report=xml --junitxml=test_reports/execution/results.xml

# Generate requirements traceability
python scripts/validation/generate_traceability.py

# Create validation summary
python scripts/validation/create_evidence_summary.py
```

## 🛠️ Development Commands

### **Makefile Targets**
```makefile
# Standard development commands
make install      # Install dependencies
make test         # Run all tests
make coverage     # Generate coverage reports
make lint         # Run code linting
make format       # Format code
make validate     # Full validation suite
make deploy       # Deploy application
make clean        # Clean generated files
```

### **Scripts Usage**
```bash
# Setup new development environment
python scripts/setup/initialize_project.py

# Validate complete implementation
python scripts/validation/validate_implementation.py

# Run integration tests
python scripts/validation/integration_test.py

# Performance benchmarking
python scripts/performance/performance_benchmark.py
```

## 📝 Documentation Requirements

### **Required Documentation**
- **`README.md`** - Project overview, setup, usage
- **`API_REFERENCE.md`** - Complete MCP tools documentation
- **`TESTING_GUIDE.md`** - Testing instructions for developers
- **`DEPLOYMENT_GUIDE.md`** - Production deployment guide
- **`TROUBLESHOOTING.md`** - Common issues and solutions

### **Development Documentation**
- **`ARCHITECTURE.md`** - System design and architecture
- **`CONTRIBUTING.md`** - Contribution guidelines
- **`CODING_STANDARDS.md`** - Code style and standards

## 🔒 Security and Compliance

### **Security Files**
```
.env.example      # Template (no secrets)
config/*.env      # Environment-specific (gitignored)
.gitignore        # Proper secret exclusion
```

### **Compliance Requirements**
- **Test Evidence** - Complete test documentation
- **Code Coverage** - Minimum coverage thresholds
- **Requirements Traceability** - Test-to-requirement mapping
- **Audit Trail** - Version control and change tracking

## 🎁 Automation and CI/CD

### **Pre-commit Hooks**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
      - id: coverage
        name: Check coverage
        entry: pytest --cov=src --cov-fail-under=80
        language: system
        pass_filenames: false
```

### **GitHub Actions Integration**
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements-dev.txt
          pytest tests/ --cov=src --junitxml=test_reports/execution/results.xml
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_reports/
```

## 📈 Metrics and Monitoring

### **Quality Metrics**
- **Code Coverage** - Line, branch, and function coverage
- **Test Success Rate** - Percentage of passing tests
- **Performance Metrics** - Response times and throughput
- **Error Rates** - Exception and failure tracking

### **Monitoring Files**
```
test_reports/metrics/performance_benchmarks.json
test_reports/metrics/quality_metrics.json
data/logs/application.log
data/logs/performance.log
```

---

## 📋 Quick Start Template

To create a new MCP project using this specification:

1. **Create directory structure**:
   ```bash
   mkdir -p my-mcp-project/{config,docs,src,tests,scripts,data,deploy}
   ```

2. **Copy this specification**:
   ```bash
   cp MCP_PROJECT_STRUCTURE_SPECIFICATION.md my-mcp-project/docs/FOLDER_STRUCTURE.md
   ```

3. **Initialize with template files**:
   ```bash
   python scripts/setup/initialize_project.py
   ```

4. **Start development**:
   ```bash
   cd my-mcp-project
   make install
   make test
   ```

This specification ensures consistency, maintainability, and validation compliance across all MCP projects.