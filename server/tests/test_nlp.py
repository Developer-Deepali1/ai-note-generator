from __future__ import annotations

from modules.nlp_engine import analyze_transcript, summarize_transcript


def test_summarize_transcript_extracts_core_artifacts():
	transcript = """
	Ava: We reviewed the Q4 roadmap and the checkout milestone.
	Noah: Action item: Ava should send the draft by Friday.
	Mia: Next step: schedule the client demo next week.
	"""

	artifacts = summarize_transcript(transcript)

	assert artifacts['summary']
	assert 'roadmap' in artifacts['keywords']
	assert any('draft by Friday' in item for item in artifacts['action_items'])
	assert artifacts['metadata']['speaker_count'] == 3
	assert artifacts['entities']


def test_analyze_transcript_classifies_planning_content():
	result = analyze_transcript(
		'We discussed roadmap priorities, resources, milestones, and the deadline.'
	)

	assert result['classification']['category'] == 'planning'
	assert result['analysis']['key_points']
