# Speaker Database Design

## Overview

This document describes the design for a speaker database system that stores speaker embeddings from pyannote.audio and enables speaker identification across transcription sessions with confidence-based learning.

## Architecture

### Components

1. **Speaker Embedding Extractor** - Extracts embeddings from audio segments using pyannote.audio's speaker verification model
2. **Speaker Database** - Stores speaker profiles with embeddings, names, and confidence scores
3. **Speaker Matcher** - Compares embeddings to identify speakers using cosine similarity
4. **Confidence Manager** - Adjusts confidence scores based on manual feedback
5. **API Layer** - REST endpoints for speaker management

### Database Schema

```sql
-- Speaker profiles table
CREATE TABLE speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Speaker embeddings table (one speaker can have multiple embeddings)
CREATE TABLE speaker_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    embedding FLOAT[] NOT NULL,  -- 512-dimensional vector for pyannote
    confidence FLOAT DEFAULT 0.5,  -- Initial confidence score
    source_file VARCHAR(500),
    audio_segment_start FLOAT,
    audio_segment_end FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Speaker identifications (tracking automatic vs manual)
CREATE TABLE speaker_identifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    embedding_id UUID REFERENCES speaker_embeddings(id) ON DELETE CASCADE,
    transcription_id UUID,
    segment_id VARCHAR(100),
    similarity_score FLOAT,
    identification_type VARCHAR(20) CHECK (identification_type IN ('automatic', 'manual')),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Confidence history for tracking adjustments
CREATE TABLE confidence_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding_id UUID REFERENCES speaker_embeddings(id) ON DELETE CASCADE,
    old_confidence FLOAT NOT NULL,
    new_confidence FLOAT NOT NULL,
    reason VARCHAR(20) CHECK (reason IN ('correct', 'incorrect', 'manual_verify', 'manual_reject')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_speaker_embeddings_speaker_id ON speaker_embeddings(speaker_id);
CREATE INDEX idx_speaker_identifications_speaker_id ON speaker_identifications(speaker_id);
CREATE INDEX idx_speaker_identifications_transcription ON speaker_identifications(transcription_id);
CREATE INDEX idx_confidence_history_embedding_id ON confidence_history(embedding_id);
```

## Embedding Extraction

### Using pyannote.audio Embedding Model

```python
from pyannote.audio import Model, Inference

# Load embedding model
model = Model.from_pretrained("pyannote/embedding")
inference = Inference(model, window="whole")

# Extract embedding from audio segment
embedding = inference(audio_segment)
# Returns 512-dimensional numpy array
```

## Speaker Matching Algorithm

### Similarity Calculation

1. **Cosine Similarity**: Compare new embedding against all stored embeddings
   ```python
   similarity = cosine_similarity(new_embedding, stored_embedding)
   ```

2. **Threshold-based Matching**:
   - High confidence: similarity > 0.85
   - Medium confidence: 0.70 < similarity <= 0.85
   - Low confidence: 0.60 < similarity <= 0.70
   - No match: similarity <= 0.60

3. **Multi-embedding Strategy**:
   - Each speaker has multiple embeddings from different recordings
   - Match against highest similarity among all embeddings
   - Aggregate confidence from top N matches

## Confidence Scoring System

### Initial Confidence

- New speaker (first embedding): 0.5
- Automatic identification: Based on similarity score (0.6-0.95)
- Manual identification: 0.95

### Confidence Adjustment Rules

1. **Correct Identification (Manual Verification)**:
   ```python
   new_confidence = min(1.0, old_confidence * 1.2)
   ```

2. **Incorrect Identification (Manual Correction)**:
   ```python
   new_confidence = max(0.1, old_confidence * 0.7)
   ```

3. **Repeated Correct Matches**:
   - After 3 consecutive correct matches: +0.05
   - After 5 consecutive correct matches: +0.10
   - After 10 consecutive correct matches: +0.15

4. **Decay for Unused Embeddings**:
   - Not used for 30 days: -0.05
   - Not used for 90 days: -0.10
   - Not used for 180 days: -0.15

### Confidence Thresholds for Auto-Assignment

- confidence >= 0.85: Auto-assign name
- confidence 0.70-0.84: Suggest name, require confirmation
- confidence < 0.70: Use generic "SPEAKER_XX" label

## API Design

### Speaker Management

