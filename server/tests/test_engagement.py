from __future__ import annotations

from modules.engagement_tracker import analyze_engagement


def test_engagement_score_uses_documented_signals():
	result = analyze_engagement(
		{
			'face_detected': True,
			'eye_contact': 80,
			'speaking_ratio': 0.5,
			'emotion': 'focused',
		},
		transcript='Ava: I can take the next action item.',
	)

	assert result['face_detected'] is True
	assert result['attention_score'] > 0.7
	assert result['signals']['eye_contact'] == 0.8
	assert result['classification'] in {'medium', 'high', 'excellent'}


def test_engagement_score_handles_absent_face():
	result = analyze_engagement(
		{
			'face_detected': False,
			'eye_contact': 0.1,
			'speaking_ratio': 0.0,
			'emotion': 'distracted',
		}
	)

	assert result['face_detected'] is False
	assert result['attention_score'] < 0.5
	assert result['classification'] == 'low'
