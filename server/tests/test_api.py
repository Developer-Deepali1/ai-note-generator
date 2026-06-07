from __future__ import annotations

import routes.pipeline as pipeline_route


def test_health_endpoint(client):
	response = client.get('/api/health')

	assert response.status_code == 200
	assert response.get_json()['status'] == 'ok'


def test_session_note_and_overview_flow(client):
	create_response = client.post(
		'/api/sessions',
		json={
			'title': 'Weekly planning',
			'context': 'Team meeting',
			'participants': ['Ava', 'Noah'],
		},
	)
	session = create_response.get_json()['session']

	note_response = client.post(
		f"/api/sessions/{session['id']}/notes",
		json={
			'title': 'Planning summary',
			'transcript': 'We reviewed milestones. Action item: send the draft by Friday.',
		},
	)
	note = note_response.get_json()['note']

	engagement_response = client.post(
		'/api/engagement/track',
		json={
			'session_id': session['id'],
			'participant_name': 'Ava',
			'event_type': 'spoke',
			'score': 0.8,
		},
	)

	overview_response = client.get('/api/analytics/overview')

	assert create_response.status_code == 201
	assert note_response.status_code == 201
	assert note['summary']
	assert 'draft by Friday' in ' '.join(note['action_items'])
	assert engagement_response.status_code == 201
	assert overview_response.status_code == 200
	assert overview_response.get_json()['overview']['session_count'] == 1


def test_pipeline_endpoint_can_analyze_and_persist(client):
	create_response = client.post(
		'/api/sessions',
		json={
			'title': 'Product review',
			'context': 'Roadmap discussion',
			'participants': ['Mia', 'Leo'],
		},
	)
	session = create_response.get_json()['session']

	pipeline_response = client.post(
		'/api/pipeline/analyze',
		json={
			'session_id': session['id'],
			'persist': True,
			'transcript': 'We should ship the draft on Friday. Action item: finalize the demo.',
			'face_detected': True,
			'eye_contact': 0.8,
			'emotion': 'focused',
		},
	)
	payload = pipeline_response.get_json()

	assert pipeline_response.status_code == 200
	assert payload['analysis']['summary']
	assert payload['engagement']['attention_score'] >= 0.0
	assert 'note' in payload
	assert 'event' in payload


def test_pipeline_endpoint_falls_back_to_nlp_when_gemini_fails(client, monkeypatch):
	monkeypatch.setattr(
		pipeline_route,
		'generate_meeting_notes',
		lambda transcript: (_ for _ in ()).throw(RuntimeError('Gemini unavailable')),
	)

	response = client.post(
		'/api/pipeline/analyze',
		json={
			'transcript': 'We reviewed the roadmap and confirmed the next steps.',
			'face_detected': True,
			'eye_contact': 0.7,
			'emotion': 'focused',
		},
	)
	payload = response.get_json()

	assert response.status_code == 200
	assert {'transcription', 'transcript', 'analysis', 'engagement'} <= payload.keys()
	assert payload['analysis']['summary']
	assert payload['analysis']['key_points']