```
POST   /api/speakers                    # Create new speaker
GET    /api/speakers                    # List all speakers
GET    /api/speakers/{id}               # Get speaker details
PUT    /api/speakers/{id}               # Update speaker name/metadata
DELETE /api/speakers/{id}               # Delete speaker

POST   /api/speakers/{id}/embeddings    # Add embedding to speaker
GET    /api/speakers/{id}/embeddings    # List speaker embeddings
```

### Speaker Identification

```
POST   /api/identify/audio              # Identify speaker from audio file
POST   /api/identify/embedding          # Identify speaker from embedding
POST   /api/verify/{identification_id}  # Verify/correct identification
```

### Embedding Management

```
GET    /api/embeddings/{id}             # Get embedding details
DELETE /api/embeddings/{id}             # Delete embedding
PUT    /api/embeddings/{id}/confidence  # Update confidence score
```

## Integration with WhisperX Service

### Enhanced Workflow

1. **Transcription with Diarization**:
   - WhisperX performs initial diarization (SPEAKER_00, SPEAKER_01, etc.)
   - Extract speaker embeddings for each diarized segment

2. **Speaker Identification**:
   - Compare embeddings against speaker database
   - Replace generic labels with known speaker names (if confidence > threshold)
   - Flag uncertain identifications for manual review

3. **Manual Feedback Loop**:
   - User confirms or corrects speaker identifications
   - Update confidence scores based on feedback
   - Store new embeddings for confirmed speakers

### Response Format

```json
{
  "text": "Full transcription text",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello everyone",
      "speaker": "John Smith",
      "speaker_id": "uuid-123",
      "confidence": 0.92,
      "identification_type": "automatic",
      "suggested_speaker": null
    },
    {
      "start": 3.5,
      "end": 7.2,
      "text": "Hi John",
      "speaker": "SPEAKER_01",
      "speaker_id": null,
      "confidence": 0.68,
      "identification_type": "uncertain",
      "suggested_speaker": {
        "name": "Jane Doe",
        "speaker_id": "uuid-456",
        "confidence": 0.68
      }
    }
  ],
  "speakers": [
    {
      "id": "uuid-123",
      "name": "John Smith",
      "segment_count": 15,
      "avg_confidence": 0.92
    }
  ]
}
```

## Storage Backend Options

### Option 1: PostgreSQL with pgvector

- **Pros**: SQL queries, ACID compliance, vector similarity search with pgvector extension
- **Cons**: Requires pgvector extension installation

```sql
CREATE EXTENSION vector;
CREATE TABLE speaker_embeddings (
    id UUID PRIMARY KEY,
    speaker_id UUID REFERENCES speakers(id),
    embedding vector(512),  -- pgvector type
    confidence FLOAT
);

-- Vector similarity index
CREATE INDEX ON speaker_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### Option 2: SQLite with JSON (Development/Standalone)

- **Pros**: No setup, portable, good for development
- **Cons**: No native vector operations, slower similarity search

```python
# Store embedding as JSON array
embedding_json = json.dumps(embedding.tolist())
```

### Option 3: Hybrid (PostgreSQL + Vector DB)

- **PostgreSQL**: Metadata, confidence scores, relationships
- **Qdrant/Milvus**: High-performance vector similarity search
- **Pros**: Best performance for large-scale
- **Cons**: More complex architecture

## Performance Considerations

1. **Embedding Extraction**: ~50-100ms per audio segment
2. **Database Lookup**: <10ms for <10,000 speakers
3. **Similarity Calculation**: <5ms for 512-dim vectors
4. **Total Overhead**: ~100-200ms per speaker segment

### Optimization Strategies

1. **Batch Processing**: Extract all embeddings, then identify in batch
2. **Caching**: Cache frequently used speaker embeddings
3. **Indexing**: Use vector similarity indexes (pgvector, FAISS)
4. **Pruning**: Remove low-confidence embeddings after extended periods

## Security & Privacy

1. **Embedding Storage**: Embeddings are biometric data - encrypt at rest
2. **Access Control**: Implement RBAC for speaker database
3. **Data Retention**: Configurable retention policies for embeddings
4. **Anonymization**: Option to use speaker IDs instead of names
5. **GDPR Compliance**: Right to deletion, data export

## Migration Path

### Phase 1: Core Infrastructure
- Speaker database schema
- Embedding extraction service
- Basic similarity matching

### Phase 2: Integration
- WhisperX service integration
- REST API endpoints
- Confidence scoring system

### Phase 3: Enhancement
- Manual feedback UI
- Confidence learning algorithms
- Performance optimizations

### Phase 4: Advanced Features
- Multi-language support
- Voice aging compensation
- Cross-application speaker sharing
