from __future__ import annotations

from database.models import create_engagement_event, create_note, create_session, ensure_database
from models.engagement import EngagementEvent
from models.note import Note
from models.session import Session
from modules.nlp_engine import summarize_transcript


def test_session_model_validates_and_serializes_payload():
	session = Session.from_payload(
		{
			'title': ' Weekly Sync ',
			'context': ' Team planning ',
			'participants': ['Ava', ' ava ', 'Noah'],
		}
	)

	assert session.title == 'Weekly Sync'
	assert session.participants == ['Ava', 'Noah']
	assert session.to_dict()['status'] == 'active'


def test_note_model_builds_from_nlp_artifacts():
	transcript = 'Ava: Action item: send the roadmap draft by Friday.'
	artifacts = summarize_transcript(transcript)
	note = Note.from_artifacts('session-1', {'transcript': transcript}, artifacts)

	assert note.session_id == 'session-1'
	assert note.summary
	assert any('Friday' in item for item in note.action_items)
	assert note.to_dict()['keywords']


def test_engagement_event_model_normalizes_scores_and_metadata():
	event = EngagementEvent.from_payload(
		'session-1',
		{
			'participant_name': ' Ava ',
			'event_type': 'focus',
			'score': 82,
			'emotion': 'focused',
			'eye_contact': 0.8,
		},
	)

	assert event.participant_name == 'Ava'
	assert event.score == 0.82
	assert event.metadata['eye_contact'] == 0.8


def test_database_helpers_persist_through_domain_models(tmp_path):
	database_path = str(tmp_path / 'models.db')
	ensure_database(database_path)
	session = create_session(
		database_path,
		{'title': 'Model persistence', 'participants': ['Ava']},
	)
	note = create_note(
		database_path,
		session['id'],
		{'transcript': 'We should send the update by Friday.'},
	)
	event = create_engagement_event(
		database_path,
		session['id'],
		{'participant_name': 'Ava', 'event_type': 'focus', 'score': 0.75},
	)

	assert session['title'] == 'Model persistence'
	assert note['summary']
	assert event['score'] == 0.75
