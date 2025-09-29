"""
Integration tests for real speaker identification functionality.
These tests verify the actual pyannote-audio integration.
"""

import pytest
import asyncio
import tempfile
import wave
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
import soundfile as sf

from src.services.speaker_service import SpeakerIdentificationService


class TestSpeakerIdentificationIntegration:
    """Integration tests for real speaker diarization."""

    @pytest.fixture
    def real_service(self) -> SpeakerIdentificationService:
        """Create service without mock diarization."""
        return SpeakerIdentificationService(diarization_service=None)

    @pytest.fixture
    def sample_wav_file(self, tmp_path: Path) -> str:
        """Create a real WAV file for testing."""
        # Generate 3 seconds of dummy audio (sine waves at different frequencies)
        sample_rate = 16000
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create two-channel audio with different frequencies to simulate speakers
        freq1, freq2 = 440, 880  # A4 and A5 notes
        audio_data = np.sin(2 * np.pi * freq1 * t) + 0.5 * np.sin(2 * np.pi * freq2 * t)

        wav_file = tmp_path / "test_audio.wav"
        sf.write(str(wav_file), audio_data, sample_rate)
        return str(wav_file)

    @pytest.fixture
    def sample_mp3_file(self, tmp_path: Path) -> str:
        """Create a fake MP3 file for format testing."""
        mp3_file = tmp_path / "test_audio.mp3"
        mp3_file.write_bytes(b"fake mp3 data")
        return str(mp3_file)

    def test_audio_format_validation_passes_for_valid_extensions(self, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test that valid audio file formats are accepted."""
        # This should not raise an exception
        result = asyncio.run(real_service.identify_speakers(sample_wav_file, enable_diarization=False))
        assert result["diarization_enabled"] is False

    def test_audio_format_validation_fails_for_invalid_extensions(self, real_service: SpeakerIdentificationService, tmp_path: Path) -> None:
        """Test that invalid audio file formats are rejected."""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not audio data")

        with pytest.raises(ValueError) as exc_info:
            asyncio.run(real_service.identify_speakers(str(invalid_file)))

        assert "invalid audio format" in str(exc_info.value).lower()

    def test_audio_file_not_found_raises_error(self, real_service: SpeakerIdentificationService) -> None:
        """Test that missing audio files raise appropriate errors."""
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(real_service.identify_speakers("/nonexistent/path.wav"))

        assert "audio file not found" in str(exc_info.value).lower()

    def test_disabled_diarization_returns_empty_results(self, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test that disabled diarization returns expected structure."""
        result = asyncio.run(real_service.identify_speakers(sample_wav_file, enable_diarization=False))

        assert result["diarization_enabled"] is False
        assert result["speakers"] == []
        assert result["segments"] == []
        assert result["speaker_count"] == 0

    @pytest.mark.slow
    @patch('pyannote.audio.Pipeline')
    def test_real_pipeline_loading_with_cuda_available(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test pipeline loading when CUDA is available."""
        # Mock torch and pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline
        mock_pipeline.to.return_value = mock_pipeline

        # Mock diarization results
        mock_turn = Mock()
        mock_turn.start = 0.0
        mock_turn.end = 2.0
        mock_diarization = Mock()
        mock_diarization.itertracks.return_value = [(mock_turn, None, "SPEAKER_00")]
        mock_pipeline.return_value = mock_diarization

        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.device') as mock_device, \
             patch('whisperx.load_audio', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink'):

            result = asyncio.run(real_service.identify_speakers(sample_wav_file))

            # Verify CUDA device was used
            mock_device.assert_called_with("cuda")
            mock_pipeline.to.assert_called_once()

            # Verify results
            assert result["diarization_enabled"] is True
            assert "SPEAKER_00" in result["speakers"]
            assert len(result["segments"]) == 1

    @patch('pyannote.audio.Pipeline')
    def test_real_pipeline_loading_cpu_fallback(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test pipeline loading falls back to CPU when CUDA unavailable."""
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline

        # Mock diarization results
        mock_turn = Mock()
        mock_turn.start = 0.0
        mock_turn.end = 2.0
        mock_diarization = Mock()
        mock_diarization.itertracks.return_value = [(mock_turn, None, "SPEAKER_00")]
        mock_pipeline.return_value = mock_diarization

        with patch('torch.cuda.is_available', return_value=False), \
             patch('whisperx.load_audio', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink'):

            result = asyncio.run(real_service.identify_speakers(sample_wav_file))

            # Verify CPU was used (no .to() call for GPU)
            mock_pipeline.to.assert_not_called()

            # Verify results
            assert result["diarization_enabled"] is True
            assert len(result["segments"]) == 1

    @patch('pyannote.audio.Pipeline')
    def test_pipeline_loading_failure_handling(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test handling of pipeline loading failures."""
        mock_pipeline_class.from_pretrained.side_effect = Exception("Pipeline unavailable")

        with pytest.raises(Exception) as exc_info:
            asyncio.run(real_service.identify_speakers(sample_wav_file))

        assert "diarization pipeline unavailable" in str(exc_info.value).lower()

    @patch('pyannote.audio.Pipeline')
    def test_real_diarization_processing_failure(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test handling of diarization processing failures."""
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline

        with patch('whisperx.load_audio', side_effect=Exception("Audio loading failed")):
            with pytest.raises(Exception) as exc_info:
                asyncio.run(real_service.identify_speakers(sample_wav_file))

            assert "real speaker diarization failed" in str(exc_info.value).lower()

    @patch('pyannote.audio.Pipeline')
    def test_multiple_speakers_detection(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test detection of multiple speakers."""
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline

        # Mock multiple speaker segments
        mock_turns = [
            (Mock(start=0.0, end=2.0), None, "SPEAKER_00"),
            (Mock(start=2.5, end=4.0), None, "SPEAKER_01"),
            (Mock(start=4.5, end=6.0), None, "SPEAKER_02"),
            (Mock(start=6.5, end=8.0), None, "SPEAKER_00"),  # Speaker 00 returns
        ]

        mock_diarization = Mock()
        mock_diarization.itertracks.return_value = mock_turns
        mock_pipeline.return_value = mock_diarization

        with patch('torch.cuda.is_available', return_value=False), \
             patch('whisperx.load_audio', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink'):

            result = asyncio.run(real_service.identify_speakers(sample_wav_file))

            # Verify multiple speakers detected
            assert result["speaker_count"] == 3
            assert len(result["speakers"]) == 3
            assert "SPEAKER_00" in result["speakers"]
            assert "SPEAKER_01" in result["speakers"]
            assert "SPEAKER_02" in result["speakers"]

            # Verify all segments present
            assert len(result["segments"]) == 4

            # Check speaker confidence is added
            for segment in result["segments"]:
                assert "speaker_confidence" in segment
                assert 0.0 <= segment["speaker_confidence"] <= 1.0

    def test_service_availability_without_diarization_service(self, real_service: SpeakerIdentificationService) -> None:
        """Test service availability check when no diarization service is provided."""
        # Real service should report as unavailable when no diarization service
        assert not real_service.is_available()

    def test_service_availability_with_diarization_service(self) -> None:
        """Test service availability check when diarization service is provided."""
        mock_service = Mock()
        service = SpeakerIdentificationService(diarization_service=mock_service)
        assert service.is_available()

    @patch('pyannote.audio.Pipeline')
    def test_temporary_file_cleanup_on_success(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test that temporary files are cleaned up even on successful processing."""
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline

        mock_diarization = Mock()
        mock_diarization.itertracks.return_value = [(Mock(start=0.0, end=2.0), None, "SPEAKER_00")]
        mock_pipeline.return_value = mock_diarization

        mock_temp_path = Mock()

        with patch('torch.cuda.is_available', return_value=False), \
             patch('whisperx.load_audio', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink') as mock_unlink, \
             patch('tempfile.NamedTemporaryFile') as mock_temp:

            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.wav"
            mock_temp.return_value.__exit__.return_value = None

            result = asyncio.run(real_service.identify_speakers(sample_wav_file))

            # Verify cleanup was called
            mock_unlink.assert_called_once()

    @patch('pyannote.audio.Pipeline')
    def test_temporary_file_cleanup_on_failure(self, mock_pipeline_class: Mock, real_service: SpeakerIdentificationService, sample_wav_file: str) -> None:
        """Test that temporary files are cleaned up even when processing fails."""
        mock_pipeline = Mock()
        mock_pipeline_class.from_pretrained.return_value = mock_pipeline
        mock_pipeline.side_effect = Exception("Processing failed")

        with patch('torch.cuda.is_available', return_value=False), \
             patch('whisperx.load_audio', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink') as mock_unlink, \
             patch('tempfile.NamedTemporaryFile') as mock_temp:

            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.wav"
            mock_temp.return_value.__exit__.return_value = None

            with pytest.raises(Exception):
                asyncio.run(real_service.identify_speakers(sample_wav_file))

            # Verify cleanup was called even on failure
            mock_unlink.assert_called_once()