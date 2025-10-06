# Speaker Identification UI Integration Guide

## Overview

The speaker identification system is **separate from transcription**. Transcription gives you generic labels (SPEAKER_00, SPEAKER_01, etc.), and this component helps identify who those speakers actually are.

## Architecture

```
┌─────────────┐        ┌──────────────────┐
│             │        │  Transcription   │
│     UI      │───────>│  Returns:        │
│             │        │  - segments      │
└─────────────┘        │  - SPEAKER_00    │
       │               │  - SPEAKER_01    │
       │               │  - metadata      │
       │               └──────────────────┘
       │
       │               ┌──────────────────┐
       │               │   Speaker ID     │
       └──────────────>│   Component      │
                       │  - Identify      │
                       │  - Feedback      │
                       │  - Learning      │
                       └──────────────────┘
```

## API Endpoints

### Base URL
```
http://localhost:8000/v1/speaker
```

### 1. Identify Speaker
**POST /v1/speaker/identify**

Identify who a speaker is based on an audio clip.

**Request:**
```typescript
// FormData multipart/form-data
{
  audio_clip: File,           // Short audio clip (2-5 seconds, WAV)
  job_id: string,            // Original transcription job ID
  segment_index: number      // Which segment this corresponds to
}
```

**Example:**
```javascript
const formData = new FormData();
formData.append('audio_clip', audioBlob, 'segment_0.wav');
formData.append('job_id', transcriptionJobId);
formData.append('segment_index', 0);

const response = await fetch('http://localhost:8000/v1/speaker/identify', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

**Response:**
```json
{
  "match_found": true,
  "speaker_name": "John Doe",
  "confidence_score": 0.87,
  "audio_clip_id": "a7f3e8d1-...",
  "message": "Speaker identified with high confidence"
}
```

OR if no match:
```json
{
  "match_found": false,
  "speaker_name": null,
  "confidence_score": 0.0,
  "audio_clip_id": "a7f3e8d1-...",
  "message": "No match found in speaker database"
}
```

### 2. Submit Feedback
**POST /v1/speaker/feedback**

Tell the system if the identification was correct or provide the correct name.

**Request:**
```json
{
  "audio_clip_id": "a7f3e8d1-...",        // From identify response
  "suggested_name": "John Doe",           // What system suggested (null if no match)
  "user_provided_name": "John Doe",       // What user says is correct
  "user_agrees": true                     // true if agrees with suggestion
}
```

**Response:**
```json
{
  "success": true,
  "message": "Confidence increased for 'John Doe'",
  "new_speaker_added": false,
  "audio_clip_id": "a7f3e8d1-..."
}
```

### 3. List Known Speakers
**GET /v1/speaker/list**

Get all speakers in the database.

**Response:**
```json
{
  "speakers": [
    {
      "name": "John Doe",
      "average_confidence": 0.92,
      "sample_count": 45
    },
    {
      "name": "Jane Smith",
      "average_confidence": 0.88,
      "sample_count": 32
    }
  ],
  "total_count": 2
}
```

### 4. Delete Speaker
**DELETE /v1/speaker/speaker/{speaker_name}**

Remove a speaker from the database.

**Response:**
```json
{
  "success": true,
  "message": "Deleted speaker: John Doe"
}
```

## UI Workflow

### Step 1: Get Transcription
```javascript
// Upload audio for transcription
const transcription = await transcribeAudio(audioFile);

// Response includes:
// {
//   segments: [...],
//   speakers: ["SPEAKER_00", "SPEAKER_01"],
//   metadata: {
//     original_filename: "meeting.wav",
//     job_id: "abc123",
//     language: "en"
//   }
// }
```

### Step 2: Extract Audio Clips for Each Speaker

For each unique speaker, extract a 2-5 second audio clip from one of their segments:

```javascript
// Extract audio clip from original file using segment timestamps
async function extractAudioClip(originalAudioFile, segment) {
  const { start, end } = segment;

  // Use Web Audio API or send to backend to extract clip
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(
    await originalAudioFile.arrayBuffer()
  );

  const sampleRate = audioBuffer.sampleRate;
  const startSample = Math.floor(start * sampleRate);
  const endSample = Math.floor(end * sampleRate);
  const length = endSample - startSample;

  const clip = audioContext.createBuffer(
    audioBuffer.numberOfChannels,
    length,
    sampleRate
  );

  for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
    const sourceData = audioBuffer.getChannelData(channel);
    const clipData = clip.getChannelData(channel);
    for (let i = 0; i < length; i++) {
      clipData[i] = sourceData[startSample + i];
    }
  }

  return audioBufferToWav(clip);
}
```

### Step 3: Identify Each Speaker

```javascript
// Group segments by speaker
const speakerSegments = {};
transcription.segments.forEach(segment => {
  if (!speakerSegments[segment.speaker]) {
    speakerSegments[segment.speaker] = [];
  }
  speakerSegments[segment.speaker].push(segment);
});

// For each speaker, extract clip and identify
const identifications = {};

