# Speaker Diarization Fix - October 2025

## Issue Summary

Speaker diarization was failing to detect speakers in transcribed audio files, returning empty speaker arrays despite the feature being enabled.

## Root Cause

WhisperX 3.4.3's `assign_word_speakers()` function has a compatibility bug with pyannote.audio 3.4.0. The function fails with a `KeyError: 'e'` when trying to assign speakers to transcription segments. This is caused by incorrect indexing of the pyannote Annotation object.

**Error trace:**
```
KeyError: 'e'
File ".../whisperx/diarize.py", line 107, in assign_word_speakers
    diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - ...
```

## Solution

Instead of using WhisperX's buggy `assign_word_speakers()`, we:

1. **Use pyannote.audio directly** for speaker diarization
2. **Convert pyannote Annotation** to a list of speaker segments manually
3. **Use the existing `_assign_speakers_to_segments()` method** to map speakers to transcription segments based on timing overlap

This approach:
- Maintains compatibility with WhisperX 3.4.3 and pyannote.audio 3.4.0
- Avoids the bug in WhisperX's integration layer
- Uses proven speaker assignment logic already in the codebase

## Changes Made

### 1. WhisperX Service (`src/services/whisperx_service.py`)

**Before:**
```python
result = await asyncio.to_thread(
    whisperx.assign_word_speakers,
    diarization_result,
    result
)
```

**After:**
```python
# Convert pyannote annotation to speaker segments
speaker_segments = []
for turn, _, speaker in diarization_result.itertracks(yield_label=True):
    speaker_segments.append({
        "start": turn.start,
        "end": turn.end,
        "speaker": speaker
    })

# Assign speakers using existing overlap-based method
result = self._assign_speakers_to_segments(
    result.get("segments", []),
    speaker_segments
)
```

### 2. Main Application (`src/main_simple.py`)

Added cuDNN library path configuration to prevent segmentation faults:
```python
# Fix cuDNN library path for pyannote.audio speaker diarization
cudnn_path = Path(sys.prefix) / "lib" / "python3.12" / "site-packages" / "nvidia" / "cudnn" / "lib"
if cudnn_path.exists():
    current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if str(cudnn_path) not in current_ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{cudnn_path}:{current_ld_path}"
```

### 3. Improved Error Logging

Changed from generic warnings to detailed error logging with full tracebacks:
```python
except Exception as e:
    logger.error(f"Speaker diarization failed: {type(e).__name__}: {str(e)}", exc_info=True)
```

## Testing Results

**Test File:** `large_audio_converted.wav` (1-hour meeting recording)

**Before Fix:**
- Speakers detected: 0
- Speaker array: `[]`

**After Fix:**
- Speakers detected: 5
- Speaker array: `["SPEAKER_00", "SPEAKER_01", "SPEAKER_02", "SPEAKER_03", "SPEAKER_04"]`
- Segments with speaker assignments: 100% of transcribed segments

## Version Compatibility

**Critical:** These versions must remain fixed together:
- WhisperX: 3.4.3
- pyannote.audio: 3.4.0
- torch: 2.5.1+
- torchaudio: 2.5.1+

**Do not downgrade WhisperX** - the fix works with the current version by avoiding the buggy function.

## Environment Requirements

1. **HuggingFace Token**: Required in `.env` file for speaker diarization model access
   ```
   HF_TOKEN=your_token_here
   ```

2. **cuDNN Libraries**: Must be accessible in `LD_LIBRARY_PATH` (handled automatically by code)

3. **GPU**: CUDA-enabled GPU recommended for performance (works on CPU but slower)

## Future Considerations

- Monitor WhisperX releases for fixes to `assign_word_speakers()`
- Consider contributing the fix upstream to WhisperX project
- Current implementation is stable and production-ready

## Related Files

- `/src/services/whisperx_service.py` - Core diarization logic
- `/src/main_simple.py` - cuDNN library path fix
- `/src/api/endpoints/transcription_simple.py` - REST API endpoint
- `/src/api/endpoints/transcription_sse.py` - SSE streaming endpoint
- `/start_server.sh` - Server startup script with environment setup
