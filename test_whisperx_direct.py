#!/usr/bin/env python3
"""Direct WhisperX test to see if transcription works at all."""
import whisperx
from whisperx import load_audio
import torch

print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())

# Load audio
audio_file = "transcribe_mcp_env/lib/python3.12/site-packages/pyannote/audio/sample/sample.wav"
print(f"\nLoading audio from {audio_file}...")
audio = load_audio(audio_file)
print(f"Audio loaded: {len(audio)} samples")

# Load model
print("\nLoading WhisperX model...")
model = whisperx.load_model("base", device="cuda", compute_type="float16")
print("Model loaded successfully")

# Transcribe
print("\nStarting transcription...")
try:
    result = model.transcribe(audio, batch_size=16)
    print("\n✅ Transcription completed!")
    print(f"Language: {result.get('language')}")
    print(f"Segments: {len(result.get('segments', []))}")
    if result.get('segments'):
        print(f"First segment: {result['segments'][0].get('text')}")
except Exception as e:
    print(f"\n❌ Transcription failed: {e}")
    import traceback
    traceback.print_exc()
