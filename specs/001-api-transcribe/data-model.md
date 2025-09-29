# Data Model: WhisperX Audio Transcription API

**Feature**: WhisperX Audio Transcription API
**Date**: 2025-01-24

## Core Entities

### AudioFile
**Purpose**: Represents input audio files submitted for transcription
**Attributes**:
- `file_path: string` - Absolute path to the uploaded audio file
- `original_name: string` - Original filename as uploaded by user
- `file_size: integer` - File size in bytes (max 5GB)
- `format: AudioFormat` - Detected audio format (WAV, MP3, M4A, FLAC)
- `duration_seconds: float` - Audio duration extracted from metadata
- `sample_rate: integer` - Audio sample rate (e.g., 44100, 16000)
- `channels: integer` - Number of audio channels (1=mono, 2=stereo)
- `created_at: datetime` - Upload timestamp
- `status: FileStatus` - Processing status (uploaded, validated, failed)

**Validation Rules**:
- File size must not exceed 5,368,709,120 bytes (5GB)
- Format must be one of: WAV, MP3, M4A, FLAC
- Duration must be greater than 0.1 seconds
- Sample rate must be between 8000 and 192000 Hz

### TranscriptionJob
**Purpose**: Represents a transcription processing request and its lifecycle
**Attributes**:
- `job_id: uuid` - Unique identifier for the transcription job
- `audio_file_id: uuid` - Reference to associated AudioFile
- `status: JobStatus` - Current job status
- `priority: JobPriority` - Processing priority (low, normal, high)
- `configuration: TranscriptionConfig` - Processing configuration settings
- `created_at: datetime` - Job creation timestamp
- `started_at: datetime?` - Processing start timestamp
- `completed_at: datetime?` - Processing completion timestamp
- `progress_percentage: integer` - Processing progress (0-100)
- `error_message: string?` - Error details if processing failed
- `result_file_path: string?` - Path to generated transcription JSON file

**State Transitions**:
```
queued → processing → completed
queued → processing → failed
queued → cancelled
processing → cancelled (if explicitly cancelled)
```

### Transcription
**Purpose**: Contains the final transcription output with speaker identification
**Attributes**:
- `transcription_id: uuid` - Unique identifier
- `job_id: uuid` - Reference to originating TranscriptionJob
- `language: string` - Detected or specified language code (e.g., "en", "es")
- `confidence_score: float` - Overall transcription confidence (0.0-1.0)
- `speakers_detected: integer` - Number of unique speakers identified
- `total_segments: integer` - Number of speech segments
- `processing_time_seconds: float` - Total processing time
- `model_used: string` - WhisperX model used (base, large-v2, large-v3)
- `created_at: datetime` - Transcription creation timestamp

### Speaker
**Purpose**: Represents an identified speaker in the audio
**Attributes**:
- `speaker_id: string` - Sequential speaker identifier ("Speaker 1", "Speaker 2", etc.)
- `transcription_id: uuid` - Reference to parent Transcription
- `total_speech_duration: float` - Total seconds of speech attributed to speaker
- `segment_count: integer` - Number of segments attributed to speaker
- `confidence_score: float` - Speaker identification confidence (0.0-1.0)
- `voice_characteristics: json?` - Optional voice analysis metadata

### SpeechSegment
**Purpose**: Individual portion of transcribed speech with timing and speaker attribution
**Attributes**:
- `segment_id: uuid` - Unique identifier
- `transcription_id: uuid` - Reference to parent Transcription
- `speaker_id: string` - Speaker attribution ("Speaker 1", "Speaker 2", etc.)
- `start_time_seconds: float` - Segment start time with millisecond precision
- `end_time_seconds: float` - Segment end time with millisecond precision
- `text: string` - Transcribed text content
- `confidence_score: float` - Segment-level confidence (0.0-1.0)
- `word_count: integer` - Number of words in segment
- `sequence_number: integer` - Sequential order in transcription

**Validation Rules**:
- `end_time_seconds` must be greater than `start_time_seconds`
- `text` must not be empty or whitespace-only
- `confidence_score` must be between 0.0 and 1.0
- `sequence_number` must be unique within transcription

