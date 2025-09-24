# Tasks: WhisperX Audio Transcription API

**Input**: Design documents from `/home/karlsoro/Projects/TranscribeMS/specs/001-api-transcribe/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✅
   → Extracted: Python 3.11, WhisperX, FastAPI, PyTorch, Celery, Redis
2. Load design documents ✅
   → data-model.md: 6 entities → 6 model tasks
   → contracts/api_spec.yaml: 4 endpoints → 4 contract tests + 4 implementations
   → research.md: Technical decisions → 3 setup tasks
   → quickstart.md: 3 integration scenarios → 3 integration tests
3. Generate tasks by category ✅
   → Setup: 4 tasks, Tests: 7 tasks, Core: 12 tasks, Integration: 5 tasks, Polish: 6 tasks
4. Apply task rules ✅
   → Different files = [P], Same file = sequential, Tests before implementation
5. Number tasks sequentially (T001-T034) ✅
6. Generate dependency graph ✅
7. Create parallel execution examples ✅
8. Validate task completeness ✅
   → All 4 endpoints have contract tests ✅
   → All 6 entities have model tasks ✅
   → All tests before implementation ✅
9. SUCCESS - 34 tasks ready for execution
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (based on plan.md)

## Phase 3.1: Setup
- [ ] T001 Create Python 3.11 project structure with src/, tests/, and configuration files
- [ ] T002 Initialize pyproject.toml with WhisperX, FastAPI, PyTorch, Celery, Redis dependencies
- [ ] T003 [P] Configure black, flake8, mypy in pyproject.toml and setup.cfg
- [ ] T004 [P] Setup Docker configuration with CUDA support in Dockerfile and docker-compose.yml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [ ] T005 [P] Contract test POST /v1/transcriptions in tests/contract/test_create_transcription.py
- [ ] T006 [P] Contract test GET /v1/transcriptions/{job_id} in tests/contract/test_get_transcription.py
- [ ] T007 [P] Contract test DELETE /v1/transcriptions/{job_id} in tests/contract/test_cancel_transcription.py
- [ ] T008 [P] Contract test GET /v1/health in tests/contract/test_health_check.py

### Integration Tests (User Stories)
- [ ] T009 [P] Integration test simple audio transcription (5-minute MP3, 2 speakers) in tests/integration/test_simple_transcription.py
- [ ] T010 [P] Integration test large file processing (2GB WAV, 3-hour conference) in tests/integration/test_large_file_processing.py
- [ ] T011 [P] Integration test real-time progress monitoring via SSE in tests/integration/test_progress_monitoring.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models
- [ ] T012 [P] AudioFile model with validation rules in src/models/audio_file.py
- [ ] T013 [P] TranscriptionJob model with state transitions in src/models/transcription_job.py
- [ ] T014 [P] Transcription result model in src/models/transcription.py
- [ ] T015 [P] Speaker model in src/models/speaker.py
- [ ] T016 [P] SpeechSegment model with timing validation in src/models/speech_segment.py
- [ ] T017 [P] ProcessingLog model for audit trail in src/models/processing_log.py

### Core Services
- [ ] T018 [P] WhisperX integration service with GPU/CPU detection in src/services/whisperx_service.py
- [ ] T019 [P] Audio processing service with chunking for large files in src/services/audio_processor.py
- [ ] T020 [P] File validation service for format/size checks in src/services/file_validator.py
- [ ] T021 TranscriptionService orchestrator for job lifecycle in src/services/transcription_service.py
- [ ] T022 Memory management service for GPU optimization in src/services/memory_manager.py

### API Endpoints
- [ ] T023 POST /v1/transcriptions endpoint with file upload in src/api/endpoints/transcriptions.py
- [ ] T024 GET /v1/transcriptions/{job_id} status endpoint in src/api/endpoints/transcriptions.py
- [ ] T025 DELETE /v1/transcriptions/{job_id} cancellation in src/api/endpoints/transcriptions.py
- [ ] T026 [P] GET /v1/health system health check in src/api/endpoints/health.py

## Phase 3.4: Integration

### Background Processing
- [ ] T027 Celery task worker for async transcription processing in src/tasks/transcription_tasks.py
- [ ] T028 Redis configuration and job queue management in src/core/redis_config.py
- [ ] T029 Server-Sent Events for real-time progress updates in src/api/endpoints/progress.py

### Application Infrastructure
- [ ] T030 FastAPI application factory with middleware in src/main.py
- [ ] T031 Comprehensive error handling with custom exceptions in src/core/exceptions.py

## Phase 3.5: Polish

### Testing & Quality
- [ ] T032 [P] Unit tests for audio processing utilities in tests/unit/test_audio_processor.py
- [ ] T033 [P] Performance tests for memory usage and GPU optimization in tests/performance/test_system_performance.py
- [ ] T034 [P] End-to-end test scenarios from quickstart guide in tests/e2e/test_quickstart_scenarios.py

## Dependencies

### Setup Dependencies
- T001 → T002 (structure before dependencies)
- T002 → T003, T004 (dependencies before configuration)

### Test Dependencies (Phase 3.2)
- Setup (T001-T004) → Tests (T005-T011)
- All tests must be written and failing before Phase 3.3

### Implementation Dependencies (Phase 3.3)
- Models (T012-T017) → Services (T018-T022)
- Services → Endpoints (T023-T026)
- T021 depends on T018, T019, T020 (TranscriptionService uses other services)
- T023, T024, T025 modify same file → sequential execution

### Integration Dependencies (Phase 3.4)
- Services (T018-T022) → Background tasks (T027, T028)
- All endpoints → Application factory (T030)
- All components → Error handling (T031)

### Polish Dependencies (Phase 3.5)
- All implementation → Polish tests (T032-T034)

## Parallel Execution Examples

### Phase 3.1 Setup (Parallel where possible)
```bash
# Launch T003 and T004 together after T002 completes:
Task: "Configure black, flake8, mypy in pyproject.toml and setup.cfg"
Task: "Setup Docker configuration with CUDA support in Dockerfile and docker-compose.yml"
```

### Phase 3.2 Contract Tests (All Parallel)
```bash
# Launch T005-T008 together:
Task: "Contract test POST /v1/transcriptions in tests/contract/test_create_transcription.py"
Task: "Contract test GET /v1/transcriptions/{job_id} in tests/contract/test_get_transcription.py"
Task: "Contract test DELETE /v1/transcriptions/{job_id} in tests/contract/test_cancel_transcription.py"
Task: "Contract test GET /v1/health in tests/contract/test_health_check.py"
```

### Phase 3.2 Integration Tests (All Parallel)
```bash
# Launch T009-T011 together:
Task: "Integration test simple audio transcription (5-minute MP3, 2 speakers) in tests/integration/test_simple_transcription.py"
Task: "Integration test large file processing (2GB WAV, 3-hour conference) in tests/integration/test_large_file_processing.py"
Task: "Integration test real-time progress monitoring via SSE in tests/integration/test_progress_monitoring.py"
```

### Phase 3.3 Data Models (All Parallel)
```bash
# Launch T012-T017 together:
Task: "AudioFile model with validation rules in src/models/audio_file.py"
Task: "TranscriptionJob model with state transitions in src/models/transcription_job.py"
Task: "Transcription result model in src/models/transcription.py"
Task: "Speaker model in src/models/speaker.py"
Task: "SpeechSegment model with timing validation in src/models/speech_segment.py"
Task: "ProcessingLog model for audit trail in src/models/processing_log.py"
```

### Phase 3.3 Core Services (Partial Parallel)
```bash
# Launch T018-T020 together (independent services):
Task: "WhisperX integration service with GPU/CPU detection in src/services/whisperx_service.py"
Task: "Audio processing service with chunking for large files in src/services/audio_processor.py"
Task: "File validation service for format/size checks in src/services/file_validator.py"

