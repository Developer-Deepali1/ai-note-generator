from __future__ import annotations

import os
from pathlib import Path


class Config:
	BASE_DIR = Path(__file__).resolve().parent
	DATABASE_PATH = os.getenv(
		'AI_NOTE_DATABASE_PATH', str(BASE_DIR / 'data' / 'ai_note_generator.db')
	)
	SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
	JSON_SORT_KEYS = False
	MAX_CONTENT_LENGTH = 25 * 1024 * 1024
	API_TITLE = 'AI-Powered Smart Note Generator & Engagement Tracker'


class DevelopmentConfig(Config):
	DEBUG = True


class TestingConfig(Config):
	TESTING = True

