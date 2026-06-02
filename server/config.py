from __future__ import annotations

import os
from pathlib import Path


class Config:
	BASE_DIR = Path(__file__).resolve().parent
	DATABASE_PATH = os.getenv(
		'AI_NOTE_DATABASE_PATH', str(BASE_DIR / 'data' / 'ai_note_generator.db')
	)
	SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
	JWT_SECRET_KEY = os.getenv(
		'JWT_SECRET_KEY',
		'dev-jwt-secret-key-change-me-32-bytes-minimum',
	)
	JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
	JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '60'))
	MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
	MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'ai_note_generator')
	MONGO_USERS_COLLECTION = os.getenv('MONGO_USERS_COLLECTION', 'users')
	JSON_SORT_KEYS = False
	MAX_CONTENT_LENGTH = 25 * 1024 * 1024
	API_TITLE = 'AI-Powered Smart Note Generator & Engagement Tracker'


class DevelopmentConfig(Config):
	DEBUG = True


class TestingConfig(Config):
	TESTING = True

