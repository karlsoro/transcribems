# TranscribeMCP REST API Guide - Complete Implementation

## Critical Features Implemented

✅ **Server-Sent Events (SSE)** - Real-time progress updates that survive tab switching  
✅ **Persistent Job Storage** - JSON-based storage survives server restarts  
✅ **Progress Tracking** - Real percentage-based progress (0-100%)  
✅ **48-Hour Retention** - Automatic cleanup with configurable retention  
✅ **AAC Support** - Full audio format support including AAC files  
✅ **CORS Fixed** - All origins allowed for development  

## Quick Start for UI Integration

### 1. Upload File (Immediate Response)

```javascript
const formData = new FormData();
formData.append('file', audioFile);
const res = await fetch('/v1/transcribe', { method: 'POST', body: formData });
const { job_id } = await res.json();
localStorage.setItem('currentJobId', job_id); // CRITICAL: Persist job ID
```

### 2. Stream Real-Time Progress (Recommended)

```javascript
const eventSource = new EventSource(`/v1/jobs/${job_id}/stream`);

eventSource.addEventListener('progress', (e) => {
  const { progress, message } = JSON.parse(e.data);
  updateProgressBar(progress); // 0-100%
});

eventSource.addEventListener('completed', (e) => {
  const { result } = JSON.parse(e.data);
  displayResults(result);
  eventSource.close();
});
```

### 3. Page Reload Recovery

```javascript
// On page load - reconnect to existing job!
const jobId = localStorage.getItem('currentJobId');
if (jobId) {
  const eventSource = new EventSource(`/v1/jobs/${jobId}/stream`);
  // Same event listeners as above
}
```

## Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/transcribe` | Upload file, get job_id immediately |
| GET | `/v1/jobs/{id}/stream` | **SSE stream** for real-time progress |
| GET | `/v1/jobs/{id}` | Polling fallback (not recommended) |
| GET | `/v1/jobs/{id}/download` | Download results JSON |
| DELETE | `/v1/jobs/{id}` | Cancel job |

## Progress Stages

- 0-5%: Job queued
- 5-15%: Initializing
- 15-30%: Loading models  
- 30-70%: Transcribing audio
- 70-95%: Speaker diarization
- 95-100%: Saving results
- 100%: Complete!

## Supported Formats
WAV, MP3, FLAC, M4A, AAC, MP4, OGG, WebM (max 5GB)

For complete API documentation, see full REST_API_GUIDE.md