# T021 and T022 run after T018-T020 complete (dependencies)
```

### Phase 3.5 Polish Tests (All Parallel)
```bash
# Launch T032-T034 together:
Task: "Unit tests for audio processing utilities in tests/unit/test_audio_processor.py"
Task: "Performance tests for memory usage and GPU optimization in tests/performance/test_system_performance.py"
Task: "End-to-end test scenarios from quickstart guide in tests/e2e/test_quickstart_scenarios.py"
```

## Notes

### TDD Requirements
- **CRITICAL**: All tests (T005-T011) must fail before starting implementation
- Run `pytest tests/contract/` and `pytest tests/integration/` to verify failures
- Only proceed to Phase 3.3 after confirming test failures

### File Modification Rules
- **[P] tasks**: Different files, can run simultaneously
- **Sequential tasks**: Same file (e.g., T023-T025 all modify src/api/endpoints/transcriptions.py)
- **Dependencies**: Some tasks require others to complete first

### GPU/CUDA Considerations
- Ensure NVIDIA drivers and CUDA toolkit installed before T018 (WhisperX service)
- GPU memory management critical for T022 (Memory manager service)
- Performance tests (T033) should validate both CPU and GPU modes

### Large File Handling
- T019 (Audio processor) must implement chunking strategy for 5GB files
- T027 (Celery tasks) must handle long-running background processing
- T010 (Large file integration test) validates complete workflow

### Error Handling Strategy
- T031 (Error handling) implements comprehensive exception hierarchy
- All services must use custom exceptions for proper error categorization
- API endpoints must return appropriate HTTP status codes per OpenAPI spec

## Validation Checklist
*GATE: Checked during execution*

- [x] All 4 API endpoints have corresponding contract tests (T005-T008)
- [x] All 6 entities have model creation tasks (T012-T017)
- [x] All tests come before implementation (T005-T011 before T012+)
- [x] Parallel tasks ([P]) truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] Dependencies properly sequenced (Setup → Tests → Core → Integration → Polish)

## Expected Outcomes

### After Phase 3.2 (Tests)
- 7 failing tests (4 contract + 3 integration)
- Test fixtures for audio files created
- Test infrastructure validated

### After Phase 3.3 (Core)
- All contract tests passing
- 6 data models with full validation
- 5 core services implementing business logic
- 4 API endpoints with proper error handling

### After Phase 3.4 (Integration)
- Background processing with Celery/Redis
- Real-time progress monitoring via SSE
- Complete FastAPI application ready for deployment

### After Phase 3.5 (Polish)
- Comprehensive test coverage (>85% per constitution)
- Performance validation for large files
- End-to-end workflow verification
- Production-ready application