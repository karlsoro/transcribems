# TranscribeMS Development Makefile

.PHONY: help install dev-install test lint format clean docker-build docker-run

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run test suite"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-fast:
	pytest tests/ -v -m "not slow"

test-integration:
	pytest tests/integration/ -v

test-unit:
	pytest tests/unit/ -v

# Code Quality
lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker
docker-build:
	docker build -t transcribems:latest .

docker-run:
	docker-compose up --build

# Development
dev:
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	celery -A src.tasks.celery_app worker --loglevel=info

# Documentation
docs:
	mkdocs serve

# Database/Storage
setup-dirs:
	mkdir -p uploads transcriptions logs

# Security
security-check:
	bandit -r src/
	safety check