"""Analytics engine for engagement and participation statistics."""

from __future__ import annotations

import csv
import io
import json
from statistics import mean
from typing import Any



def calculate_attendance_percentage(attended: int, total: int) -> float:
    """Calculate attendance percentage with guard rails."""
    if total <= 0:
        return 0.0
    return round(max(0.0, min(100.0, (attended / total) * 100)), 2)



def calculate_participation_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate participation counts and speaker distribution."""
    if not events:
        return {'total_events': 0, 'speaking_events': 0, 'participation_ratio': 0.0}

    speaking = sum(1 for event in events if str(event.get('event_type', '')).lower() in {'spoke', 'question', 'response'})
    return {
        'total_events': len(events),
        'speaking_events': speaking,
        'participation_ratio': round(speaking / len(events), 3),
    }



def generate_engagement_trends(scores: list[float]) -> dict[str, Any]:
    """Generate basic trend data for charting."""
    if not scores:
        return {'trend': 'stable', 'average': 0.0, 'change': 0.0, 'series': []}

    start = scores[0]
    end = scores[-1]
    change = round(end - start, 2)
    if change > 2:
        trend = 'up'
    elif change < -2:
        trend = 'down'
    else:
        trend = 'stable'
    return {
        'trend': trend,
        'average': round(mean(scores), 2),
        'change': change,
        'series': [round(value, 2) for value in scores],
    }



def calculate_analytics_summary(
    *,
    attendance_total: int,
    attendance_present: int,
    engagement_scores: list[float],
    participation_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute session-level analytics summary."""
    attendance = calculate_attendance_percentage(attendance_present, attendance_total)
    trends = generate_engagement_trends(engagement_scores)
    participation = calculate_participation_metrics(participation_events)
    return {
        'attendance_percentage': attendance,
        'engagement_average': trends['average'],
        'engagement_trend': trends['trend'],
        'engagement_change': trends['change'],
        'participation_ratio': participation['participation_ratio'],
        'event_count': participation['total_events'],
    }



def compare_participant_performance(participants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort participant performance for comparisons."""
    ranked = sorted(
        (
            {
                'participant': item.get('participant', item.get('participant_name', 'Participant')),
                'engagement_score': float(item.get('engagement_score', 0.0)),
                'attendance_percentage': float(item.get('attendance_percentage', 0.0)),
            }
            for item in participants
        ),
        key=lambda item: (item['engagement_score'], item['attendance_percentage']),
        reverse=True,
    )
    return ranked



def export_analytics_data(payload: dict[str, Any], *, export_format: str = 'json') -> str:
    """Export analytics payload as JSON or CSV."""
    if export_format == 'json':
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['metric', 'value'])
        for key, value in payload.items():
            writer.writerow([key, value])
        return output.getvalue()

    raise ValueError('Unsupported export format. Use json or csv.')
