"""
Unit tests for speaker service edge cases and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.services.speaker_service import SpeakerIdentificationService


class TestSpeakerServiceEdgeCases:
    """Test edge cases and error handling in speaker service."""

    def test_test_service_with_sync_method(self, tmp_path: Path) -> None:
        """Test backward compatibility with synchronous test services."""
        # Create mock service with sync method
        mock_service = Mock()
        mock_service.identify_speakers = Mock(return_value={
            "speakers": ["SPEAKER_00"],
            "segments": [{"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00", "text": "Test"}],
            "speaker_count": 1
        })

        service = SpeakerIdentificationService(diarization_service=mock_service)

        # Create valid audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        result = asyncio.run(service.identify_speakers(str(audio_file)))

        # Verify sync method was called and result processed
        mock_service.identify_speakers.assert_called_once_with(str(audio_file))
        assert result["diarization_enabled"] is True
        assert len(result["speakers"]) == 1
        assert result["speaker_count"] == 1

        # Verify default confidence was added
        assert result["segments"][0]["speaker_confidence"] == 0.9

    def test_test_service_with_async_method(self, tmp_path: Path) -> None:
        """Test backward compatibility with asynchronous test services."""
        # Create mock service with async method
        mock_service = Mock()
        mock_service.identify_speakers = AsyncMock(return_value={
            "speakers": ["SPEAKER_00", "SPEAKER_01"],
            "segments": [
                {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00", "text": "First", "speaker_confidence": 0.95},
                {"start": 2.5, "end": 4.0, "speaker": "SPEAKER_01", "text": "Second"}
            ]
        })

        service = SpeakerIdentificationService(diarization_service=mock_service)

        # Create valid audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        result = asyncio.run(service.identify_speakers(str(audio_file)))

        # Verify async method was called
        mock_service.identify_speakers.assert_called_once_with(str(audio_file))
        assert result["diarization_enabled"] is True
        assert len(result["speakers"]) == 2

        # Verify confidence handling (existing + default)
        segments = result["segments"]
        assert segments[0]["speaker_confidence"] == 0.95  # Original
        assert segments[1]["speaker_confidence"] == 0.9   # Default added

    def test_test_service_missing_method(self, tmp_path: Path) -> None:
        """Test error when test service is missing identify_speakers method."""
        # Create a mock that doesn't have identify_speakers
        class MockServiceWithoutMethod:
            pass

        mock_service = MockServiceWithoutMethod()
        service = SpeakerIdentificationService(diarization_service=mock_service)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        with pytest.raises(Exception) as exc_info:
            asyncio.run(service.identify_speakers(str(audio_file)))

        error_message = str(exc_info.value).lower()
        assert "missing identify_speakers method" in error_message

    def test_test_service_malformed_response(self, tmp_path: Path) -> None:
        """Test handling of malformed responses from test service."""
        mock_service = Mock()
        mock_service.identify_speakers = Mock(return_value={
            "segments": [
                {"speaker": "SPEAKER_00", "text": "Missing timing"},  # Missing start/end
                {"start": 1.0, "end": 2.0, "speaker": "SPEAKER_01", "text": "Valid"}
            ]
        })

        service = SpeakerIdentificationService(diarization_service=mock_service)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        with pytest.raises(Exception) as exc_info:
            asyncio.run(service.identify_speakers(str(audio_file)))

        assert "missing timing information" in str(exc_info.value).lower()

    def test_test_service_exception_propagation(self, tmp_path: Path) -> None:
        """Test that test service exceptions are properly propagated."""
        mock_service = Mock()
        mock_service.identify_speakers = Mock(side_effect=RuntimeError("Service crashed"))

        service = SpeakerIdentificationService(diarization_service=mock_service)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        with pytest.raises(Exception) as exc_info:
            asyncio.run(service.identify_speakers(str(audio_file)))

        assert "test diarization service failed" in str(exc_info.value).lower()
        assert "service crashed" in str(exc_info.value).lower()

    def test_audio_format_validation_case_insensitive(self, tmp_path: Path) -> None:
        """Test that audio format validation is case insensitive."""
        service = SpeakerIdentificationService()

        # Test various cases
        for ext in ['.WAV', '.Mp3', '.AAC', '.M4A', '.FLAC', '.OGG']:
            audio_file = tmp_path / f"test{ext}"
            audio_file.write_bytes(b"fake audio data")

            # Should not raise exception for valid extensions regardless of case
            result = asyncio.run(service.identify_speakers(str(audio_file), enable_diarization=False))
            assert result["diarization_enabled"] is False

    def test_audio_format_validation_invalid_extensions(self, tmp_path: Path) -> None:
        """Test rejection of various invalid file extensions."""
        service = SpeakerIdentificationService()

        invalid_extensions = ['.txt', '.pdf', '.doc', '.exe', '.zip', '.json']

        for ext in invalid_extensions:
            audio_file = tmp_path / f"invalid{ext}"
            audio_file.write_bytes(b"fake data")

            with pytest.raises(ValueError) as exc_info:
                asyncio.run(service.identify_speakers(str(audio_file)))

            assert "invalid audio format" in str(exc_info.value).lower()

    def test_speaker_count_calculation(self, tmp_path: Path) -> None:
        """Test automatic speaker count calculation when missing from response."""
        mock_service = Mock()
        mock_service.identify_speakers = Mock(return_value={
            "speakers": ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
            "segments": [
                {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00", "text": "First"},
                {"start": 2.5, "end": 4.0, "speaker": "SPEAKER_01", "text": "Second"}
            ]
            # Note: speaker_count is missing, should be calculated
        })

        service = SpeakerIdentificationService(diarization_service=mock_service)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        result = asyncio.run(service.identify_speakers(str(audio_file)))

        # Speaker count should be calculated from speakers list
        assert result["speaker_count"] == 3

    def test_empty_response_handling(self, tmp_path: Path) -> None:
        """Test handling of empty responses from test service."""
        mock_service = Mock()
        mock_service.identify_speakers = Mock(return_value={})

        service = SpeakerIdentificationService(diarization_service=mock_service)

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        result = asyncio.run(service.identify_speakers(str(audio_file)))

        # Should handle empty response gracefully
        assert result["diarization_enabled"] is True
        assert result["speakers"] == []
        assert result["segments"] == []
        assert result["speaker_count"] == 0

    @patch('src.services.speaker_service.logger')
    def test_pipeline_loading_logging(self, mock_logger: Mock) -> None:
        """Test that pipeline loading events are properly logged."""
        async def run_test():
            service = SpeakerIdentificationService()

            with patch('pyannote.audio.Pipeline') as mock_pipeline_class, \
                 patch('torch.cuda.is_available', return_value=True), \
                 patch('torch.device') as mock_device:

                mock_pipeline = Mock()
                mock_pipeline_class.from_pretrained.return_value = mock_pipeline

                await service._load_pipeline()

                # Verify logging occurred
                mock_logger.info.assert_called_with("Pyannote pipeline loaded on cuda")

        asyncio.run(run_test())

    @patch('src.services.speaker_service.logger')
    def test_pipeline_loading_error_logging(self, mock_logger: Mock) -> None:
        """Test that pipeline loading errors are properly logged."""
        async def run_test():
            service = SpeakerIdentificationService()

            with patch('pyannote.audio.Pipeline') as mock_pipeline_class:
                mock_pipeline_class.from_pretrained.side_effect = Exception("Model download failed")

                with pytest.raises(Exception):
                    await service._load_pipeline()

                # Verify error logging occurred
                mock_logger.error.assert_called_once()
                assert "failed to load pyannote pipeline" in mock_logger.error.call_args[0][0].lower()

        asyncio.run(run_test())

    @patch('src.services.speaker_service.logger')
    def test_real_diarization_success_logging(self, mock_logger: Mock, tmp_path: Path) -> None:
        """Test that successful real diarization is logged."""
        service = SpeakerIdentificationService()

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        mock_turn = Mock()
        mock_turn.start = 0.0
        mock_turn.end = 2.0

        with patch('pyannote.audio.Pipeline') as mock_pipeline_class, \
             patch('torch.cuda.is_available', return_value=False), \
             patch('whisperx.load_audio', return_value=[0.1, 0.2, 0.3]), \
             patch('soundfile.write'), \
             patch('pathlib.Path.unlink'):

            mock_pipeline = Mock()
            mock_pipeline_class.from_pretrained.return_value = mock_pipeline

            mock_diarization = Mock()
            mock_diarization.itertracks.return_value = [(mock_turn, None, "SPEAKER_00")]
            mock_pipeline.return_value = mock_diarization

            result = asyncio.run(service.identify_speakers(str(audio_file)))

            # Verify success logging
            success_calls = [call for call in mock_logger.info.call_args_list
                           if "real diarization found" in str(call).lower()]
            assert len(success_calls) > 0

    @patch('src.services.speaker_service.logger')
    def test_real_diarization_error_logging(self, mock_logger: Mock, tmp_path: Path) -> None:
        """Test that real diarization errors are logged."""
        async def run_test():
            service = SpeakerIdentificationService()

            audio_file = tmp_path / "test.wav"
            audio_file.write_bytes(b"fake audio data")

            with patch('whisperx.load_audio', side_effect=Exception("Audio processing failed")):
                with pytest.raises(Exception):
                    await service._use_real_diarization(str(audio_file))

                # Verify error logging
                mock_logger.error.assert_called_once()
                assert "real speaker diarization failed" in mock_logger.error.call_args[0][0].lower()

        asyncio.run(run_test())

    def test_is_available_with_diarization_service(self) -> None:
        """Test is_available returns True when diarization service is provided."""
        mock_service = Mock()
        service = SpeakerIdentificationService(diarization_service=mock_service)
        assert service.is_available() is True

    def test_is_available_without_diarization_service(self) -> None:
        """Test is_available returns False when no diarization service provided."""
        service = SpeakerIdentificationService(diarization_service=None)
        assert service.is_available() is False