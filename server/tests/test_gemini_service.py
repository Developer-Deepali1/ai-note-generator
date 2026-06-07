from __future__ import annotations

from modules import gemini_service
from modules.gemini_service import GeminiConfig, GeminiServiceError, generate_meeting_notes


def _config() -> GeminiConfig:
	return GeminiConfig(
		api_key='test-key',
		model_name='gemini-test',
		timeout_seconds=0.1,
		max_retries=0,
		retry_initial_delay_seconds=0.0,
		retry_max_delay_seconds=0.0,
		temperature=0.2,
		max_output_tokens=512,
	)


def test_generate_meeting_notes_valid_transcript(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(
		gemini_service,
		'_generate_with_timeout',
		lambda config, transcript: {
			'summary': 'Gemini summary of the meeting.',
			'key_points': ['Roadmap reviewed', 'Release date confirmed'],
			'action_items': ['Send recap email'],
			'decisions': ['Proceed with launch'],
			'risks': ['Timeline risk if approvals slip'],
			'follow_ups': ['Prepare launch checklist'],
		},
	)

	result = generate_meeting_notes('We reviewed the roadmap and confirmed the release date.')

	assert result['summary'] == 'Gemini summary of the meeting.'
	assert result['key_points'] == ['Roadmap reviewed', 'Release date confirmed']
	assert result['action_items'] == ['Send recap email']
	assert result['decisions'] == ['Proceed with launch']
	assert result['risks'] == ['Timeline risk if approvals slip']
	assert result['follow_ups'] == ['Prepare launch checklist']


def test_generate_meeting_notes_empty_transcript():
	result = generate_meeting_notes('   ')

	assert result == {
		'summary': '',
		'key_points': [],
		'action_items': [],
		'decisions': [],
		'risks': [],
		'follow_ups': [],
	}


def test_generate_meeting_notes_handles_long_transcript(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(
		gemini_service,
		'_generate_with_timeout',
		lambda config, transcript: {
			'summary': 'Long transcript summarized.',
			'key_points': [f'Point {index}' for index in range(1, 6)],
			'action_items': [f'Action {index}' for index in range(1, 4)],
			'decisions': ['Decision 1'],
			'risks': ['Risk 1'],
			'follow_ups': ['Follow up 1'],
		},
	)

	transcript = ' '.join(f'Topic {index} discussed.' for index in range(500))
	result = generate_meeting_notes(transcript)

	assert result['summary'] == 'Long transcript summarized.'
	assert len(result['key_points']) == 5
	assert len(result['action_items']) == 3


def test_generate_meeting_notes_api_failure_falls_back_to_empty(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(
		gemini_service,
		'_generate_with_timeout',
		lambda config, transcript: (_ for _ in ()).throw(GeminiServiceError('upstream failure')),
	)

	result = generate_meeting_notes('We discussed the roadmap.')

	assert result == {
		'summary': '',
		'key_points': [],
		'action_items': [],
		'decisions': [],
		'risks': [],
		'follow_ups': [],
	}


def test_generate_meeting_notes_timeout(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(
		gemini_service,
		'_generate_with_timeout',
		lambda config, transcript: (_ for _ in ()).throw(GeminiServiceError('timed out')),
	)

	result = generate_meeting_notes('We discussed the roadmap.')

	assert result['summary'] == ''
	assert result['key_points'] == []


def test_generate_meeting_notes_invalid_response(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(gemini_service, '_generate_with_timeout', lambda config, transcript: 'not json')

	result = generate_meeting_notes('We discussed the roadmap.')

	assert result == {
		'summary': '',
		'key_points': [],
		'action_items': [],
		'decisions': [],
		'risks': [],
		'follow_ups': [],
	}


def test_generate_meeting_notes_invalid_schema(monkeypatch):
	monkeypatch.setattr(gemini_service.GeminiConfig, 'from_env', classmethod(lambda cls: _config()))
	monkeypatch.setattr(gemini_service, '_generate_with_timeout', lambda config, transcript: ['invalid'])

	result = generate_meeting_notes('We discussed the roadmap.')

	assert result == {
		'summary': '',
		'key_points': [],
		'action_items': [],
		'decisions': [],
		'risks': [],
		'follow_ups': [],
	}