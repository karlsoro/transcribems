# Speaker Database Usage Guide

## Overview

The Speaker Database system enables persistent speaker identification across transcription sessions using pyannote.audio embeddings. Instead of generic labels like "SPEAKER_00", the system can automatically identify known speakers by name with confidence-based learning from manual feedback.

## Quick Start

### 1. Enable Speaker Services

The speaker services are automatically initialized when the application starts. Ensure your `.env` file includes:

```env
HF_TOKEN=your_huggingface_token_here
```

The speaker database is stored in `speaker_database.db` (SQLite).

### 2. Register a New Speaker

**API Endpoint**: `POST /api/speakers/register`

```bash
curl -X POST "http://localhost:8000/api/speakers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "audio_path": "/path/to/audio.wav",
    "start_time": 0.0,
    "end_time": 5.0,
    "metadata": {
      "department": "Engineering",
      "role": "Manager"
    }
  }'
```

**Response**:
```json
{
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Smith",
  "message": "Speaker registered successfully"
}
```

### 3. Identify Speaker from Audio

**API Endpoint**: `POST /api/speakers/identify`

```bash
curl -X POST "http://localhost:8000/api/speakers/identify" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "/path/to/new_audio.wav",
    "start_time": 10.0,
    "end_time": 15.0,
    "transcription_id": "trans-123",
    "segment_id": "seg-456"
  }'
```

**Response (Automatic Identification)**:
```json
{
  "identified": true,
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "speaker_name": "John Smith",
  "confidence": 0.92,
  "similarity": 0.89,
  "identification_type": "automatic",
  "suggested_speaker": null
}
```

**Response (Suggested Match)**:
```json
{
  "identified": false,
  "speaker_id": null,
  "speaker_name": null,
  "confidence": 0.78,
  "similarity": 0.75,
  "identification_type": "suggested",
  "suggested_speaker": {
    "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
    "speaker_name": "John Smith",
    "confidence": 0.78
  }
}
```

**Response (Unknown Speaker)**:
```json
{
  "identified": false,
  "speaker_id": null,
  "speaker_name": null,
  "confidence": 0.0,
  "identification_type": "unknown",
  "suggested_speaker": null
}
```

### 4. Verify/Correct Identification

When the system suggests a speaker or you need to correct an identification:

**API Endpoint**: `POST /api/speakers/verify`

```bash
curl -X POST "http://localhost:8000/api/speakers/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
    "embedding": [...],  # 512-dimensional array from identification response
    "correct": true,
    "transcription_id": "trans-123",
    "segment_id": "seg-456",
    "source_file": "/path/to/audio.wav",
    "segment_start": 10.0,
    "segment_end": 15.0
  }'
```

**Parameters**:
- `correct: true` - Confirms the identification was correct
- `correct: false` - Indicates the speaker was wrong (but `speaker_id` is the correct one)

## API Reference

### Speaker Management

#### Create Speaker

```http
POST /api/speakers/
```

**Request Body**:
```json
{
  "name": "Jane Doe",
  "metadata": {
    "title": "CEO",
    "company": "Acme Corp"
  }
}
```

#### List All Speakers

```http
GET /api/speakers/
```

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Smith",
    "created_at": "2025-10-04T10:00:00",
    "updated_at": "2025-10-04T10:00:00",
    "metadata": {},
    "embedding_count": 5,
    "avg_confidence": 0.87
  }
]
```

#### Get Speaker Details

```http
GET /api/speakers/{speaker_id}
```

#### Delete Speaker

```http
DELETE /api/speakers/{speaker_id}
```

### Speaker Embeddings

#### Get Speaker Embeddings

```http
GET /api/speakers/{speaker_id}/embeddings
```

**Response**:
```json
{
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "embeddings": [
    {
      "embedding_id": "...",
      "embedding": [...],  # 512-dimensional array
      "confidence": 0.92,
      "source_file": "/path/to/audio.wav",
      "audio_segment_start": 0.0,
      "audio_segment_end": 5.0,
      "metadata": {}
    }
  ],
  "count": 1
}
```

### Speaker Statistics

#### Get Speaker Statistics

```http
GET /api/speakers/{speaker_id}/statistics
```

**Response**:
```json
{
  "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Smith",
  "embedding_count": 5,
  "avg_confidence": 0.87,
  "max_confidence": 0.95,
  "min_confidence": 0.72,
  "created_at": "2025-10-04T10:00:00",
  "metadata": {}
}
```

## Integration with Transcription

### Workflow

1. **Transcribe with Diarization**: Use WhisperX to transcribe and diarize audio
2. **Extract Embeddings**: Extract speaker embeddings from each diarized segment
3. **Identify Speakers**: Match embeddings against speaker database
4. **Update Transcription**: Replace generic labels with identified names
5. **Manual Review**: User confirms or corrects identifications
6. **Learn**: System updates confidence scores based on feedback

### Enhanced Transcription Response

Future integration will provide:

```json
{
  "text": "Hello everyone, this is John speaking.",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello everyone",
      "speaker": "John Smith",
      "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
      "confidence": 0.92,
      "identification_type": "automatic"
    },
    {
      "start": 3.5,
      "end": 7.0,
      "text": "this is John speaking",
      "speaker": "SPEAKER_00",
      "speaker_id": null,
      "confidence": 0.68,
      "identification_type": "uncertain",
      "suggested_speaker": {
        "name": "John Smith",
        "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
        "confidence": 0.68
      }
    }
  ]
}
```

## Confidence Scoring

### Confidence Levels

- **High (≥0.85)**: Automatic assignment, high certainty
- **Medium (0.70-0.84)**: Suggested assignment, requires confirmation
- **Low (0.60-0.69)**: Uncertain match, manual review recommended
- **Very Low (<0.60)**: No reliable match, treat as unknown

### Confidence Adjustment

The system learns from manual feedback:

1. **Correct Identification**: Confidence increases by 20% (max 1.0)
2. **Incorrect Identification**: Confidence decreases by 30% (min 0.1)
3. **Related Embeddings**: Similar embeddings are adjusted based on feedback
4. **Decay**: Unused embeddings lose confidence over time

### Example Confidence Evolution

```
Initial:     0.50 (new speaker)
  ↓ Manual verification (correct)
