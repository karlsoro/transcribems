# Tasks: Convert TranscribeMS API to MCP Server

**Input**: Design documents from `/specs/002-adjust-the-current/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Create project structure with src/, tests/ directories and MCP server package layout
- [ ] T002 Initialize Python project with pyproject.toml, MCP SDK, WhisperX, asyncio, pydantic dependencies
- [ ] T003 [P] Configure black, mypy, and pytest tools in pyproject.toml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] MCP tool contract test for transcribe_audio in tests/contract/test_transcribe_audio_tool.py
- [ ] T005 [P] MCP tool contract test for get_transcription_progress in tests/contract/test_progress_tool.py
- [ ] T006 [P] MCP tool contract test for list_transcription_history in tests/contract/test_history_tool.py
- [ ] T007 [P] MCP tool contract test for get_transcription_result in tests/contract/test_result_tool.py
- [ ] T008 [P] MCP tool contract test for batch_transcribe in tests/contract/test_batch_tool.py
- [ ] T009 [P] MCP tool contract test for cancel_transcription in tests/contract/test_cancel_tool.py
- [ ] T010 [P] MCP error response contract test in tests/contract/test_error_responses.py
- [ ] T011 [P] Integration test single audio file transcription scenario in tests/integration/test_single_file.py
- [ ] T012 [P] Integration test large file with progress tracking in tests/integration/test_large_file.py
- [ ] T013 [P] Integration test batch processing scenario in tests/integration/test_batch_processing.py
- [ ] T014 [P] Integration test error handling and recovery in tests/integration/test_error_handling.py
- [ ] T015 [P] Integration test transcription history scenario in tests/integration/test_history.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T016 [P] AudioFile model with validation and state transitions in src/models/audio_file.py
- [ ] T017 [P] TranscriptionJob model with progress tracking in src/models/transcription_job.py
- [ ] T018 [P] TranscriptionResult model with segments and speakers in src/models/transcription_result.py
- [ ] T019 [P] TranscriptionSegment model with word-level data in src/models/transcription_segment.py
- [ ] T020 [P] Word model with timing and confidence in src/models/word.py
- [ ] T021 [P] Speaker model with diarization data in src/models/speaker.py
- [ ] T022 [P] JobStatus enum and supporting types in src/models/types.py
- [ ] T023 [P] TranscriptionSettings configuration model in src/models/settings.py
- [ ] T024 [P] AudioFileService for file validation and metadata in src/services/audio_file_service.py
- [ ] T025 [P] TranscriptionService with WhisperX integration in src/services/transcription_service.py
- [ ] T026 [P] ProgressService for job progress tracking in src/services/progress_service.py
- [ ] T027 [P] StorageService for file-based persistence in src/services/storage_service.py
- [ ] T028 [P] HistoryService for transcription history management in src/services/history_service.py
- [ ] T029 transcribe_audio MCP tool implementation in src/tools/transcribe_tool.py
- [ ] T030 get_transcription_progress MCP tool in src/tools/progress_tool.py
- [ ] T031 list_transcription_history MCP tool in src/tools/history_tool.py
- [ ] T032 get_transcription_result MCP tool in src/tools/result_tool.py
- [ ] T033 batch_transcribe MCP tool in src/tools/batch_tool.py
- [ ] T034 cancel_transcription MCP tool in src/tools/cancel_tool.py
- [ ] T035 MCP server main class and tool registration in src/server.py
- [ ] T036 Error handling and structured error responses in src/error_handler.py
- [ ] T037 WhisperX model management and caching in src/whisper_manager.py

## Phase 3.4: Integration
- [ ] T038 Connect StorageService to file system with JSON serialization
- [ ] T039 Integrate WhisperX with chunked processing for large files
- [ ] T040 Progress tracking integration with asyncio tasks
- [ ] T041 MCP server startup and tool registration
- [ ] T042 File format detection and audio preprocessing pipeline
- [ ] T043 Speaker diarization integration with WhisperX
- [ ] T044 Error propagation from services to MCP tools
- [ ] T045 Concurrent job processing with resource management

## Phase 3.5: Polish
- [ ] T046 [P] Unit tests for AudioFile validation in tests/unit/test_audio_file.py
- [ ] T047 [P] Unit tests for TranscriptionJob state management in tests/unit/test_transcription_job.py
- [ ] T048 [P] Unit tests for file format detection in tests/unit/test_format_detection.py
- [ ] T049 [P] Unit tests for progress calculation in tests/unit/test_progress.py
- [ ] T050 [P] Unit tests for error handling in tests/unit/test_error_handling.py
- [ ] T051 Performance tests for 1GB file processing in tests/performance/test_large_files.py
- [ ] T052 Performance tests for MCP tool response times (<200ms) in tests/performance/test_response_times.py
- [ ] T053 [P] CLI entry point for MCP server in src/cli.py
- [ ] T054 [P] Configuration file handling and validation in src/config.py
- [ ] T055 [P] README.md with installation and usage instructions
- [ ] T056 Memory usage optimization and cleanup for large files
- [ ] T057 Comprehensive logging throughout the application
- [ ] T058 Run quickstart.md integration scenarios end-to-end

## Dependencies
- Setup (T001-T003) before everything
- Contract tests (T004-T015) before implementation (T016-T037)
- Models (T016-T023) before services (T024-T028)
- Services before tools (T029-T034)
- Server and core components (T035-T037) before integration (T038-T045)
- All implementation before polish (T046-T058)

## Parallel Example
```bash
# Launch contract tests together (T004-T015):
Task: "MCP tool contract test for transcribe_audio in tests/contract/test_transcribe_audio_tool.py"
Task: "MCP tool contract test for get_transcription_progress in tests/contract/test_progress_tool.py"
Task: "MCP tool contract test for list_transcription_history in tests/contract/test_history_tool.py"
Task: "MCP tool contract test for get_transcription_result in tests/contract/test_result_tool.py"
Task: "MCP tool contract test for batch_transcribe in tests/contract/test_batch_tool.py"
Task: "MCP tool contract test for cancel_transcription in tests/contract/test_cancel_tool.py"
Task: "MCP error response contract test in tests/contract/test_error_responses.py"
Task: "Integration test single audio file transcription scenario in tests/integration/test_single_file.py"
Task: "Integration test large file with progress tracking in tests/integration/test_large_file.py"
Task: "Integration test batch processing scenario in tests/integration/test_batch_processing.py"
Task: "Integration test error handling and recovery in tests/integration/test_error_handling.py"
Task: "Integration test transcription history scenario in tests/integration/test_history.py"

