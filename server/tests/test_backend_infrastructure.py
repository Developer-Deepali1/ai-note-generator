from __future__ import annotations

import json
import logging
import sqlite3

import pytest

from database.connection import initialize_schema
from utils.constants import ENGAGEMENT_WEIGHTS, SessionStatus
from utils.logger import JSONFormatter
from utils.validators import (
    ValidationError,
    validate_audio_format,
    validate_email,
    validate_participants,
    validate_request_payload,
    validate_session_status,
)


REQUIRED_TABLES = {
    'users',
    'sessions',
    'notes',
    'engagement_events',
    'participants',
    'attendance_records',
    'audio_files',
    'reports',
    'analytics_summary',
    'action_items',
    'keywords_index',
    'entity_recognition',
    'api_logs',
    'system_metadata',
}


def test_schema_initialization_includes_required_objects(tmp_path):
    database_path = tmp_path / 'schema.db'
    initialize_schema(database_path)

    connection = sqlite3.connect(database_path)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    views = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view'"
        ).fetchall()
    }
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
    }
    connection.close()

    assert REQUIRED_TABLES.issubset(tables)
    assert {'vw_session_overview', 'vw_participant_engagement', 'vw_note_artifacts'} <= views
    assert 'trg_sessions_updated_at' in triggers


def test_constants_engagement_weights_total_100_percent():
    assert round(sum(ENGAGEMENT_WEIGHTS.values()), 2) == 1.0
    assert SessionStatus.ACTIVE.value == 'active'


def test_validators_handle_success_and_error_cases():
    assert validate_email('Team.Lead@example.com') == 'team.lead@example.com'
    assert validate_audio_format('session.wav') == '.wav'
    assert validate_participants(['Ava', ' ava ', 'Noah']) == ['Ava', 'Noah']
    assert validate_session_status('ACTIVE') == 'active'

    sanitized_payload = validate_request_payload(
        {'title': '<Weekly Sync>', 'participants': ['Ava']},
        required_fields=['title'],
        optional_fields=['participants'],
    )
    assert sanitized_payload['title'] == '&lt;Weekly Sync&gt;'

    with pytest.raises(ValidationError):
        validate_email('invalid-email')

    with pytest.raises(ValidationError):
        validate_session_status('unknown')


def test_json_formatter_generates_structured_json():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name='test.logger',
        level=logging.INFO,
        pathname=__file__,
        lineno=88,
        msg='Pipeline completed',
        args=(),
        exc_info=None,
    )
    record.request_id = 'req-123'
    record.session_id = 'sess-789'

    serialized = formatter.format(record)
    payload = json.loads(serialized)

    assert payload['message'] == 'Pipeline completed'
    assert payload['level'] == 'INFO'
    assert payload['request_id'] == 'req-123'
    assert payload['session_id'] == 'sess-789'
