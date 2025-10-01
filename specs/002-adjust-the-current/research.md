# Research: MCP Server Implementation for TranscribeMCP

**Date**: 2025-09-25
**Feature**: Convert TranscribeMCP API to MCP Server
**Branch**: 002-adjust-the-current

## Technology Decisions

### Model Context Protocol (MCP) Implementation

**Decision**: Use Python MCP SDK with asyncio-based server implementation
**Rationale**:
- MCP SDK provides official support for tool definitions and server lifecycle
- Asyncio enables concurrent transcription processing without blocking tool responses
- Python ecosystem has mature audio processing libraries (WhisperX, torchaudio)
- Cross-platform compatibility matches Claude Code's deployment targets

**Alternatives considered**:
- TypeScript MCP implementation: Rejected due to limited audio processing libraries
- Rust MCP implementation: Rejected due to complexity of WhisperX Python bindings
- Go MCP implementation: Rejected due to lack of mature transcription libraries

### Transcription Backend Integration

**Decision**: WhisperX with local processing and speaker diarization
**Rationale**:
- WhisperX provides speaker diarization capability beyond base Whisper
- Local processing ensures privacy and eliminates API dependencies
- Supports all required audio formats (MP3, WAV, M4A, OGG, FLAC, AAC, WMA)
- Provides word-level timestamps and confidence scores
- Can handle large files (up to 1GB) with streaming processing

**Alternatives considered**:
- OpenAI Whisper API: Rejected due to cloud dependency and privacy concerns
- Azure Speech Services: Rejected due to cost and API dependency
- Google Cloud Speech-to-Text: Rejected due to cloud requirement
- Base Whisper: Rejected due to lack of speaker diarization

### File Processing Strategy

**Decision**: Chunked processing with progress reporting for files >5 minutes
**Rationale**:
- Large files (up to 1GB) require chunked processing to avoid memory issues
- Progress updates enhance user experience for long transcriptions
- Allows for cancellation and recovery of long-running operations
- Maintains responsiveness of MCP tool interface

**Alternatives considered**:
- Full file processing: Rejected due to memory constraints on large files
- Streaming transcription: Rejected due to WhisperX architecture limitations
- Background queue processing: Rejected to maintain simplicity

### Storage and Caching

**Decision**: File-based transcription history with JSON metadata
**Rationale**:
- Simple implementation without database dependencies
- Easy to backup and transfer between systems
- Supports quick retrieval of previous transcription results
- Minimal overhead for single-user MCP server deployment

**Alternatives considered**:
- SQLite database: Rejected due to added complexity for single-user scenario
- In-memory only: Rejected due to loss of transcription history
- Cloud storage: Rejected due to privacy and offline requirements

### Audio Format Support

**Decision**: Use librosa/torchaudio for format conversion with ffmpeg fallback
**Rationale**:
- librosa handles most common formats natively (MP3, WAV, M4A, FLAC)
- torchaudio provides additional format support
- ffmpeg fallback ensures compatibility with all specified formats
- Automatic format detection reduces user configuration

**Alternatives considered**:
- ffmpeg only: Rejected due to external dependency management complexity
- pydub: Rejected due to limited format support compared to librosa
- Native format libraries: Rejected due to multiple dependencies

### MCP Tool Design

**Decision**: Separate tools for transcribe, progress, history, and batch operations
**Rationale**:
- Clear separation of concerns for different user workflows
- Enables parallel processing of multiple operations
- Follows MCP best practices for tool granularity
- Supports both single file and batch transcription scenarios

**Alternatives considered**:
- Single transcribe tool with modes: Rejected due to complexity
- File system integration: Rejected due to Claude Code integration patterns
- Streaming tools: Rejected due to MCP protocol limitations

## Implementation Patterns

### Error Handling Strategy
- MCP error responses with structured error codes
- Graceful degradation for unsupported formats
- User-friendly error messages with actionable suggestions
- Logging for debugging without exposing sensitive paths

### Performance Optimization
- Lazy loading of WhisperX models
- Model caching between transcription requests
- Chunked processing with configurable chunk sizes
- Memory management for large audio files

### Testing Strategy
- MCP protocol compliance tests
- Audio processing unit tests with sample files
- Integration tests with Claude Code MCP client
- Performance benchmarks for large file processing

## Dependencies and Requirements

### Core Dependencies
- `mcp>=1.0.0` - Model Context Protocol SDK
- `whisperx>=3.1.0` - Transcription with speaker diarization
- `librosa>=0.10.0` - Audio processing and format support
- `torch>=2.0.0` - Required by WhisperX
- `transformers>=4.30.0` - Transformer models for transcription
- `pydantic>=2.0.0` - Data validation and serialization

### System Requirements
- Python 3.11+ (required for async improvements)
- CUDA support recommended for GPU acceleration
- 4GB+ RAM for large audio file processing
- Cross-platform: Windows, macOS, Linux

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking

## Architecture Decisions

### Server Architecture
- Single-process MCP server with async request handling
- Concurrent transcription processing using asyncio tasks
- Thread-safe model management with locks
- Graceful shutdown with cleanup of temporary files

### Integration Points
- MCP server discovery via Claude Code configuration
- File path resolution between Claude Code workspace and server
- Progress reporting through MCP tool responses
- Error propagation with structured error responses

### Security Considerations
- Input validation for file paths and parameters
- File size limits (1GB maximum) to prevent resource exhaustion
- Temporary file cleanup to prevent disk space issues
- No external network requests (local processing only)