for (const [speaker, segments] of Object.entries(speakerSegments)) {
  // Use first segment as sample (at least 2 seconds long)
  const sampleSegment = segments.find(s => (s.end - s.start) >= 2) || segments[0];

  const audioClip = await extractAudioClip(originalAudioFile, sampleSegment);

  const formData = new FormData();
  formData.append('audio_clip', audioClip, `${speaker}.wav`);
  formData.append('job_id', transcription.metadata.job_id);
  formData.append('segment_index', segments[0].id);

  const response = await fetch('/v1/speaker/identify', {
    method: 'POST',
    body: formData
  });

  identifications[speaker] = await response.json();
}

// Now you have:
// identifications = {
//   "SPEAKER_00": { match_found: true, speaker_name: "John Doe", ... },
//   "SPEAKER_01": { match_found: false, speaker_name: null, ... }
// }
```

### Step 4: Show UI for User Confirmation

```javascript
// For each speaker, show identification result
{identifications.map(({speaker, result}) => (
  <SpeakerCard key={speaker}>
    <h3>{speaker}</h3>
    {result.match_found ? (
      <div>
        <p>Identified as: <strong>{result.speaker_name}</strong></p>
        <p>Confidence: {(result.confidence_score * 100).toFixed(0)}%</p>
        <button onClick={() => confirmSpeaker(speaker, result)}>
          ✓ Correct
        </button>
        <button onClick={() => correctSpeaker(speaker, result)}>
          ✗ Change Name
        </button>
      </div>
    ) : (
      <div>
        <p>Unknown speaker</p>
        <input
          type="text"
          placeholder="Enter speaker name"
          onChange={e => setSpeakerName(speaker, e.target.value)}
        />
        <button onClick={() => addNewSpeaker(speaker, result)}>
          Add Speaker
        </button>
      </div>
    )}
  </SpeakerCard>
))}
```

### Step 5: Submit Feedback

```javascript
// User confirms identification is correct
async function confirmSpeaker(speaker, result) {
  await fetch('/v1/speaker/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_clip_id: result.audio_clip_id,
      suggested_name: result.speaker_name,
      user_provided_name: result.speaker_name,
      user_agrees: true
    })
  });

  // Confidence score increases for this speaker
}

// User corrects the identification
async function correctSpeaker(speaker, result, correctName) {
  await fetch('/v1/speaker/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_clip_id: result.audio_clip_id,
      suggested_name: result.speaker_name,
      user_provided_name: correctName,
      user_agrees: false
    })
  });

  // Old name confidence decreases
  // New name confidence increases (or gets added to DB)
}

// User provides name for unknown speaker
async function addNewSpeaker(speaker, result, newName) {
  await fetch('/v1/speaker/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_clip_id: result.audio_clip_id,
      suggested_name: null,
      user_provided_name: newName,
      user_agrees: false
    })
  });

  // New speaker added to database with initial confidence
}
```

## Complete Example Flow

```javascript
// 1. User uploads audio file
const audioFile = document.getElementById('audio-upload').files[0];

// 2. Transcribe the audio
const transcription = await transcribeAudio(audioFile);
// Returns: { segments, speakers: ["SPEAKER_00", "SPEAKER_01"], metadata }

// 3. For each speaker, identify them
const speakers = [...new Set(transcription.speakers)];
const identifications = [];

for (const speaker of speakers) {
  // Find a good segment for this speaker (2-5 seconds)
  const segment = transcription.segments
    .filter(s => s.speaker === speaker && (s.end - s.start) >= 2)
    [0];

  if (!segment) continue;

  // Extract audio clip
  const clip = await extractAudioClip(audioFile, segment);

  // Identify speaker
  const formData = new FormData();
  formData.append('audio_clip', clip, `${speaker}.wav`);
  formData.append('job_id', transcription.metadata.job_id);
  formData.append('segment_index', segment.id);

  const result = await fetch('/v1/speaker/identify', {
    method: 'POST',
    body: formData
  }).then(r => r.json());

  identifications.push({ speaker, result });
}

// 4. Show UI with results
renderSpeakerIdentifications(identifications);

// 5. When user confirms/corrects, send feedback
// (see confirmSpeaker, correctSpeaker, addNewSpeaker functions above)
```

## Confidence Score System

### Initial Scores
- New speaker added: **0.6** initial confidence
- First manual confirmation: boost to **0.75**

### Score Adjustments
- User agrees with suggestion: **+0.10** (capped at 0.95)
- User corrects suggestion:
  - Wrong name: **-0.05**
  - Correct name: **+0.15** (or create with 0.6 if new)

### Thresholds
- **≥ 0.85**: High confidence - show with green indicator
- **0.70 - 0.84**: Medium confidence - show with yellow indicator
- **0.60 - 0.69**: Low confidence - show with orange indicator
- **< 0.60**: Not reliable - don't auto-suggest

## Error Handling

```javascript
try {
  const result = await fetch('/v1/speaker/identify', {
    method: 'POST',
    body: formData
  });

  if (!result.ok) {
    const error = await result.json();
    console.error('Speaker identification failed:', error.detail);
    // Show error to user
  }

  const data = await result.json();
  // Process successful result

} catch (error) {
  console.error('Network error:', error);
  // Show network error to user
}
```

## Notes

- **Audio clips should be 2-5 seconds** for best results
- **WAV format** is preferred for audio clips
- System learns over time - more feedback = better accuracy
- Each speaker needs manual confirmation at least once
- Confidence scores prevent false positives
