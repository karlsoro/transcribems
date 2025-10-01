# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TranscribeMCP is a structured feature development framework built on the "specKit" system. It provides a comprehensive workflow for specification-driven development with enterprise-grade standards and automated tooling. The project operates within the `transcribe_mcp/` subdirectory and uses custom Claude commands for feature development.

## Architecture and Structure

This is a **specification-first development environment** with the following key components:

### Core Framework Components

- **`.specify/`** - Core framework containing:
  - `memory/constitution.md` - Enterprise IT standards and constraints (1100+ lines of comprehensive standards)
  - `templates/` - Templates for specs, plans, tasks, and agent files
  - `scripts/bash/` - Automation scripts for setup and management

- **`.claude/commands/`** - Custom Claude commands for the development workflow:
  - `/specify` - Generate feature specifications
  - `/clarify` - Clarify ambiguous requirements
  - `/plan` - Create implementation plans
  - `/tasks` - Break down features into executable tasks
  - `/implement` - Execute the implementation
  - `/analyze` - Cross-artifact consistency analysis
  - `/constitution` - Create or update the project constitution

### Feature Development Workflow

Features are developed in structured directories under `specs/{branch}/`:
```
specs/
└── 001-feature-name/
    ├── spec.md           # Feature specification
    ├── plan.md           # Implementation plan
    ├── tasks.md          # Task breakdown
    ├── data-model.md     # Data entities and relationships
    ├── research.md       # Technical decisions and research
    ├── quickstart.md     # Integration scenarios
    └── contracts/        # API specifications and tests
```

## Development Commands and Workflow

### Core Claude Commands
Execute these commands in order for feature development:

1. **`/specify "<feature description>"`** - Generate feature specification
2. **`/clarify`** - Clarify any ambiguous requirements (run if needed)
3. **`/plan`** - Create technical implementation plan
4. **`/tasks`** - Generate detailed task breakdown
5. **`/analyze`** - Validate consistency across artifacts
6. **`/implement`** - Execute the implementation

### Constitution Management Command
- **`/constitution`** - Create or update the project constitution with interactive principle inputs, maintaining template synchronization

### Script Commands
- **`./specify/scripts/bash/check-prerequisites.sh`** - Check environment and artifacts
- **`./specify/scripts/bash/setup-plan.sh`** - Initialize planning environment
- **`./specify/scripts/bash/create-new-feature.sh`** - Create new feature structure

## Key Development Principles

### Constitution-Driven Development
The project follows strict enterprise standards defined in `constitution.md`:

- **Technology Stack**: React 18+ with TypeScript, Material-UI, Node.js/Python backends
- **Security**: SSO with Azure AD, OWASP Top 10 compliance, comprehensive security controls
- **Architecture**: Microservices, REST APIs, PostgreSQL databases
- **Deployment**: Azure cloud with GitHub Actions CI/CD
- **Testing**: 80% minimum coverage, TDD approach

### Branch and Feature Management
- Features use numbered branch format: `001-feature-name`
- Non-git repositories fall back to feature directory structure
- Environment variable `SPECIFY_FEATURE` can override branch detection

### Quality Gates and Validation
- Constitution compliance is **non-negotiable**
- Cross-artifact consistency validation before implementation
- Security scanning and vulnerability assessment required
- Performance and accessibility standards enforcement

## Working with This Repository

### When Starting New Features
1. Ensure you're on a properly named feature branch (`001-feature-name`) or set `SPECIFY_FEATURE` environment variable
2. Use `/specify` command to generate initial specification
3. Follow the complete workflow through `/implement`

### When Modifying Existing Features
1. Run `/analyze` to check current state consistency
2. Update specifications before making changes
3. Re-run task breakdown if architecture changes

### Understanding the Constitution
The `constitution.md` file contains:
- Technology stack requirements and prohibited technologies
- Comprehensive security standards (OWASP Top 10)
- UI/UX standards with specific color palettes and Material-UI configuration
- Data governance and compliance requirements (GDPR, CCPA, SOX)
- CI/CD pipeline requirements with Azure deployment standards

### Enterprise Standards Compliance
All development must adhere to:
- **Authentication**: Azure AD SSO required
- **Security**: TLS 1.3, AES-256 encryption, comprehensive security headers
- **Performance**: 3-second page load, Core Web Vitals compliance
- **Accessibility**: WCAG 2.1 AA compliance
- **Testing**: Jest/pytest frameworks, 80% coverage minimum

## Important Notes

- **No package.json or traditional build commands** - This is a specification and workflow framework
- **Custom command system** - Use Claude commands (`/specify`, `/plan`, etc.) instead of npm/pip commands
- **Constitution is authoritative** - Technical decisions must align with enterprise standards
- **Feature-centric structure** - Work happens in feature-specific directories under `specs/`
- **Git optional** - Framework works with or without git repositories

## Tips for Claude Code Development

1. **Always check constitution compliance** when making technical decisions
2. **Use the custom commands** - they're specifically designed for this workflow
3. **Follow the phase structure** - Setup → Tests → Core → Integration → Polish
4. **Validate cross-artifact consistency** with `/analyze` before implementation
5. **Respect enterprise security and performance standards**
