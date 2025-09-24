"""
Contract test for speaker identification functionality.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from pathlib import Path


class TestSpeakerIdentificationContract:
    """Contract tests for speaker diarization and identification."""

    @pytest.fixture
    def mock_whisperx_diarization(self):
        """Mock WhisperX diarization component."""
        diarization = Mock()
        diarization.identify_speakers = AsyncMock()
        diarization.is_available = Mock(return_value=True)
        return diarization

    @pytest.fixture
    def sample_audio_with_speakers(self, tmp_path):
        """Create sample audio file path for multi-speaker testing."""
        audio_file = tmp_path / "multi_speaker.wav"
        audio_file.write_bytes(b"fake multi-speaker audio data")
        return str(audio_file)

    def test_speaker_diarization_identifies_multiple_speakers(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Should identify and differentiate multiple speakers in audio.
        """
        # Mock diarization results
        mock_whisperx_diarization.identify_speakers.return_value = {
            "speakers": ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
            "segments": [
                {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00", "text": "First speaker talking"},
                {"start": 3.5, "end": 6.0, "speaker": "SPEAKER_01", "text": "Second speaker responds"},
                {"start": 6.5, "end": 9.0, "speaker": "SPEAKER_02", "text": "Third speaker joins"},
                {"start": 9.5, "end": 12.0, "speaker": "SPEAKER_00", "text": "First speaker continues"},
            ],
            "speaker_count": 3
        }

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        # This will fail until SpeakerIdentificationService is implemented
        result = asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        assert "speakers" in result
        assert len(result["speakers"]) == 3
        assert "SPEAKER_00" in result["speakers"]
        assert "SPEAKER_01" in result["speakers"]
        assert "SPEAKER_02" in result["speakers"]
        assert result["speaker_count"] == 3

    def test_speaker_segments_have_correct_attribution(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Each segment should be correctly attributed to a speaker.
        """
        mock_whisperx_diarization.identify_speakers.return_value = {
            "segments": [
                {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00", "text": "Hello"},
                {"start": 2.5, "end": 4.5, "speaker": "SPEAKER_01", "text": "Hi there"},
                {"start": 5.0, "end": 7.0, "speaker": "SPEAKER_00", "text": "How are you?"},
            ]
        }

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        result = asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        segments = result["segments"]
        assert segments[0]["speaker"] == "SPEAKER_00"
        assert segments[1]["speaker"] == "SPEAKER_01"
        assert segments[2]["speaker"] == "SPEAKER_00"

        # Verify speaker consistency
        speaker_00_segments = [s for s in segments if s["speaker"] == "SPEAKER_00"]
        assert len(speaker_00_segments) == 2

    def test_speaker_identification_handles_single_speaker(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Should handle audio with only one speaker.
        """
        mock_whisperx_diarization.identify_speakers.return_value = {
            "speakers": ["SPEAKER_00"],
            "segments": [
                {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00", "text": "Single speaker monologue"},
                {"start": 5.5, "end": 10.0, "speaker": "SPEAKER_00", "text": "Continuing the same speaker"},
            ],
            "speaker_count": 1
        }

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        result = asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        assert result["speaker_count"] == 1
        assert len(result["speakers"]) == 1
        assert all(seg["speaker"] == "SPEAKER_00" for seg in result["segments"])

    def test_speaker_identification_can_be_disabled(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Should be able to disable speaker identification for performance.
        """
        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        # When disabled, should not call diarization service
        result = asyncio.run(service.identify_speakers(
            sample_audio_with_speakers,
            enable_diarization=False
        ))

        # Should return generic speaker labels or none
        mock_whisperx_diarization.identify_speakers.assert_not_called()

        # Result should indicate no diarization was performed
        assert result.get("diarization_enabled") is False

    def test_speaker_timing_accuracy(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Speaker segments should have accurate start/end timestamps.
        """
        mock_whisperx_diarization.identify_speakers.return_value = {
            "segments": [
                {"start": 0.125, "end": 2.750, "speaker": "SPEAKER_00", "text": "Precise timing"},
                {"start": 3.000, "end": 5.125, "speaker": "SPEAKER_01", "text": "Another speaker"},
            ]
        }

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        result = asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        segments = result["segments"]

        # Verify timing precision (should support sub-second accuracy)
        assert segments[0]["start"] == 0.125
        assert segments[0]["end"] == 2.750
        assert segments[1]["start"] == 3.000
        assert segments[1]["end"] == 5.125

        # Verify no overlapping segments
        assert segments[0]["end"] <= segments[1]["start"]

    def test_speaker_identification_error_handling(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Should handle diarization errors gracefully.
        """
        mock_whisperx_diarization.identify_speakers.side_effect = Exception("Diarization model failed")

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        # Should either raise informative exception or fallback gracefully
        with pytest.raises(Exception) as exc_info:
            asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        assert "diarization" in str(exc_info.value).lower() or "speaker" in str(exc_info.value).lower()

    def test_speaker_metadata_includes_confidence_scores(self, mock_whisperx_diarization, sample_audio_with_speakers):
        """
        Contract: Should include confidence scores for speaker identification.
        """
        mock_whisperx_diarization.identify_speakers.return_value = {
            "speakers": ["SPEAKER_00", "SPEAKER_01"],
            "segments": [
                {
                    "start": 0.0, "end": 2.0, "speaker": "SPEAKER_00",
                    "text": "High confidence", "speaker_confidence": 0.95
                },
                {
                    "start": 2.5, "end": 4.5, "speaker": "SPEAKER_01",
                    "text": "Lower confidence", "speaker_confidence": 0.78
                },
            ]
        }

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        result = asyncio.run(service.identify_speakers(sample_audio_with_speakers))

        for segment in result["segments"]:
            assert "speaker_confidence" in segment
            assert 0.0 <= segment["speaker_confidence"] <= 1.0

    def test_speaker_service_validates_audio_format(self, mock_whisperx_diarization):
        """
        Contract: Should validate audio file format before processing.
        """
        invalid_audio_path = "/path/to/invalid.txt"

        from src.services.speaker_service import SpeakerIdentificationService
        service = SpeakerIdentificationService(diarization_service=mock_whisperx_diarization)

        with pytest.raises(ValueError) as exc_info:
            asyncio.run(service.identify_speakers(invalid_audio_path))

        assert "audio format" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()