### ProcessingLog
**Purpose**: Audit trail and debugging information for transcription processing
**Attributes**:
- `log_id: uuid` - Unique identifier
- `job_id: uuid` - Reference to TranscriptionJob
- `level: LogLevel` - Log level (DEBUG, INFO, WARN, ERROR)
- `message: string` - Log message content
- `component: string` - System component that generated log (api, worker, whisperx)
- `timestamp: datetime` - Log entry timestamp
- `metadata: json?` - Additional structured data (error details, performance metrics)

## Enumerations

### AudioFormat
```python
enum AudioFormat:
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
```

### FileStatus
```python
enum FileStatus:
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    FAILED = "failed"
```

### JobStatus
```python
enum JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### JobPriority
```python
enum JobPriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
```

### LogLevel
```python
enum LogLevel:
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
```

## Complex Data Types

### TranscriptionConfig
**Purpose**: Configuration parameters for transcription processing
**Attributes**:
- `model_size: string` - WhisperX model ("base", "large-v2", "large-v3")
- `language: string?` - Target language code (auto-detect if null)
- `enable_diarization: boolean` - Enable speaker identification
- `min_speakers: integer?` - Minimum expected speakers (1-10)
- `max_speakers: integer?` - Maximum expected speakers (1-10)
- `enable_vad: boolean` - Enable Voice Activity Detection filtering
- `batch_size: integer` - Processing batch size (auto-calculated if 0)
- `temperature: float` - Sampling temperature (0.0-1.0)
- `debug_mode: boolean` - Enable verbose logging

**Default Values**:
```json
{
    "model_size": "large-v2",
    "language": null,
    "enable_diarization": true,
    "min_speakers": null,
    "max_speakers": null,
    "enable_vad": true,
    "batch_size": 0,
    "temperature": 0.0,
    "debug_mode": false
}
```

## Relationships

### Primary Relationships
- `AudioFile` ← 1:1 → `TranscriptionJob`
- `TranscriptionJob` ← 1:1 → `Transcription`
- `Transcription` ← 1:N → `Speaker`
- `Transcription` ← 1:N → `SpeechSegment`
- `TranscriptionJob` ← 1:N → `ProcessingLog`

### Foreign Key Constraints
- `TranscriptionJob.audio_file_id` → `AudioFile.file_id`
- `Transcription.job_id` → `TranscriptionJob.job_id`
- `Speaker.transcription_id` → `Transcription.transcription_id`
- `SpeechSegment.transcription_id` → `Transcription.transcription_id`
- `ProcessingLog.job_id` → `TranscriptionJob.job_id`

## JSON Output Schema

### Transcription Response Format
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "metadata": {
        "audio_duration_seconds": 1800.5,
        "processing_time_seconds": 45.2,
        "language": "en",
        "model_used": "large-v2",
        "speakers_detected": 3
    },
    "speakers": [
        {
            "speaker_id": "Speaker 1",
            "total_speech_duration": 720.3,
            "segment_count": 45
        },
        {
            "speaker_id": "Speaker 2",
            "total_speech_duration": 650.8,
            "segment_count": 38
        }
    ],
    "segments": [
        {
            "start_time": 0.0,
            "end_time": 3.2,
            "speaker": "Speaker 1",
            "text": "Welcome everyone to today's meeting.",
            "confidence": 0.95
        },
        {
            "start_time": 3.5,
            "end_time": 7.1,
            "speaker": "Speaker 2",
            "text": "Thank you for having me.",
            "confidence": 0.92
        }
    ]
}
```

## Storage Considerations

### File Storage
- **Audio Files**: Stored in `/uploads/{date}/{job_id}/` with original extension
- **Transcription Files**: Stored in `./transcriptions/{date}/{job_id}.json`
- **Temporary Files**: Auto-cleaned after 24 hours
- **Backup Strategy**: Daily incremental backups of transcription outputs

### Database Considerations
- **Indexing**: Create indexes on `job_id`, `status`, `created_at` for query performance
- **Partitioning**: Consider date-based partitioning for large-scale deployments
- **Retention**: Archive completed jobs older than 90 days
- **Constraints**: Implement check constraints for enum values and ranges