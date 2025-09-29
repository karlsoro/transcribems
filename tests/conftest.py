"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[TestClient, None]:
    """Create a test client for the FastAPI application."""
    # This will be implemented once the main app is created
    pass


@pytest.fixture
def sample_audio_file():
    """Provide path to sample audio file for testing."""
    # This will be implemented with actual test audio files
    pass


@pytest.fixture
def mock_whisperx():
    """Mock WhisperX service for testing without actual AI processing."""
    # This will be implemented for unit testing
    pass
