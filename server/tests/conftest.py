from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path: Path):
	database_path = tmp_path / 'test.db'
	test_app = create_app({'TESTING': True, 'DATABASE_PATH': str(database_path)})
	yield test_app


@pytest.fixture()
def client(app):
	return app.test_client()

