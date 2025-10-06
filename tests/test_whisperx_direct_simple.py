"""
Ultra-simple WhisperX test - direct call without async wrappers.
"""
import os
import sys
from pathlib import Path

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")
os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("ULTRA-SIMPLE WHISPERX TEST")
print("=" * 80)

# Import WhisperX
print("\n1. Importing WhisperX...")
import whisperx

# Load audio
print("\n2. Loading audio file...")
audio_file = "/home/karlsoro/Projects/TranscribeMS/test_data/large_audio_converted.wav"
audio = whisperx.load_audio(audio_file)
print(f"   Audio loaded: {len(audio)} samples, {len(audio)/16000:.1f} seconds")

# Load model
print("\n3. Loading WhisperX model...")
device = "cuda"
compute_type = "float16"
model = whisperx.load_model("large-v2", device, compute_type=compute_type)
print(f"   Model loaded on {device} with {compute_type}")

# Transcribe
print("\n4. Transcribing (this may take several minutes)...")
print("   Calling model.transcribe()...")
sys.stdout.flush()

try:
    result = model.transcribe(audio, batch_size=16, language="en")
    print(f"\n5. SUCCESS! Transcription completed")
    print(f"   Segments: {len(result.get('segments', []))}")
    print(f"   Language: {result.get('language', 'unknown')}")
    if 'text' in result:
        print(f"   Text preview: {result['text'][:200]}")
except Exception as e:
    print(f"\n5. FAILED: {e}")
    import traceback
    traceback.print_exc()
