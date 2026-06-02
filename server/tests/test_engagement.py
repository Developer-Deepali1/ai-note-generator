from __future__ import annotations

from modules.engagement_tracker import analyze_engagement, calculate_group_engagement



def test_engagement_analysis_returns_weighted_score():
    result = analyze_engagement(
        {
            'face_detected': True,
            'eye_contact': 0.8,
            'speaking_ratio': 0.6,
            'emotion': 'focused',
            'historical_scores': [70.0, 72.0],
        },
        transcript='We should complete the draft this week.',
    )
    assert 0.0 <= result['attention_score'] <= 1.0
    assert result['engagement_score'] >= 0.0
    assert result['classification'] in {'low', 'medium', 'high', 'excellent'}



def test_group_engagement_aggregates_scores():
    summary = calculate_group_engagement([
        {'engagement_score': 70.0},
        {'engagement_score': 90.0},
    ])
    assert summary['average_score'] == 80.0
    assert summary['participant_count'] == 2