Updated:     0.95
  ↓ Automatic match (similar segment)
Confirmed:   0.92
  ↓ User confirms again
Reinforced:  0.95 (capped at 1.0)
  ↓ Not used for 90 days
Decayed:     0.85
```

## Best Practices

### 1. Initial Speaker Registration

- Use clear audio samples (5-10 seconds minimum)
- Choose segments where speaker is alone
- Register from multiple recordings for robustness
- Include metadata for context (role, department, etc.)

### 2. Ongoing Identification

- Review suggested matches when confidence is 0.70-0.84
- Always verify first few identifications for new speakers
- Provide feedback on automatic identifications when errors occur
- Re-register speakers if voice changes significantly (illness, aging)

### 3. Database Maintenance

- Periodically review and merge duplicate speakers
- Remove outdated or low-confidence embeddings
- Export speaker database for backup
- Use metadata to organize speakers by context (project, department, etc.)

### 4. Privacy & Security

- Store speaker database securely (embeddings are biometric data)
- Implement access controls for speaker management endpoints
- Consider encryption at rest for production deployments
- Provide data export/deletion for GDPR compliance

## Multi-Application Sharing

The speaker database is designed to be shared across applications:

### Shared Database Approach

```python
# Application A
db_service = SpeakerDatabaseService(db_path="/shared/speaker_db.db")

# Application B (different service)
db_service = SpeakerDatabaseService(db_path="/shared/speaker_db.db")
```

### Benefits

- **Consistent Identification**: Same speakers identified across applications
- **Accumulated Learning**: Confidence improves from all applications
- **Centralized Management**: Single database for all speaker data

### Considerations

- Ensure database is accessible to all applications
- Use proper file locking for concurrent access
- Consider PostgreSQL with pgvector for high-concurrency scenarios

## Troubleshooting

### Low Identification Accuracy

**Possible Causes**:
- Poor audio quality in reference samples
- Insufficient number of embeddings per speaker
- Voice changes (illness, emotion, audio quality)
- Similar-sounding speakers

**Solutions**:
- Add more diverse reference samples
- Use longer audio segments (5-10 seconds)
- Adjust confidence thresholds
- Manual verification and feedback

### Database Performance Issues

**Symptoms**: Slow speaker identification

**Solutions**:
- Regularly prune low-confidence embeddings
- Limit embeddings per speaker (keep top 10-20)
- Consider PostgreSQL with pgvector for vector similarity indexing
- Implement embedding caching for frequently identified speakers

### Confidence Not Improving

**Check**:
- Ensure manual verification is being recorded
- Verify embeddings are from same speaker
- Check if audio quality is consistent
- Review similarity thresholds

## Advanced Configuration

### Custom Thresholds

Adjust confidence thresholds in the identification service:

```python
identification_service = SpeakerIdentificationService(
    embedding_service=embedding_service,
    database_service=database_service,
    auto_assign_threshold=0.90,  # Higher = more conservative
    suggest_threshold=0.75,       # Widen suggestion range
    min_match_threshold=0.65      # Lower = more matches
)
```

### Database Backend

Switch to PostgreSQL with pgvector for production:

```sql
-- Install pgvector extension
CREATE EXTENSION vector;

-- Modify schema to use vector type
CREATE TABLE speaker_embeddings (
    id UUID PRIMARY KEY,
    speaker_id UUID REFERENCES speakers(id),
    embedding vector(512),  -- Native vector type
    confidence FLOAT,
    ...
);

-- Create vector similarity index
CREATE INDEX ON speaker_embeddings
USING ivfflat (embedding vector_cosine_ops);
```

## Migration & Export

### Export Speaker Database

```bash
# SQLite backup
cp speaker_database.db speaker_database_backup.db

# Export to JSON
python scripts/export_speaker_db.py --output speakers.json
```

### Import Speaker Database

```bash
python scripts/import_speaker_db.py --input speakers.json
```

## Support & Resources

- **Design Document**: [SPEAKER_DATABASE_DESIGN.md](SPEAKER_DATABASE_DESIGN.md)
- **API Documentation**: Available at `/docs` endpoint
- **Source Code**:
  - `src/services/speaker_embedding_service.py`
  - `src/services/speaker_database_service.py`
  - `src/services/speaker_identification_service.py`
  - `src/api/endpoints/speaker_management.py`
