# Quickstart Guide: TranscribeMS MCP Server

**Date**: 2025-09-25
**Feature**: Convert TranscribeMS API to MCP Server
**Branch**: 002-adjust-the-current

This guide provides step-by-step integration scenarios for using TranscribeMS as an MCP server with Claude Code.

## Prerequisites

### System Requirements
- Python 3.11 or higher
- 4GB+ RAM (8GB+ recommended for large files)
- Claude Code installed and running
- Audio files in supported formats: MP3, WAV, M4A, OGG, FLAC, AAC, WMA

### Installation Steps

1. **Install TranscribeMS MCP Server**
   ```bash
   pip install transcribems-mcp
   ```

2. **Configure Claude Code MCP Integration**
   ```bash
   # Add MCP server to Claude Code configuration
   claude mcp add transcribems transcribems-mcp serve
   ```

3. **Verify Installation**
   ```bash
   # Check MCP server status
   claude mcp status transcribems
   ```

## Integration Scenarios

### Scenario 1: Single Audio File Transcription

**User Story**: As a developer, I want to transcribe a meeting recording while working in Claude Code to extract action items and notes.

**Test Steps**:
1. Place an audio file in your workspace: `meeting_2025_01_24.mp3`
2. In Claude Code, request transcription:
   ```
   Please transcribe the audio file meeting_2025_01_24.mp3 in my workspace
   ```
3. Claude Code calls the MCP tool and processes the request
4. Receive transcription with speaker identification and timestamps

**Expected Result**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "text": "Speaker 1: Good morning everyone, let's start with...",
    "confidence_score": 0.92,
    "language": "en",
    "processing_time": 45.2,
    "segments": [
      {
        "start_time": 0.0,
        "end_time": 3.5,
        "text": "Good morning everyone, let's start with",
        "confidence": 0.94,
        "speaker_id": "SPEAKER_00"
      }
    ],
    "speakers": [
      {
        "speaker_id": "SPEAKER_00",
        "total_speech_time": 120.5,
        "segment_count": 15,
        "confidence": 0.89
      }
    ]
  }
}
```

**Validation**:
- [ ] Audio file is recognized and processed
- [ ] Transcription contains accurate text
- [ ] Speaker diarization identifies multiple speakers
- [ ] Word-level timestamps are present
- [ ] Confidence scores are within expected range (0.8-1.0)

### Scenario 2: Large File with Progress Tracking

**User Story**: As a researcher, I want to transcribe a 1-hour interview with progress updates so I can monitor the processing status.

**Test Steps**:
1. Place a large audio file (>5 minutes): `interview_long.wav`
2. In Claude Code, request transcription:
   ```
   Transcribe interview_long.wav and show me progress updates
   ```
3. Claude Code initiates transcription and polls for progress
4. Receive periodic progress updates during processing

**Expected Progress Flow**:
```json
// Initial response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "processing",
  "progress": 0.1
}

// Progress update
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "processing",
  "progress": 0.45,
  "current_chunk": 9,
  "total_chunks": 20,
  "estimated_remaining": 180
}

// Completion
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "result": { /* full transcription result */ }
}
```

**Validation**:
- [ ] Progress updates are provided for files >5 minutes
- [ ] Progress percentage increases monotonically
- [ ] Estimated remaining time decreases appropriately
- [ ] Final result includes complete transcription with all metadata

### Scenario 3: Batch Processing Multiple Files

**User Story**: As a content creator, I want to transcribe multiple podcast episodes simultaneously to generate show notes efficiently.

**Test Steps**:
1. Place multiple audio files in workspace:
   - `episode_01.mp3`
   - `episode_02.mp3`
   - `episode_03.m4a`
2. In Claude Code, request batch transcription:
   ```
   Please transcribe all three episode files in my workspace using batch processing
   ```
3. Claude Code initiates batch transcription
4. Monitor progress of all jobs simultaneously

**Expected Batch Response**:
```json
{
  "batch_id": "batch-550e8400-e29b-41d4-a716-446655440002",
  "jobs": [
    {
      "job_id": "job-1",
      "file_path": "episode_01.mp3",
      "status": "processing"
    },
    {
      "job_id": "job-2",
      "file_path": "episode_02.mp3",
      "status": "pending"
    },
    {
      "job_id": "job-3",
      "file_path": "episode_03.m4a",
      "status": "processing"
    }
  ],
  "total_jobs": 3
}
```

**Validation**:
- [ ] All files are accepted and queued for processing
- [ ] Jobs process in parallel (multiple "processing" status)
- [ ] Each job produces individual transcription results
- [ ] Batch operation completes when all jobs finish

### Scenario 4: Error Handling and Recovery

**User Story**: As a user, I want clear error messages and guidance when transcription fails so I can resolve issues quickly.

**Test Steps**:
1. Attempt to transcribe a non-existent file:
   ```
   Transcribe nonexistent.mp3
   ```
2. Attempt to transcribe a file that's too large (>1GB)
3. Attempt to transcribe an unsupported format (.txt file)

**Expected Error Responses**:

**File Not Found**:
```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "The specified audio file does not exist or is not accessible",
    "details": {
      "error_type": "validation_error",
      "user_action": "Verify the file path exists and Claude Code has read permissions"
    }
  }
}
```

**File Too Large**:
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Audio file exceeds maximum size limit of 1GB",
    "details": {
      "error_type": "validation_error",
      "max_size_bytes": 1073741824,
      "user_action": "Split the audio file into smaller chunks or compress the file"
    }
  }
}
```

