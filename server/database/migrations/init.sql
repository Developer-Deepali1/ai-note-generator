PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA cache_size = -64000;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    preferred_language TEXT NOT NULL DEFAULT 'en',
    last_login_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    participants_json TEXT NOT NULL DEFAULT '[]',
    transcript TEXT NOT NULL DEFAULT '',
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    -- Keep these values synchronized with SessionStatus in server/utils/constants.py.
    CHECK (status IN ('created', 'active', 'analyzed', 'completed', 'archived', 'failed'))
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    transcript TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL,
    key_points_json TEXT NOT NULL DEFAULT '[]',
    action_items_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    confidence_score REAL,
    language_code TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS engagement_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    participant_id TEXT,
    event_type TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    emotion_label TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS participants (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT,
    display_name TEXT NOT NULL,
    email TEXT,
    joined_at TEXT,
    left_at TEXT,
    total_presence_seconds INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    UNIQUE (session_id, display_name)
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    attendance_percentage REAL NOT NULL DEFAULT 0,
    focus_percentage REAL NOT NULL DEFAULT 0,
    presence_percentage REAL NOT NULL DEFAULT 0,
    eye_contact_percentage REAL NOT NULL DEFAULT 0,
    engagement_score REAL NOT NULL DEFAULT 0,
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants (id) ON DELETE CASCADE,
    CHECK (attendance_percentage BETWEEN 0 AND 100),
    CHECK (focus_percentage BETWEEN 0 AND 100),
    CHECK (presence_percentage BETWEEN 0 AND 100),
    CHECK (eye_contact_percentage BETWEEN 0 AND 100),
    CHECK (engagement_score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS audio_files (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    uploaded_by TEXT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    duration_seconds REAL,
    sample_rate INTEGER,
    mime_type TEXT,
    processing_status TEXT NOT NULL DEFAULT 'queued',
    transcript_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE SET NULL,
    -- Keep these values synchronized with AudioProcessingStatus/TranscriptStatus in server/utils/constants.py.
    CHECK (processing_status IN ('queued', 'processing', 'completed', 'failed')),
    CHECK (transcript_status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    generated_by TEXT,
    report_type TEXT NOT NULL DEFAULT 'pdf',
    storage_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    generated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (generated_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS analytics_summary (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    avg_engagement_score REAL NOT NULL DEFAULT 0,
    attendance_rate REAL NOT NULL DEFAULT 0,
    total_events INTEGER NOT NULL DEFAULT 0,
    key_topics_json TEXT NOT NULL DEFAULT '[]',
    sentiment_breakdown_json TEXT NOT NULL DEFAULT '{}',
    generated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    UNIQUE (session_id)
);

CREATE TABLE IF NOT EXISTS action_items (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    note_id TEXT,
    owner_name TEXT,
    owner_user_id TEXT,
    description TEXT NOT NULL,
    due_date TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'open',
    source_sentence TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE SET NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users (id) ON DELETE SET NULL,
    -- Keep these values synchronized with ActionItemPriority/ActionItemStatus in server/utils/constants.py.
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS keywords_index (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    note_id TEXT,
    keyword TEXT NOT NULL,
    normalized_keyword TEXT NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    relevance_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS entity_recognition (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    note_id TEXT,
    entity_text TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    confidence_score REAL,
    source_sentence TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS api_logs (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    request_id TEXT,
    method TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    latency_ms REAL,
    ip_address TEXT,
    user_agent TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_by TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (updated_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notes_session_id ON notes (session_id);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_engagement_events_session_id ON engagement_events (session_id);
CREATE INDEX IF NOT EXISTS idx_engagement_events_participant_name ON engagement_events (participant_name);
CREATE INDEX IF NOT EXISTS idx_engagement_events_created_at ON engagement_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_participants_session_id ON participants (session_id);
CREATE INDEX IF NOT EXISTS idx_participants_user_id ON participants (user_id);

CREATE INDEX IF NOT EXISTS idx_attendance_records_session_id ON attendance_records (session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_participant_id ON attendance_records (participant_id);

CREATE INDEX IF NOT EXISTS idx_audio_files_session_id ON audio_files (session_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_status ON audio_files (processing_status, transcript_status);

CREATE INDEX IF NOT EXISTS idx_reports_session_id ON reports (session_id);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports (generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_summary_session_id ON analytics_summary (session_id);

CREATE INDEX IF NOT EXISTS idx_action_items_session_id ON action_items (session_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items (status);
CREATE INDEX IF NOT EXISTS idx_action_items_due_date ON action_items (due_date);

CREATE INDEX IF NOT EXISTS idx_keywords_index_session_id ON keywords_index (session_id);
CREATE INDEX IF NOT EXISTS idx_keywords_index_normalized ON keywords_index (normalized_keyword);

CREATE INDEX IF NOT EXISTS idx_entity_recognition_session_id ON entity_recognition (session_id);
CREATE INDEX IF NOT EXISTS idx_entity_recognition_type ON entity_recognition (entity_type);

CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint_status ON api_logs (endpoint, status_code);

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE users SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_sessions_updated_at
AFTER UPDATE ON sessions
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE sessions SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_notes_updated_at
AFTER UPDATE ON notes
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE notes SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_engagement_events_updated_at
AFTER UPDATE ON engagement_events
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE engagement_events SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_participants_updated_at
AFTER UPDATE ON participants
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE participants SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_attendance_records_updated_at
AFTER UPDATE ON attendance_records
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE attendance_records SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_audio_files_updated_at
AFTER UPDATE ON audio_files
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE audio_files SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_reports_updated_at
AFTER UPDATE ON reports
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE reports SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_analytics_summary_updated_at
AFTER UPDATE ON analytics_summary
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE analytics_summary SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_action_items_updated_at
AFTER UPDATE ON action_items
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE action_items SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_keywords_index_updated_at
AFTER UPDATE ON keywords_index
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE keywords_index SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_entity_recognition_updated_at
AFTER UPDATE ON entity_recognition
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE entity_recognition SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_system_metadata_updated_at
AFTER UPDATE ON system_metadata
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE system_metadata SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE key = OLD.key;
END;

CREATE VIEW IF NOT EXISTS vw_session_overview AS
SELECT
    s.id AS session_id,
    s.title,
    s.status,
    s.created_at,
    s.updated_at,
    COUNT(DISTINCT n.id) AS notes_count,
    COUNT(DISTINCT p.id) AS participants_count,
    COUNT(DISTINCT ee.id) AS engagement_events_count,
    ROUND(AVG(ee.score), 2) AS avg_engagement_score
FROM sessions s
LEFT JOIN notes n ON n.session_id = s.id
LEFT JOIN participants p ON p.session_id = s.id
LEFT JOIN engagement_events ee ON ee.session_id = s.id
GROUP BY s.id;

CREATE VIEW IF NOT EXISTS vw_participant_engagement AS
SELECT
    p.id AS participant_id,
    p.session_id,
    p.display_name,
    COALESCE(ar.attendance_percentage, 0) AS attendance_percentage,
    COALESCE(ar.focus_percentage, 0) AS focus_percentage,
    COALESCE(ar.presence_percentage, 0) AS presence_percentage,
    COALESCE(ar.eye_contact_percentage, 0) AS eye_contact_percentage,
    COALESCE(ar.engagement_score, 0) AS engagement_score,
    COUNT(ee.id) AS engagement_events
FROM participants p
LEFT JOIN attendance_records ar ON ar.participant_id = p.id
LEFT JOIN engagement_events ee ON ee.participant_id = p.id
GROUP BY p.id;

CREATE VIEW IF NOT EXISTS vw_note_artifacts AS
SELECT
    n.id AS note_id,
    n.session_id,
    n.title,
    n.summary,
    n.keywords_json,
    n.action_items_json,
    COUNT(DISTINCT ai.id) AS extracted_action_items,
    COUNT(DISTINCT er.id) AS extracted_entities
FROM notes n
LEFT JOIN action_items ai ON ai.note_id = n.id
LEFT JOIN entity_recognition er ON er.note_id = n.id
GROUP BY n.id;

INSERT OR IGNORE INTO system_metadata (key, value, description)
VALUES
    ('schema_version', '1.0.0', 'Current schema migration version'),
    ('initialized_at', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Initial database bootstrap timestamp');