# Launch model creation together (T016-T023):
Task: "AudioFile model with validation and state transitions in src/models/audio_file.py"
Task: "TranscriptionJob model with progress tracking in src/models/transcription_job.py"
Task: "TranscriptionResult model with segments and speakers in src/models/transcription_result.py"
Task: "TranscriptionSegment model with word-level data in src/models/transcription_segment.py"
Task: "Word model with timing and confidence in src/models/word.py"
Task: "Speaker model with diarization data in src/models/speaker.py"
Task: "JobStatus enum and supporting types in src/models/types.py"
Task: "TranscriptionSettings configuration model in src/models/settings.py"

# Launch service layer together (T024-T028):
Task: "AudioFileService for file validation and metadata in src/services/audio_file_service.py"
Task: "TranscriptionService with WhisperX integration in src/services/transcription_service.py"
Task: "ProgressService for job progress tracking in src/services/progress_service.py"
Task: "StorageService for file-based persistence in src/services/storage_service.py"
Task: "HistoryService for transcription history management in src/services/history_service.py"
```

## Notes
- [P] tasks = different files, no dependencies between them
- All contract tests MUST fail before implementing any functionality (TDD)
- Verify WhisperX models download and cache properly during setup
- Test with actual audio files of various formats and sizes
- Monitor memory usage during large file processing
- Commit after completing each task group

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - mcp_tools_spec.json: 6 MCP tools → 6 contract test tasks [P] + 6 implementation tasks
   - error_responses.json: Error handling → 1 contract test task [P] + error handler implementation

2. **From Data Model**:
   - 6 core entities (AudioFile, TranscriptionJob, etc.) → 6 model tasks [P]
   - 2 supporting types → 2 additional model tasks [P]

3. **From User Stories (quickstart.md)**:
   - 5 integration scenarios → 5 integration test tasks [P]
   - End-to-end validation → 1 comprehensive test task

4. **Ordering**:
   - Setup → Contract Tests → Integration Tests → Models → Services → Tools → Integration → Polish
   - Dependencies enforced: models before services, services before tools

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All 6 MCP tools have corresponding contract tests
- [x] All 6+ entities have model creation tasks
- [x] All contract tests come before implementation
- [x] Parallel tasks ([P]) operate on different files
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD approach: tests fail before implementation
- [x] Integration scenarios from quickstart.md covered
- [x] Performance requirements addressed (1GB files, <200ms responses)
- [x] Error handling comprehensively tested
- [x] Storage and persistence properly implemented
- [x] WhisperX integration with speaker diarization
- [x] MCP protocol compliance validated