**Validation**:
- [ ] Clear error codes and messages for each error type
- [ ] Actionable user guidance provided
- [ ] Errors don't crash the MCP server
- [ ] Subsequent valid requests work after errors

### Scenario 5: Transcription History and Retrieval

**User Story**: As a frequent user, I want to access my previous transcriptions without re-processing files to save time and maintain a record.

**Test Steps**:
1. Complete several transcriptions (from previous scenarios)
2. In Claude Code, request transcription history:
   ```
   Show me my recent transcription history
   ```
3. Select and retrieve a specific previous result:
   ```
   Get the full result for job [job_id]
   ```

**Expected History Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_path": "meeting_2025_01_24.mp3",
      "status": "completed",
      "started_at": "2025-01-24T10:00:00Z",
      "completed_at": "2025-01-24T10:02:15Z",
      "duration": 1380.5,
      "word_count": 2156
    }
  ],
  "total_count": 15
}
```

**Validation**:
- [ ] History shows completed, failed, and processing jobs
- [ ] Results can be retrieved by job ID
- [ ] Timestamps and metadata are preserved
- [ ] History persists across MCP server restarts

## Performance Expectations

### Processing Times
- **Small files** (<5 min): 30-60 seconds
- **Medium files** (5-30 min): 2-8 minutes
- **Large files** (30-60 min): 10-25 minutes
- **Maximum file** (1GB): Up to 45 minutes

### Resource Usage
- **Memory**: 2-6GB during processing (model dependent)
- **CPU**: High utilization during transcription
- **Disk**: ~500MB for models, temporary files during processing
- **Network**: None (local processing only)

### Quality Metrics
- **Accuracy**: 85-95% for clear audio
- **Speaker ID**: 80-90% accuracy with distinct voices
- **Confidence**: Average 0.8-0.95 for good audio quality
- **Language Detection**: 95%+ accuracy for supported languages

## Troubleshooting

### Common Issues

**Model Download Fails**:
- Check internet connection
- Ensure sufficient disk space (2GB+)
- Verify write permissions in model cache directory

**Out of Memory Error**:
- Use smaller model size (`tiny` or `base`)
- Reduce chunk length to 15-20 seconds
- Close other memory-intensive applications

**Slow Processing**:
- Enable GPU acceleration if available (CUDA/MPS)
- Use larger chunk sizes for long files
- Ensure SSD storage for temporary files

**Poor Transcription Quality**:
- Check audio quality (clear speech, minimal background noise)
- Try different model sizes (`medium` or `large`)
- Ensure correct language detection/specification

### Support Commands

Check MCP server logs:
```bash
claude mcp logs transcribems
```

Restart MCP server:
```bash
claude mcp restart transcribems
```

Update to latest version:
```bash
pip install --upgrade transcribems-mcp
claude mcp restart transcribems
```

## Next Steps

After validating these integration scenarios:

1. **Performance Testing**: Test with various file sizes and formats
2. **Load Testing**: Multiple concurrent transcription jobs
3. **Edge Case Testing**: Corrupted files, network interruptions, disk full scenarios
4. **User Experience**: Gather feedback on Claude Code integration workflow
5. **Documentation**: Create user-facing documentation and examples

This quickstart guide serves as the acceptance criteria for the TranscribeMS MCP server implementation.