PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
	id TEXT PRIMARY KEY,
	title TEXT NOT NULL,
	context TEXT DEFAULT '',
	status TEXT NOT NULL DEFAULT 'active',
	participants_json TEXT NOT NULL DEFAULT '[]',
	transcript TEXT DEFAULT '',
	created_at TEXT NOT NULL,
	updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
	id TEXT PRIMARY KEY,
	session_id TEXT NOT NULL,
	title TEXT NOT NULL,
	transcript TEXT DEFAULT '',
	summary TEXT NOT NULL,
	key_points_json TEXT NOT NULL DEFAULT '[]',
	action_items_json TEXT NOT NULL DEFAULT '[]',
	keywords_json TEXT NOT NULL DEFAULT '[]',
	created_at TEXT NOT NULL,
	FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS engagement_events (
	id TEXT PRIMARY KEY,
	session_id TEXT NOT NULL,
	participant_name TEXT NOT NULL,
	event_type TEXT NOT NULL,
	score REAL NOT NULL DEFAULT 0,
	created_at TEXT NOT NULL,
	FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notes_session_id ON notes (session_id);
CREATE INDEX IF NOT EXISTS idx_engagement_events_session_id ON engagement_events (session_id);
CREATE INDEX IF NOT EXISTS idx_engagement_events_participant_name ON engagement_events (participant_name);
