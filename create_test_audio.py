#!/usr/bin/env python3
"""Create test audio files for TranscribeMS integration testing.

This script generates synthetic audio files with known content
for testing the transcription system end-to-end.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_sine_wave_audio(frequency: float, duration: float, sample_rate: int = 16000) -> np.ndarray:
    """Generate a sine wave audio signal."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t) * 0.3  # Low amplitude
    return audio.astype(np.float32)

def generate_speech_like_audio(duration: float, sample_rate: int = 16000) -> np.ndarray:
    """Generate speech-like audio using multiple frequency components."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Base frequencies typical for human speech
    f1 = 100 + 50 * np.sin(2 * np.pi * 0.5 * t)  # Fundamental frequency variation
    f2 = 800 + 200 * np.sin(2 * np.pi * 0.3 * t)  # First formant
    f3 = 2400 + 400 * np.sin(2 * np.pi * 0.1 * t)  # Second formant

    # Generate speech-like signal
    signal = (np.sin(2 * np.pi * f1 * t) * 0.3 +
              np.sin(2 * np.pi * f2 * t) * 0.2 +
              np.sin(2 * np.pi * f3 * t) * 0.1)

    # Add some noise for realism
    noise = np.random.normal(0, 0.05, len(signal))
    signal = signal + noise

    # Apply envelope to create speech-like segments
    envelope = np.ones_like(signal)
    segment_length = int(sample_rate * 1.0)  # 1 second segments

    for i in range(0, len(signal), segment_length * 2):
        # Create pauses between "words"
        pause_start = min(i + segment_length, len(signal))
        pause_end = min(i + int(segment_length * 1.5), len(signal))
        envelope[pause_start:pause_end] *= 0.1

    return (signal * envelope).astype(np.float32)

def create_test_audio_files():
    """Create various test audio files."""
    test_dir = Path("test_audio")
    test_dir.mkdir(exist_ok=True)

    sample_rate = 16000  # WhisperX prefers 16kHz

    test_files = []

    # 1. Short speech-like audio (5 seconds)
    logger.info("Creating short speech-like audio...")
    short_audio = generate_speech_like_audio(5.0, sample_rate)
    short_file = test_dir / "short_speech.wav"
    sf.write(short_file, short_audio, sample_rate)
    test_files.append(short_file)

    # 2. Medium speech-like audio (15 seconds)
    logger.info("Creating medium speech-like audio...")
    medium_audio = generate_speech_like_audio(15.0, sample_rate)
    medium_file = test_dir / "medium_speech.wav"
    sf.write(medium_file, medium_audio, sample_rate)
    test_files.append(medium_file)

    # 3. Multi-speaker simulation (10 seconds with frequency changes)
    logger.info("Creating multi-speaker simulation...")
    duration = 10.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Speaker 1: Lower frequency (first 5 seconds)
    speaker1 = generate_speech_like_audio(5.0, sample_rate)
    # Speaker 2: Higher frequency (next 5 seconds)
    speaker2_audio = generate_speech_like_audio(5.0, sample_rate)
    speaker2 = speaker2_audio * 1.2  # Slightly different amplitude

    multi_speaker = np.concatenate([speaker1, speaker2])
    multi_file = test_dir / "multi_speaker.wav"
    sf.write(multi_file, multi_speaker, sample_rate)
    test_files.append(multi_file)

    # 4. Quiet audio for testing low volume
    logger.info("Creating quiet audio...")
    quiet_audio = generate_speech_like_audio(8.0, sample_rate) * 0.1  # Very quiet
    quiet_file = test_dir / "quiet_speech.wav"
    sf.write(quiet_file, quiet_audio, sample_rate)
    test_files.append(quiet_file)

    # 5. High quality audio (44.1kHz)
    logger.info("Creating high quality audio...")
    hq_sample_rate = 44100
    hq_audio = generate_speech_like_audio(6.0, hq_sample_rate)
    hq_file = test_dir / "high_quality_speech.wav"
    sf.write(hq_file, hq_audio, hq_sample_rate)
    test_files.append(hq_file)

    # Create metadata file
    metadata = {
        "test_files": [],
        "created_by": "TranscribeMS test audio generator",
        "sample_rate": sample_rate,
        "format": "WAV",
        "notes": "Synthetic audio files for testing transcription system"
    }

    for test_file in test_files:
        file_info = {
            "filename": test_file.name,
            "path": str(test_file),
            "duration": sf.info(test_file).duration,
            "samplerate": sf.info(test_file).samplerate,
            "channels": sf.info(test_file).channels,
            "size_bytes": test_file.stat().st_size
        }
        metadata["test_files"].append(file_info)

    # Save metadata
    import json
    metadata_file = test_dir / "test_audio_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Created {len(test_files)} test audio files in {test_dir}/")
    logger.info("Test audio files:")
    for file_info in metadata["test_files"]:
        logger.info(f"  - {file_info['filename']}: {file_info['duration']:.1f}s, "
                   f"{file_info['samplerate']}Hz, {file_info['size_bytes']} bytes")

    return test_files, metadata

if __name__ == "__main__":
    try:
        test_files, metadata = create_test_audio_files()
        print(f"✅ Successfully created {len(test_files)} test audio files")
        print("📁 Files available for testing:")
        for file_info in metadata["test_files"]:
            print(f"  - {file_info['filename']}")

    except Exception as e:
        print(f"❌ Failed to create test audio files: {e}")
        raise