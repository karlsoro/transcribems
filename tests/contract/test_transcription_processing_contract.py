"""
Contract test for transcription processing functionality.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
from pathlib import Path
import json


class TestTranscriptionProcessingContract:
    """Contract tests for transcription processing service."""

    @pytest.fixture
    def mock_whisperx_service(self):
        """Mock WhisperX service for testing."""
        service = Mock()
        service.transcribe_audio = AsyncMock()
        service.identify_speakers = AsyncMock()
        service.is_gpu_available = Mock(return_value=True)
        return service

    @pytest.fixture
    def sample_audio_path(self, tmp_path):
        """Create a temporary audio file for testing."""
        audio_file = tmp_path / "test_audio.wav"
        audio_file.write_bytes(b"fake audio data")
        return str(audio_file)

    def test_transcribe_audio_returns_segments_with_timestamps(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: transcribe_audio should return segments with start/end timestamps.
        """
        # Mock expected return structure
        expected_segments = [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world",
                "speaker": "SPEAKER_00"
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "How are you today?",
                "speaker": "SPEAKER_01"
            }
        ]
        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": expected_segments,
            "language": "en",
            "processing_time": 12.34
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        # This will fail until TranscriptionService is implemented
        result = asyncio.run(service.process_audio_file(sample_audio_path))

        assert "segments" in result
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 2.5
        assert result["segments"][0]["text"] == "Hello world"
        assert result["segments"][0]["speaker"] == "SPEAKER_00"

    def test_transcription_includes_speaker_identification(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: Should identify and label speakers when diarization is enabled.
        """
        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "First speaker", "speaker": "SPEAKER_00"},
                {"start": 3.0, "end": 5.5, "text": "Second speaker", "speaker": "SPEAKER_01"},
            ],
            "speakers": ["SPEAKER_00", "SPEAKER_01"],
            "language": "en"
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        result = asyncio.run(service.process_audio_file(
            sample_audio_path,
            enable_speaker_diarization=True
        ))

        assert "speakers" in result
        assert len(result["speakers"]) == 2
        assert "SPEAKER_00" in result["speakers"]
        assert "SPEAKER_01" in result["speakers"]

    def test_transcription_handles_language_detection(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: Should detect language automatically when language='auto'.
        """
        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": [{"start": 0.0, "end": 2.5, "text": "Bonjour monde", "speaker": "SPEAKER_00"}],
            "language": "fr",
            "language_probability": 0.98
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        result = asyncio.run(service.process_audio_file(
            sample_audio_path,
            language="auto"
        ))

        assert result["language"] == "fr"
        assert "language_probability" in result
        assert result["language_probability"] > 0.9

    def test_transcription_uses_specified_language(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: Should use specified language when provided.
        """
        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": [{"start": 0.0, "end": 2.5, "text": "Hello world", "speaker": "SPEAKER_00"}],
            "language": "en"
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        _ = asyncio.run(service.process_audio_file(  # Unused result
            sample_audio_path,
            language="en"
        ))

        # Verify the service was called with correct language
        mock_whisperx_service.transcribe_audio.assert_called_once()
        call_args = mock_whisperx_service.transcribe_audio.call_args[1]
        assert call_args["language"] == "en"

    def test_transcription_saves_output_file(self, mock_whisperx_service, sample_audio_path, tmp_path):
        """
        Contract: Should save transcription to JSON file in output directory.
        """
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": [{"start": 0.0, "end": 2.5, "text": "Test content", "speaker": "SPEAKER_00"}],
            "language": "en"
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        result = asyncio.run(service.process_audio_file(
            sample_audio_path,
            output_dir=str(output_dir)
        ))

        assert "output_file" in result
        output_file = Path(result["output_file"])
        assert output_file.exists()
        assert output_file.suffix == ".json"

        # Verify JSON content
        with open(output_file) as f:
            saved_data = json.load(f)
        assert "segments" in saved_data
        assert saved_data["segments"][0]["text"] == "Test content"

    def test_transcription_handles_processing_errors(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: Should handle and report processing errors gracefully.
        """
        mock_whisperx_service.transcribe_audio.side_effect = Exception("WhisperX processing failed")

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        with pytest.raises(Exception) as exc_info:
            asyncio.run(service.process_audio_file(sample_audio_path))

        assert "processing failed" in str(exc_info.value).lower()

    def test_transcription_reports_processing_time(self, mock_whisperx_service, sample_audio_path):
        """
        Contract: Should track and report processing time.
        """
        mock_whisperx_service.transcribe_audio.return_value = {
            "segments": [{"start": 0.0, "end": 2.5, "text": "Test", "speaker": "SPEAKER_00"}],
            "language": "en",
            "processing_time": 15.75
        }

        from src.services.transcription_service import TranscriptionService
        service = TranscriptionService(whisperx_service=mock_whisperx_service)

        result = asyncio.run(service.process_audio_file(sample_audio_path))

        assert "processing_time" in result
        assert isinstance(result["processing_time"], float)
        assert result["processing_time"] > 0
