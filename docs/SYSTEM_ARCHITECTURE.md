# AI-Powered Smart Note Generator & Engagement Tracker - System Architecture

## Project Overview

The **AI-Powered Smart Note Generator & Engagement Tracker** is an intelligent web application designed to automatically generate structured notes, summaries, and key action items from meetings and online classes while simultaneously tracking participant engagement using computer vision techniques.

### Key Objectives
- Automate speech-to-text conversion from meeting recordings
- Generate intelligent summaries, key points, and action items using NLP
- Track participant engagement through facial detection and attention analysis
- Provide comprehensive analytics and PDF reports for educators/organizers
- Reduce manual note-taking effort and improve knowledge retention

---

## Complete End-to-End Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    USER INITIATES MEETING/CLASS SESSION                      │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │   CREATE SESSION     │  │  UPLOAD AUDIO FILE   │
        │   (POST /sessions)   │  │ (POST /audio/upload) │
        └──────────────────────┘  └──────────────────────┘
                    │                         │
                    │         ┌───────────���───┘
                    │         │
                    ▼         ▼
        ┌─────────────────────────────────┐
        │  SESSION CREATED IN DATABASE    │
        │  (SQLite with UUID & Timestamp) │
        └────────────────┬────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌─────────────────────────────┐  ┌────────────────────────────────┐
│   AUDIO PROCESSING PHASE    │  │   VIDEO PROCESSING PHASE       │
│  (Speech-to-Text Module)    │  │  (Computer Vision Module)      │
└──────────────┬──────────────┘  └────────────┬───────────────────┘
               │                             │
               │  ┌─────────────────────────┬┴─────────────────┐
               │  │                         │                 │
               ▼  ▼                         ▼                 ▼
      ┌──────────────────┐      ┌──────────────────┐  ┌───────────────┐
      │  Whisper STT     │      │  Face Detection  │  │  Eye Tracking │
      │  (Placeholder)   │      │   (MediaPipe)    │  │   (OpenCV)    │
      └────────┬─────────┘      └────────┬─────────┘  └───────┬───────┘
               │                         │                    │
               ▼                         ▼                    ▼
      ┌──────────────────┐      ┌──────────────────┐  ┌───────────────┐
      │   Transcript     │      │  Face Presence   │  │ Eye Contact   │
      │    Creation      │      │    Percentage    │  │   Duration    │
      └────────┬─────────┘      └────────┬─────────┘  └───────┬───────┘
               │                         │                    │
               └─────────────────────────┼────────────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │                                 │
                        ▼                                 ▼
        ┌──────────────────────────────┐  ┌─────────────────────────────┐
        │    NLP PROCESSING ENGINE     │  │  ENGAGEMENT ANALYSIS ENGINE │
        │   (Text Analysis Pipeline)   │  │   (Engagement Scoring)      │
        └──────────────┬───────────────┘  └────────────────┬────────────┘
                       │                                    │
        ┌──────────────┴──────────────────────────────────┬┘
        │                                                 │
        ▼                                                 ▼
┌───────────────────────┐                    ┌──────────────────────────┐
│  Text Cleaning        │                    │  Calculate Engagement    │
│  Sentence Segmentation│                    │  Score (40% Presence +   │
│  Keyword Extraction   │                    │   30% Eye Contact +      │
│  Entity Recognition   │                    │   20% Participation +    │
│  Action Item Detection│                    │   10% Emotion)           │
│  Summarization        │                    │                          │
└───────────┬───────────┘                    └───────────┬──────────────┘
            │                                            │
            ▼                                            ▼
