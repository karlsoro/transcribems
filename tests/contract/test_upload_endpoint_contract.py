"""
Contract test for audio file upload endpoint.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import Mock
import io


@pytest.fixture
def client():
    """FastAPI test client - will fail until app is implemented."""
    from src.main import app  # This import will fail initially
    return TestClient(app)


@pytest.fixture
def sample_audio_file():
    """Mock audio file for testing."""
    # Create a mock audio file with proper content
    audio_content = b"RIFF" + b"\x00" * 40  # Mock WAV header
    return io.BytesIO(audio_content)


class TestAudioUploadContract:
    """Contract tests for audio file upload endpoint."""

    def test_upload_endpoint_accepts_valid_audio_file(self, client, sample_audio_file):
        """
        Contract: POST /v1/transcribe should accept valid audio files.
        Expected Response: 202 Accepted with job_id.
        """
        response = client.post(
            "/v1/transcribe",
            files={"file": ("test.wav", sample_audio_file, "audio/wav")},
            data={"language": "auto", "enable_speaker_diarization": True}
        )

        assert response.status_code == 202
        assert "job_id" in response.json()
        assert "message" in response.json()
        assert response.json()["message"] == "Transcription job started"

    def test_upload_endpoint_validates_file_format(self, client):
        """
        Contract: Should reject unsupported file formats.
        Expected Response: 422 Unprocessable Entity.
        """
        invalid_file = io.BytesIO(b"not an audio file")
        response = client.post(
            "/v1/transcribe",
            files={"file": ("test.txt", invalid_file, "text/plain")}
        )

        assert response.status_code == 422
        assert "error" in response.json()
        assert "Unsupported audio format" in response.json()["error"]

    def test_upload_endpoint_validates_file_size(self, client):
        """
        Contract: Should reject files exceeding size limit.
        Expected Response: 413 Request Entity Too Large.
        """
        # Mock large file (6GB)
        large_file = Mock()
        large_file.size = 6 * 1024 * 1024 * 1024  # 6GB

        response = client.post(
            "/v1/transcribe",
            files={"file": ("large.wav", large_file, "audio/wav")}
        )

        assert response.status_code == 413
        assert "error" in response.json()
        assert "File too large" in response.json()["error"]

    def test_upload_endpoint_requires_file(self, client):
        """
        Contract: Should require file parameter.
        Expected Response: 422 Unprocessable Entity.
        """
        response = client.post("/v1/transcribe")

        assert response.status_code == 422
        assert "error" in response.json()

    def test_upload_response_includes_job_tracking(self, client, sample_audio_file):
        """
        Contract: Successful upload should return job tracking information.
        """
        response = client.post(
            "/v1/transcribe",
            files={"file": ("test.wav", sample_audio_file, "audio/wav")}
        )

        data = response.json()
        assert "job_id" in data
        assert "status_url" in data
        assert data["status_url"].endswith(f"/v1/jobs/{data['job_id']}")

    def test_upload_accepts_optional_parameters(self, client, sample_audio_file):
        """
        Contract: Should accept optional transcription parameters.
        """
        response = client.post(
            "/v1/transcribe",
            files={"file": ("test.wav", sample_audio_file, "audio/wav")},
            data={
                "language": "en",
                "enable_speaker_diarization": False,
                "model_size": "medium"
            }
        )

        assert response.status_code == 202

    def test_upload_validates_language_parameter(self, client, sample_audio_file):
        """
        Contract: Should validate language parameter if provided.
        """
        response = client.post(
            "/v1/transcribe",
            files={"file": ("test.wav", sample_audio_file, "audio/wav")},
            data={"language": "invalid-lang"}
        )

        assert response.status_code == 422
        assert "Invalid language code" in response.json()["error"]