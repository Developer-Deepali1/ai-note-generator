from __future__ import annotations

from modules.nlp_engine import analyze_transcript, summarize_transcript



def test_nlp_summary_keywords_and_actions():
    transcript = 'Alice will send the report tomorrow. We reviewed milestones and launch risks.'
    summary = summarize_transcript(transcript)
    assert summary['summary']
    assert any('send the report' in item.lower() for item in summary['action_items'])
    assert summary['keywords']



def test_nlp_analysis_exposes_cleaned_transcript():
    result = analyze_transcript('  Hello\n\nworld.  ')
    assert result['cleaned_transcript'] == 'Hello world.'