┌─────────────────────────────────┐         ┌────────────────────────────┐
│  Generated Artifacts:            │         │  Engagement Metrics:       │
│  ✓ Summary                       │         │  ✓ Attention Score        │
│  ✓ Key Points                    │         │  ✓ Focus Percentage       │
│  ✓ Action Items                  │         │  ✓ Presence Duration      │
│  ✓ Keywords                      │         │  ✓ Emotion Detection      │
│  ✓ Named Entities                │         │  ✓ Participation Level    │
└─────────────┬─────────────────────┘         └────────────┬──────────────┘
              │                                            │
              └────────────────────────┬───────────────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │                             │
                        ▼                             ▼
                ┌─────────────────────┐     ┌────────────────────┐
                │  PERSIST IN DATABASE│     │  PERSIST IN DATABASE│
                │  (notes table)      │     │  (engagement_events)│
                └────────────┬────────┘     └────────────┬───────┘
                             │                          │
                             └──────────────┬───────────┘
                                            │
                            ┌───────────────┴───────────────┐
                            │                               │
                            ▼                               ▼
                    ┌──────────────────┐         ┌─────────────────────┐
                    │  GENERATE REPORT │         │   UPDATE SESSION    │
                    │  (PDF Generator) │         │   STATUS TO ANALYZED│
                    └────────┬─────────┘         └─────────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  PDF REPORT CONTAINS:    │
                    │  ✓ Session Information  │
                    │  ✓ Generated Notes      │
                    │  ✓ Summary              │
                    │  ✓ Key Points           │
                    │  ✓ Action Items         │
                    │  ✓ Attendance Report    │
                    │  ✓ Engagement Analytics │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │  DASHBOARD DISPLAY   │
                    │  ✓ Overview Cards    │
                    │  ✓ Charts & Graphs   │
                    │  ✓ Session Details   │
                    │  ✓ Engagement Trends │
                    │  ✓ Attendance Stats  │
                    └──────────────────────┘
```

---

## System Architecture Layers

### 1. **Presentation Layer (Frontend)**
- **Technology**: React.js, TypeScript, Vite
- **Responsibilities**:
  - User authentication (login/registration)
  - Session management interface
  - Real-time audio/video recording
  - Dashboard and analytics visualization
  - PDF report download functionality
  - Responsive UI with Tailwind CSS

### 2. **API Layer (Backend Routes)**
- **Technology**: Flask REST API
- **Base URL**: `/api`
- **Endpoints**:
  - `/health` - Service health check
  - `/sessions` - Session CRUD operations
  - `/sessions/<id>/notes` - Note generation and retrieval
  - `/sessions/<id>/engagement` - Engagement event tracking
  - `/audio/transcribe` - Audio processing
  - `/pipeline/analyze` - End-to-end analysis
  - `/analytics/overview` - Dashboard statistics

### 3. **Service Layer (Business Logic)**

#### Speech-to-Text Module
```python
- transcribe_payload(payload) → Dictionary with transcript
- transcribe_text(text) → Direct text transcription
- Handles: .mp3, .wav file formats
- Integration: OpenAI Whisper API (placeholder in current implementation)
```

#### NLP Engine Module
```python
- summarize_transcript(transcript) → Structured analysis
- analyze_transcript(transcript) → Full analysis with classification
- Extracts: Keywords, Key Points, Action Items, Named Entities
```

#### Engagement Tracker Module
```python
- analyze_engagement(payload, transcript) → Engagement score
- Face detection verification
- Eye contact calculation
- Emotion sentiment analysis
- Composite scoring algorithm
```

### 4. **Data Access Layer (Database)**
- **Technology**: SQLite (development), expandable to PostgreSQL/MySQL
- **Tables**:
  - `sessions` - Meeting/class session records
  - `notes` - Generated notes with artifacts
  - `engagement_events` - Participant engagement tracking
  - `users` - User authentication (planned)

### 5. **Utilities & Helpers**
- **Constants**: Configuration values and mappings
- **Validators**: Input validation and sanitization
- **Decorators**: Authentication, logging, error handling
- **Logger**: Centralized logging system
- **File Handler**: Audio/document file management

---

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    context TEXT,
    status TEXT DEFAULT 'active',
    participants_json TEXT,
    transcript TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

**Statuses**: `active`, `analyzing`, `analyzed`, `completed`, `archived`

### Notes Table
```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    transcript TEXT,
    summary TEXT,
    key_points_json TEXT,
    action_items_json TEXT,
    keywords_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
)
```

### Engagement Events Table
```sql
CREATE TABLE engagement_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    event_type TEXT,
    score REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
)
```

**Event Types**: `attended`, `face_detected`, `eye_contact`, `speaking`, `distracted`

---

## API Endpoint Specifications

### Session Management

#### Create Session
```
POST /api/sessions
Content-Type: application/json

{
  "title": "Q4 Planning Meeting",
  "context": "Team planning and roadmap discussion",
  "participants": ["John", "Rahul", "Sarah"]
}

Response: 201 Created
{
  "session": {
    "id": "uuid-string",
    "title": "Q4 Planning Meeting",
    "status": "active",
    "created_at": "2026-06-02T10:00:00Z",
    "note_count": 0,
    "engagement_count": 0
  }
}
```

#### List Sessions
```
GET /api/sessions

