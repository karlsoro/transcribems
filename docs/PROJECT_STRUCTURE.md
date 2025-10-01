# TranscribeMCP Project Structure

This document describes the organized directory structure of the TranscribeMCP project.

## 📁 Directory Overview

```
TranscribeMCP/
├── src/                          # Source code
│   ├── mcp_server/              # MCP server implementations
│   │   ├── server.py            # Main MCP server (stdio, HTTP/SSE, HTTP/StreamableHTTP)
│   │   ├── cli.py               # CLI interface for server modes
│   │   └── fastmcp_server.py    # Legacy FastMCP implementation
│   ├── models/                  # Data models
│   ├── services/                # Business logic services
│   └── tools/                   # MCP tool implementations
│
├── tests/                       # All test files
│   ├── integration/             # Integration tests
│   │   ├── test_mcp_integration.py
│   │   ├── test_complete_pipeline.py
│   │   ├── test_http_server.py  # HTTP server integration tests
│   │   └── test_*.py
│   ├── test_cli.py              # CLI functionality tests
│   ├── validation/              # Validation tests
│   │   └── production_validation_test.py
│   ├── results/                 # Test results and outputs
│   │   ├── *.json               # JSON test results
│   │   └── *.txt                # Text outputs
│   ├── outputs/                 # Test execution outputs
│   │   ├── cli_tests/           # CLI test outputs
│   │   ├── e2e_tests/           # End-to-end test outputs
│   │   ├── gpu_tests/           # GPU test outputs
│   │   ├── validation/          # Validation outputs
│   │   ├── debug/               # Debug outputs
│   │   └── transcripts/         # Transcript outputs
│   └── logs/                    # Test execution logs
│       └── *.log                # Log files
│
├── docs/                        # Documentation
│   ├── guides/                  # User guides
│   │   ├── MCP_CONNECTION_GUIDE.md
│   │   ├── MCP_QUICK_REFERENCE.md
│   │   ├── MCP_SERVER_READY.md
│   │   ├── MCP_PROJECT_STRUCTURE_SPECIFICATION.md
│   │   ├── DEPLOYMENT_PACKAGE.md
│   │   ├── FINAL_PRODUCTION_VALIDATION.md
│   │   ├── PRODUCTION_READY_DEPLOYMENT.md
│   │   └── WORKING_SYSTEM_VALIDATION.md
│   ├── api/                     # API documentation
│   ├── INTEGRATION_EXAMPLES.md  # Integration code examples (stdio clients)
│   ├── HTTP_CLIENT_EXAMPLES.md  # HTTP client examples (Python, JS, cURL)
│   ├── SERVER_MODES.md          # Complete server modes guide
│   ├── QUICK_START_CLI.md       # CLI quick reference
│   ├── CHANGELOG_CLI.md         # CLI enhancement changelog
│   └── PROJECT_STRUCTURE.md     # This file
│
├── scripts/                     # Utility scripts
│   ├── setup/                   # Setup and initialization
│   ├── utils/                   # Utility scripts
│   │   ├── fix_audio_backend.py
│   │   ├── fix_lightning_checkpoint.py
│   │   ├── fix_whisperx_environment.py
│   │   └── reorganize_folders.py
│   ├── start_mcp_server.sh      # MCP server startup
│   └── test_mcp_connection.py   # Connection test utility
│
├── config/                      # Configuration files
├── data/                        # Data files
├── deploy/                      # Deployment configurations
│
├── specs/                       # Feature specifications
├── implement/                   # Implementation tracking
│
├── test_data/                   # Test audio files
├── production_validation/       # Production validation artifacts
├── validation_results/          # Validation outputs
│
├── transcribe_mcp_env/            # Python virtual environment
│
├── CLAUDE.md                    # Project-level Claude instructions
├── README.md                    # Project overview
├── pyproject.toml              # Python project configuration
└── pyrightconfig.json          # Python type checking config
```

## 📂 Key Directory Purposes

