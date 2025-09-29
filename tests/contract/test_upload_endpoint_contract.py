"""
Contract test for audio file upload endpoint.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import io


@pytest.fixture
def client():
    """FastAPI test client - will fail until app is implemented."""
    from src.main import app  # This import will fail initially
    return TestClient(app)


@pytest.fixture
def sample_audio_file():
    """Create a minimal valid WAV file for testing."""
    # Create a minimal valid WAV file (44 bytes header + 1 sample)
    # WAV file format: RIFF header + fmt chunk + data chunk
    wav_header = (
        b'RIFF'                    # Chunk ID
        b'\x2d\x00\x00\x00'       # Chunk size (45 bytes total - 8)
        b'WAVE'                    # Format
        b'fmt '                    # Subchunk1 ID
        b'\x10\x00\x00\x00'       # Subchunk1 size (16 for PCM)
        b'\x01\x00'               # Audio format (1 = PCM)
        b'\x01\x00'               # Number of channels (1)
        b'\x44\xac\x00\x00'       # Sample rate (44100)
        b'\x44\xac\x00\x00'       # Byte rate
        b'\x01\x00'               # Block align
        b'\x08\x00'               # Bits per sample (8)
        b'data'                    # Subchunk2 ID
        b'\x01\x00\x00\x00'       # Subchunk2 size (1 byte of data)
        b'\x80'                    # One sample of audio data
    )
    return io.BytesIO(wav_header)


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