Response: 200 OK
{
  "sessions": [
    {
      "id": "uuid-string",
      "title": "Q4 Planning Meeting",
      "status": "active",
      "participants": ["John", "Rahul", "Sarah"],
      "created_at": "2026-06-02T10:00:00Z",
      "updated_at": "2026-06-02T10:30:00Z",
      "note_count": 2,
      "engagement_count": 5,
      "transcript_excerpt": "First 240 characters of transcript..."
    }
  ]
}
```

#### Get Session Details
```
GET /api/sessions/{session_id}

Response: 200 OK
{
  "session": {
    "id": "uuid-string",
    "title": "Q4 Planning Meeting",
    "context": "Team planning and roadmap discussion",
    "status": "analyzed",
    "participants": ["John", "Rahul", "Sarah"],
    "created_at": "2026-06-02T10:00:00Z",
    "updated_at": "2026-06-02T10:30:00Z",
    "transcript": "Full transcript content...",
    "note_count": 2,
    "engagement_count": 5
  }
}
```

### Note Generation

#### Create Note
```
POST /api/sessions/{session_id}/notes
Content-Type: application/json

{
  "title": "Meeting Summary",
  "transcript": "Today we discussed Q4 objectives..."
}

Response: 201 Created
{
  "note": {
    "id": "uuid-string",
    "session_id": "session-uuid",
    "title": "Meeting Summary",
    "summary": "Discussed Q4 objectives and team responsibilities...",
    "key_points": [
      "Complete Q4 roadmap by June 15",
      "Allocate resources for priority features",
      "Schedule weekly sync meetings"
    ],
    "action_items": [
      "John → Finalize Q4 roadmap",
      "Rahul → Update database schema",
      "Sarah → Prepare resource allocation"
    ],
    "keywords": ["Q4", "roadmap", "resources", "schedule"],
    "created_at": "2026-06-02T10:15:00Z"
  }
}
```

#### List Notes for Session
```
GET /api/sessions/{session_id}/notes

Response: 200 OK
{
  "notes": [
    {
      "id": "uuid-string",
      "session_id": "session-uuid",
      "title": "Meeting Summary",
      "summary": "Summary content...",
      "key_points": [...],
      "action_items": [...],
      "keywords": [...],
      "created_at": "2026-06-02T10:15:00Z"
    }
  ]
}
```

### Engagement Tracking

#### Track Engagement Event
```
POST /api/engagement/track
Content-Type: application/json

{
  "session_id": "session-uuid",
  "participant_name": "John",
  "face_detected": true,
  "eye_contact": 0.85,
  "emotion": "focused",
  "speaking_ratio": 0.60,
  "attention_score": 0.78
}

Response: 201 Created
{
  "event": {
    "id": "event-uuid",
    "session_id": "session-uuid",
    "participant_name": "John",
    "event_type": "attended",
    "score": 0.78,
    "created_at": "2026-06-02T10:20:00Z"
  },
  "analysis": {
    "face_detected": true,
    "face_eye_score": 0.85,
    "emotion": "focused",
    "emotion_score": 0.85,
    "attention_score": 0.78,
    "classification": "high",
    "signals": {
      "eye_contact": 0.85,
      "speaking_ratio": 0.60
    }
  }
}
```

### Integrated Pipeline

#### Analyze Complete Pipeline
```
POST /api/pipeline/analyze
Content-Type: application/json

{
  "session_id": "session-uuid",
  "transcript": "Full meeting transcript content...",
  "face_detected": true,
  "eye_contact": 0.80,
  "emotion": "neutral",
  "persist": true,
  "title": "Custom Note Title"
}

Response: 200 OK
{
  "transcription": {
    "source": "text",
    "transcript": "Full transcript...",
    "confidence": 1.0
  },
  "analysis": {
    "summary": "Meeting focused on...",
    "key_points": [...],
    "action_items": [...],
    "keywords": [...]
  },
  "engagement": {
    "attention_score": 0.78,
    "classification": "high",
    ...
  },
  "note": {...},
  "event": {...}
}
```

### Analytics

#### Get Overview
```
GET /api/analytics/overview

Response: 200 OK
{
  "overview": {
    "session_count": 15,
    "note_count": 42,
    "engagement_event_count": 285,
    "average_engagement_score": 0.72,
    "top_participants": [
      {
        "participant_name": "John",
        "events": 45,
        "average_score": 0.85
      },
      {
        "participant_name": "Rahul",
        "events": 38,
        "average_score": 0.78
      }
    ]
  }
}
```

---

## Engagement Score Calculation Formula

```
Engagement Score = 
  40% × Presence Score +
  30% × Eye Contact Score +
  20% × Emotion Score +
  10% × Attention Score