### `/src` - Source Code
All production source code organized by function:
- **mcp_server/**: MCP protocol server implementations
  - `server.py`: Multi-transport server (stdio, HTTP/SSE, HTTP/StreamableHTTP)
  - `cli.py`: Command-line interface with mode selection
  - `fastmcp_server.py`: Legacy FastMCP implementation
- **models/**: Pydantic data models and schemas
- **services/**: Business logic and service layer
- **tools/**: Individual MCP tool implementations

### `/tests` - Test Suite
All test files organized by type:
- **integration/**: End-to-end and integration tests
- **validation/**: Production validation and smoke tests
- **results/**: Test result files (JSON, text)
- **outputs/**: Test execution outputs organized by category
  - **cli_tests/**: CLI test outputs
  - **e2e_tests/**: End-to-end test outputs
  - **gpu_tests/**: GPU test outputs
  - **validation/**: Validation test outputs
  - **debug/**: Debug and diagnostic outputs
  - **transcripts/**: Generated transcript files
- **logs/**: Test execution log files

### `/docs` - Documentation
All project documentation:
- **guides/**: User guides, setup instructions, deployment docs
- **api/**: API documentation and specifications
- **INTEGRATION_EXAMPLES.md**: Code examples for integration
- **PROJECT_STRUCTURE.md**: This file

### `/scripts` - Automation Scripts
Utility and automation scripts:
- **setup/**: Installation and setup scripts
- **utils/**: Maintenance and fix scripts
- **start_mcp_server.sh**: Quick-start server launcher
- **test_mcp_connection.py**: Connection verification tool

### `/config` - Configuration
Configuration files and templates

### `/data` - Data Files
Audio samples, test data, and datasets

### `/deploy` - Deployment
Deployment configurations, Docker files, and infrastructure

### `/specs` - Specifications
Feature specifications and planning documents (specKit framework)

### `/test_data` - Test Audio Files
Audio files used for testing transcription

## 🎯 File Organization Principles

### Tests
- ✅ All test files in `/tests/`
- ✅ Organized by test type (integration, validation)
- ✅ Test results in `/tests/results/`
- ✅ Test outputs in `/tests/outputs/` (organized by category)
- ✅ Test logs in `/tests/logs/`
- ❌ No test files in project root
- ❌ No test outputs in project root

### Documentation
- ✅ All `.md` docs in `/docs/`
- ✅ Guides in `/docs/guides/`
- ✅ API docs in `/docs/api/`
- ❌ Only `README.md` and `CLAUDE.md` in root

### Scripts
- ✅ All scripts in `/scripts/`
- ✅ Utility scripts in `/scripts/utils/`
- ✅ Setup scripts in `/scripts/setup/`
- ❌ No loose `.py` scripts in root

### Source Code
- ✅ All production code in `/src/`
- ✅ Organized by module type
- ✅ Clear separation of concerns
- ❌ No source files in root

## 📍 Important File Locations

### MCP Server
- **Main Server**: `src/mcp_server/server.py`
- **FastMCP Server**: `src/mcp_server/fastmcp_server.py` (recommended)
- **Startup Script**: `scripts/start_mcp_server.sh`
- **Test Script**: `scripts/test_mcp_connection.py`

### Documentation
- **Connection Guide**: `docs/guides/MCP_CONNECTION_GUIDE.md`
- **Quick Reference**: `docs/guides/MCP_QUICK_REFERENCE.md`
- **Integration Examples**: `docs/INTEGRATION_EXAMPLES.md`
- **Server Status**: `docs/guides/MCP_SERVER_READY.md`

### Configuration
- **Python Config**: `pyproject.toml` (root)
- **Type Checking**: `pyrightconfig.json` (root)
- **Project Instructions**: `CLAUDE.md` (root)

### Tests
- **Integration Tests**: `tests/integration/test_*.py`
- **Validation Tests**: `tests/validation/production_validation_test.py`
- **Test Results**: `tests/results/*.json`
- **Test Outputs**: `tests/outputs/` (cli_tests, e2e_tests, gpu_tests, validation, debug, transcripts)
- **Test Logs**: `tests/logs/*.log`

## 🔄 Migration Summary

Files moved during reorganization:

### From Root → `/tests/integration/`
- `test_complete_pipeline.py`
- `test_direct_services.py`
- `test_final_pipeline.py`
- `test_fixed_whisperx.py`
- `test_fixes_validation.py`
- `test_gpu_enhanced_service.py`
- `test_large_real_audio.py`
- `test_large_with_speakers.py`
- `test_mcp_integration.py`
- `test_proper_whisperx_integration.py`
- `test_proper_whisperx.py`
- `test_service_validation.py`
- `test_torchcodec_integration.py`
- `test_true_whisperx_native.py`
- `test_working_transcription.py`
- `simple_mcp_test.py`

### From Root → `/tests/validation/`
- `production_validation_test.py`

### From Root → `/tests/results/`
- `*.json` (test result files)
- `multi_speaker.txt`

### From Root → `/docs/guides/`
- `MCP_CONNECTION_GUIDE.md`
- `MCP_QUICK_REFERENCE.md`
- `MCP_SERVER_READY.md`
- `MCP_PROJECT_STRUCTURE_SPECIFICATION.md`
- `DEPLOYMENT_PACKAGE.md`
- `FINAL_PRODUCTION_VALIDATION.md`
- `PRODUCTION_READY_DEPLOYMENT.md`
- `WORKING_SYSTEM_VALIDATION.md`

### From Root → `/scripts/utils/`
- `fix_audio_backend.py`
- `fix_lightning_checkpoint.py`
- `fix_whisperx_environment.py`
- `reorganize_folders.py`

## 🚀 Quick Navigation

| Need to... | Go to... |
|------------|----------|
| Start MCP server | `scripts/start_mcp_server.sh` |
| Test connection | `scripts/test_mcp_connection.py` |
| View integration guide | `docs/guides/MCP_CONNECTION_GUIDE.md` |
| See code examples | `docs/INTEGRATION_EXAMPLES.md` |
| Run integration tests | `tests/integration/` |
| Check server code | `src/mcp_server/fastmcp_server.py` |
| View project overview | `README.md` |
| Configure project | `pyproject.toml` |

## 📝 Maintenance Notes

- Keep test files in `/tests/` organized by type
- Place all documentation in `/docs/` with appropriate subdirectories
- Utility scripts go in `/scripts/utils/`
- Source code stays in `/src/` with clear module separation
- Root directory should only contain essential config files

---

**Last Updated**: 2025-09-30
**Version**: 1.0.0
**Status**: ✅ Organized and Current