Where:
- Presence Score: 1.0 if face detected, 0.2 otherwise
- Eye Contact Score: Normalized eye gaze duration (0.0-1.0)
- Emotion Score: Mapped from emotion state
  - Positive/Happy: 0.90
  - Focused: 0.85
  - Neutral: 0.70
  - Bored: 0.25
  - Frustrated: 0.30
  - Distracted: 0.20
- Attention Score: Composite of speaking ratio and attentiveness
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, TypeScript, Vite | User Interface |
| **Backend** | Flask 3.0, Python 3.9+ | REST API Server |
| **Database** | SQLite (dev), PostgreSQL (prod) | Data Persistence |
| **AI/NLP** | Transformers, spaCy, NLTK | Text Analysis |
| **Speech-to-Text** | OpenAI Whisper | Audio Transcription |
| **Computer Vision** | OpenCV, MediaPipe | Face Detection & Tracking |
| **PDF Generation** | ReportLab | Report Export |
| **Deployment** | Docker, Gunicorn, Nginx | Production Hosting |

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Container                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Nginx (Reverse Proxy)                     │ │
│  └────────────────┬─────────────────────────────────┘ │
│                   │                                    │
│  ┌────────────────▼──────────────────────────────────┐ │
│  │      Gunicorn (WSGI Application Server)           │ │
│  │      Flask App Instance (Multiple Workers)        │ │
│  └────────────────┬──────────────────────────────────┘ │
│                   │                                    │
│  ┌────────────────▼──────────────────────────────────┐ │
│  │  SQLite/PostgreSQL Database                       │ │
│  │  Redis Cache (Optional)                           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Security Considerations

1. **Authentication**: JWT tokens for API security
2. **CORS**: Configured for production domains
3. **Input Validation**: All user inputs sanitized
4. **Database Security**: SQL parameterized queries
5. **File Upload**: Validate file types and sizes
6. **Environment Variables**: Sensitive config stored securely
7. **Rate Limiting**: API endpoint throttling (planned)
8. **HTTPS**: Enforced in production

---

## Performance Optimization

1. **Async Processing**: Background tasks for heavy NLP operations
2. **Caching**: Redis cache for frequently accessed data
3. **Database Indexing**: Optimized queries with proper indexes
4. **Pagination**: Large result sets paginated
5. **Compression**: Gzip compression for API responses
6. **CDN**: Static assets served via CDN
7. **Lazy Loading**: Frontend components loaded on demand

---

## Monitoring & Logging

1. **Application Logs**: Centralized logging with timestamps
2. **Error Tracking**: Sentry integration for exception monitoring
3. **Performance Metrics**: APM for API response times
4. **Database Monitoring**: Query performance analysis
5. **Health Checks**: `/api/health` endpoint for uptime monitoring

---

## Future Enhancements

1. **Real Whisper Integration**: Replace placeholder with actual OpenAI Whisper API
2. **MediaPipe/OpenCV Implementation**: Real-time face and eye tracking
3. **Advanced NLP**: Fine-tuned models for specific domains
4. **Emotion Detection**: Deep learning-based emotion analysis
5. **Multi-language Support**: Transcription and analysis in multiple languages
6. **Collaborative Features**: Real-time note sharing and editing
7. **Mobile Apps**: iOS and Android native applications
8. **WebRTC Integration**: Live streaming and recording from browser

---

## Development Roadmap

**Phase 1 (Complete)**: Basic architecture, database, API endpoints
**Phase 2 (In Progress)**: Frontend dashboard, basic NLP
**Phase 3 (Planned)**: Whisper integration, ML models
**Phase 4 (Planned)**: Computer vision features
**Phase 5 (Planned)**: Mobile apps and advanced features

---

## Documentation Structure

- `docs/SETUP_GUIDE.md` - Local development setup
- `docs/API_DOCUMENTATION.md` - Detailed API reference
- `docs/DEPLOYMENT_GUIDE.md` - Production deployment
- `docs/SYSTEM_ARCHITECTURE.md` - This file
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/CONTRIBUTING.md` - Development guidelines

---

**Last Updated**: 2026-06-02
**Version**: 1.0.0
